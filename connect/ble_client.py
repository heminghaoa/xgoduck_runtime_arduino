"""Desktop test client for duck-connect (roadmap 2.5), playing the phone's part over Bluetooth.

Needs a Mac or PC with Bluetooth and: pip install bleak cryptography
The pairing key comes from the sticker, from --key, or from the board over SSH (--ssh).

  python connect/ble_client.py scan
  python connect/ble_client.py --ssh arduino@192.168.1.45 status
  python connect/ble_client.py --ssh arduino@192.168.1.45 wifi-scan
  python connect/ble_client.py --ssh arduino@192.168.1.45 wifi-connect "My Wi-Fi"
"""
import argparse
import asyncio
import getpass
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from duck_connect import crypto, framing  # noqa: E402

SERVICE_UUID = 'b5f1a6e0-6c1d-4f5e-9a37-2d0c8e4b7a10'
INFO_UUID = 'b5f1a6e1-6c1d-4f5e-9a37-2d0c8e4b7a10'
RX_UUID = 'b5f1a6e2-6c1d-4f5e-9a37-2d0c8e4b7a10'
TX_UUID = 'b5f1a6e3-6c1d-4f5e-9a37-2d0c8e4b7a10'
IDENTITY = '~/ArduinoApps/xgoduck_runtime_arduino/data/identity.json'


def key_from_args(args):
    if args.key:
        return args.key.split('k=')[-1].split('&')[0]  # the bare key or the sticker's xgoduck:// link
    if args.ssh:
        out = subprocess.run(['ssh', args.ssh, 'cat ' + IDENTITY], capture_output=True, text=True, check=True).stdout
        return json.loads(out)['key']
    sys.exit('this command needs the pairing key: --key or --ssh')


class Duck:
    def __init__(self, client):
        self.client, self.reader, self.inbox, self.next_id = client, framing.Reassembler(), asyncio.Queue(), 0
        self.chunk = max(20, (client.mtu_size or 23) - 3)

    async def start(self):
        def on_notify(_, data):
            messages, error = self.reader.feed(bytes(data))
            for m in messages:
                self.inbox.put_nowait(m)
            if error:
                print('frame error:', error)
        await self.client.start_notify(TX_UUID, on_notify)

    async def ask(self, op, timeout=20, **fields):
        self.next_id += 1
        rid = self.next_id
        for chunk in framing.chunks(framing.encode({'op': op, 'id': rid, **fields}), self.chunk):
            await self.client.write_gatt_char(RX_UUID, chunk, response=True)
        while True:
            m = await asyncio.wait_for(self.inbox.get(), timeout)
            if m.get('id') == rid:
                if not m.get('ok'):
                    raise RuntimeError(f'{op}: {m.get("error")}')
                return m
            print('event:', json.dumps(m, ensure_ascii=False))

    async def pair(self, key):
        hello = await self.ask('hello', chunk=self.chunk)
        challenge = await self.ask('challenge')
        duck_id, nonce, app_nonce = challenge['duck_id'], challenge['nonce'], crypto.nonce()
        reply = await self.ask('pair', nonce=nonce, app_nonce=app_nonce,
                               proof=crypto.app_proof(key, duck_id, nonce, app_nonce))
        if not crypto.same(reply['duck_proof'], crypto.duck_proof(key, duck_id, nonce, app_nonce)):
            raise RuntimeError('the duck could not prove it knows the key: not your duck?')
        self.session_key = crypto.session_key(key, duck_id, nonce, app_nonce)
        print(f'paired with duck {duck_id} (protocol {hello["proto"]}, chunk {self.chunk} bytes)')


async def find(name_filter):
    from bleak import BleakScanner
    found = await BleakScanner.discover(timeout=6, service_uuids=[SERVICE_UUID], return_adv=True)
    ducks = [(d, adv) for d, adv in found.values() if SERVICE_UUID in (adv.service_uuids or [])]
    return [d for d, adv in ducks if not name_filter or name_filter in (adv.local_name or d.name or '')]


async def main(args):
    from bleak import BleakClient
    ducks = await find(args.name)
    if args.command == 'scan':
        for d in ducks:
            async with BleakClient(d) as c:
                info = json.loads(await c.read_gatt_char(INFO_UUID))
            print(f'{d.address}  {info["name"]}  duck {info["duck_id"]}  protocol {info["proto"]}')
        print(f'{len(ducks)} duck(s) found')
        return
    if not ducks:
        sys.exit('no duck found: is duck-connect running and Bluetooth on?')
    async with BleakClient(ducks[0]) as c:
        duck = Duck(c)
        await duck.start()
        if args.command == 'status':
            print(json.dumps(await duck.ask('status'), indent=2, ensure_ascii=False))
            return
        await duck.pair(key_from_args(args))
        if args.command == 'pair':
            return
        if args.command == 'wifi-scan':
            for n in (await duck.ask('wifi_scan'))['networks']:
                print(f'{"*" if n["active"] else " "} {n["signal"]:3d}  {n["ssid"]}  [{n["security"]}]'
                      f'{"  saved" if n["saved"] else ""}')
        elif args.command == 'wifi-saved':
            print(json.dumps((await duck.ask('wifi_saved'))['networks'], indent=2, ensure_ascii=False))
        elif args.command == 'net-status':
            print(json.dumps(await duck.ask('net_status'), indent=2, ensure_ascii=False))
        elif args.command == 'wifi-connect':
            password = getpass.getpass(f'password for {args.ssid} (empty for an open network): ')
            sealed = crypto.seal_secret(duck.session_key, args.ssid, password) if password else None
            fields = dict(ssid=args.ssid, hidden=args.hidden, **({'password': sealed} if sealed else {}))
            print((await duck.ask('wifi_connect', **fields))['state'], '...')
            while True:
                event = await asyncio.wait_for(duck.inbox.get(), 60)
                if event.get('ev') == 'net':
                    print(json.dumps(event, indent=2, ensure_ascii=False))
                    break
        elif args.command == 'wifi-forget':
            print('removed', (await duck.ask('wifi_forget', ssid=args.ssid))['removed'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--key', help='pairing key, or the whole xgoduck://pair link from the sticker')
    p.add_argument('--ssh', help='read the key from the board, e.g. arduino@192.168.1.45')
    p.add_argument('--name', help='only ducks whose advertised name contains this')
    sub = p.add_subparsers(dest='command', required=True)
    for name in ('scan', 'status', 'pair', 'wifi-scan', 'wifi-saved', 'net-status'):
        sub.add_parser(name)
    c = sub.add_parser('wifi-connect')
    c.add_argument('ssid')
    c.add_argument('--hidden', action='store_true')
    sub.add_parser('wifi-forget').add_argument('ssid')
    asyncio.run(main(p.parse_args()))
