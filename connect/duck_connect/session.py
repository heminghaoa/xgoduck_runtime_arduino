"""One phone's conversation with the duck, independent of the Bluetooth transport.

Requests are {"op": ..., "id": n, ...}; the reply carries the same id with "ok".
A request without an id gets no reply unless it fails. The duck also sends
events: {"ev": "status"} every few seconds after hello, and {"ev": "net"} when a
Wi-Fi connection attempt ends. Everything but hello, challenge, pair and status
needs a completed pairing on this connection.
"""
import asyncio
from . import PROTOCOL_VERSION, crypto

MAX_PAIR_FAILURES = 5
REMOTE_MODES = ('shadow', 'off', 'hold', 'policy')
ACTIONS = ('pick', 'roulade')
PUBLIC_OPS = {'hello', 'challenge', 'pair', 'status'}


class Session:
    def __init__(self, identity, wifi, app, send):
        self.identity, self.wifi, self.app, self.send = identity, wifi, app, send
        self.greeted = False
        self.chunk = None          # largest chunk the phone said it can take, from hello
        self.duck_nonce = None     # outstanding challenge, single use
        self.paired = False
        self.key = None            # session key for sealed secrets
        self.failures = 0
        self.drove = False
        self.connecting = False
        self.tasks = set()

    async def handle(self, msg):
        op, rid = msg.get('op'), msg.get('id')
        try:
            handler = getattr(self, 'op_' + op, None) if isinstance(op, str) else None
            if handler is None:
                raise ValueError(f'unknown op: {op}')
            if op not in PUBLIC_OPS and not self.paired:
                raise PermissionError('pair first')
            result = await handler(msg)
            if rid is not None:
                await self.send({'id': rid, 'ok': True, **(result or {})})
        except (ValueError, PermissionError, TypeError, OSError) as exc:
            reply = {'ok': False, 'error': str(exc) or type(exc).__name__}
            reply.update({'id': rid} if rid is not None else {'op': op})
            await self.send(reply)

    async def close(self):
        """The phone disconnected: forget the pairing and stop any travel it started."""
        self.paired, self.key, self.duck_nonce = False, None, None
        if self.drove:
            self.drove = False
            try:
                await asyncio.to_thread(self.app.command, twist=[0.0, 0.0, 0.0])
            except (ValueError, OSError):
                pass

    def _require_identity(self):
        if not self.identity.key:
            raise ValueError(self.identity.error or 'duck identity unavailable')

    async def op_hello(self, msg):
        chunk = msg.get('chunk')
        if isinstance(chunk, int) and not isinstance(chunk, bool):
            self.chunk = max(20, min(chunk, 512))
        self.greeted = True
        return dict(proto=PROTOCOL_VERSION, duck_id=self.identity.id, paired=self.paired,
                    identity_error=self.identity.error or None)

    async def op_challenge(self, msg):
        self.identity.reload()
        self._require_identity()
        self.duck_nonce = crypto.nonce()
        return dict(nonce=self.duck_nonce, duck_id=self.identity.id)

    async def op_pair(self, msg):
        self._require_identity()
        if self.failures >= MAX_PAIR_FAILURES:
            raise PermissionError('too many wrong attempts; reconnect to try again')
        nonce, app_nonce, proof = msg.get('nonce'), msg.get('app_nonce'), msg.get('proof')
        expected, self.duck_nonce = self.duck_nonce, None
        if not expected or not crypto.same(nonce, expected):
            raise ValueError('challenge expired; ask for a new one')
        if not isinstance(app_nonce, str) or not 8 <= len(app_nonce) <= 64:
            raise ValueError('app_nonce must be 8 to 64 characters')
        key, duck_id = self.identity.key, self.identity.id
        if not crypto.same(proof, crypto.app_proof(key, duck_id, nonce, app_nonce)):
            self.failures += 1
            raise PermissionError('wrong pairing key')
        self.paired, self.failures = True, 0
        self.key = crypto.session_key(key, duck_id, nonce, app_nonce)
        return dict(duck_proof=crypto.duck_proof(key, duck_id, nonce, app_nonce))

    async def op_status(self, msg):
        return await asyncio.to_thread(self.app.status)

    async def op_net_status(self, msg):
        return await asyncio.to_thread(self.wifi.status)

    async def op_wifi_scan(self, msg):
        return dict(networks=await asyncio.to_thread(self.wifi.scan))

    async def op_wifi_saved(self, msg):
        return dict(networks=await asyncio.to_thread(self.wifi.saved))

    async def op_wifi_connect(self, msg):
        ssid, sealed, hidden = msg.get('ssid'), msg.get('password'), msg.get('hidden', False)
        _check_ssid(ssid)
        if not isinstance(hidden, bool):
            raise ValueError('hidden must be true or false')
        password = crypto.open_secret(self.key, ssid, sealed) if sealed is not None else None
        if password is not None and not 8 <= len(password) <= 63:
            raise ValueError('a WPA password has 8 to 63 characters')
        if self.connecting:
            raise ValueError('already connecting; wait for the result')
        self.connecting = True

        async def attempt():
            try:
                result = await asyncio.to_thread(self.wifi.connect, ssid, password, hidden)
            except (ValueError, OSError) as exc:
                result = dict(state='failed', ssid=ssid, error=str(exc))
            finally:
                self.connecting = False
            await self.send({'ev': 'net', **result})
        task = asyncio.ensure_future(attempt())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return dict(state='connecting', ssid=ssid)

    async def op_wifi_forget(self, msg):
        ssid = msg.get('ssid')
        _check_ssid(ssid)
        return dict(removed=await asyncio.to_thread(self.wifi.forget, ssid))

    async def op_wifi_priority(self, msg):
        ssid, priority = msg.get('ssid'), msg.get('priority')
        _check_ssid(ssid)
        if not isinstance(priority, int) or isinstance(priority, bool) or not -999 <= priority <= 999:
            raise ValueError('priority must be a whole number from -999 to 999')
        return dict(updated=await asyncio.to_thread(self.wifi.set_priority, ssid, priority))

    async def op_mode(self, msg):
        mode = msg.get('mode')
        if mode not in REMOTE_MODES:
            raise ValueError('mode must be one of ' + ', '.join(REMOTE_MODES))
        return await asyncio.to_thread(self.app.mode, mode)

    async def op_command(self, msg):
        fields = {k: msg[k] for k in ('twist', 'head', 'mouth') if k in msg}
        if not fields:
            raise ValueError('command needs twist, head or mouth')
        await asyncio.to_thread(self.app.command, **fields)
        if 'twist' in fields:
            self.drove = True

    async def op_action(self, msg):
        name = msg.get('name')
        if name not in ACTIONS:
            raise ValueError('action must be pick or roulade')
        return await asyncio.to_thread(self.app.action, name)


def _check_ssid(ssid):
    if not isinstance(ssid, str) or not 1 <= len(ssid.encode('utf-8')) <= 32:
        raise ValueError('ssid must be 1 to 32 bytes')
