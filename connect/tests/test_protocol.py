import asyncio
import random

from duck_connect import crypto, framing
from duck_connect.session import MAX_PAIR_FAILURES, Session
from fakes import DUCK_ID, KEY, FakeApp, FakeIdentity, FakeWifi


def test_frames_survive_any_chunking():
    messages = [{'op': 'hello', 'id': 1}, {'op': 'wifi_scan', 'id': 2, 'note': 'ü' * 300}, {'op': 'status'}]
    stream = b''.join(framing.encode(m) for m in messages)
    rng = random.Random(4)
    for _ in range(50):
        r, got, i = framing.Reassembler(), [], 0
        while i < len(stream):
            n = rng.randint(1, 40)
            out, error = r.feed(stream[i:i + n])
            assert error is None
            got += out
            i += n
        assert got == messages


def test_bad_frames_are_reported_and_skipped():
    r = framing.Reassembler()
    out, error = r.feed(b'\x00\x03abc' + framing.encode({'op': 'status'}))
    assert error == 'message is not JSON' and out == [{'op': 'status'}]
    out, error = r.feed(b'\xff\xff')
    assert error == 'message too large' and not r.buffer


def test_sealed_password_is_bound_to_its_ssid():
    key = crypto.session_key(KEY, DUCK_ID, 'duck-nonce', 'app-nonce')
    sealed = crypto.seal_secret(key, 'home', 'correct horse')
    assert crypto.open_secret(key, 'home', sealed) == 'correct horse'
    for ssid, k in (('cafe', key), ('home', crypto.session_key(KEY, DUCK_ID, 'other', 'app-nonce'))):
        try:
            crypto.open_secret(k, ssid, sealed)
            raise AssertionError('opened with the wrong ssid or key')
        except ValueError:
            pass


class Phone:
    """Drives a Session the way the iPhone app will."""

    def __init__(self, key=KEY):
        self.key, self.sent = key, []
        self.wifi, self.app = FakeWifi(), FakeApp()
        self.session = Session(FakeIdentity(), self.wifi, self.app, self._receive)
        self.next_id = 0

    async def _receive(self, message):
        self.sent.append(message)

    async def ask(self, op, **fields):
        self.next_id += 1
        await self.session.handle({'op': op, 'id': self.next_id, **fields})
        return [m for m in self.sent if m.get('id') == self.next_id][-1]

    async def pair(self):
        nonce = (await self.ask('challenge'))['nonce']
        app_nonce = crypto.nonce()
        reply = await self.ask('pair', nonce=nonce, app_nonce=app_nonce,
                               proof=crypto.app_proof(self.key, DUCK_ID, nonce, app_nonce))
        if reply['ok']:
            # The phone checks the duck knows the key too before trusting it with a password.
            assert reply['duck_proof'] == crypto.duck_proof(KEY, DUCK_ID, nonce, app_nonce)
            self.session_key = crypto.session_key(self.key, DUCK_ID, nonce, app_nonce)
        return reply


def run(coro):
    return asyncio.run(coro)


def test_hello_and_status_need_no_pairing():
    async def go():
        phone = Phone()
        hello = await phone.ask('hello', chunk=182)
        assert hello['ok'] and hello['duck_id'] == DUCK_ID and hello['proto'] == 1 and phone.session.chunk == 182
        assert (await phone.ask('status'))['battery']['percent'] == 55
        for op in ('wifi_scan', 'net_status', 'mode', 'command'):
            reply = await phone.ask(op)
            assert not reply['ok'] and reply['error'] == 'pair first'
    run(go())


def test_pairing_with_the_sticker_key():
    async def go():
        phone = Phone()
        assert (await phone.pair())['ok'] and phone.session.paired
        assert (await phone.ask('wifi_scan'))['networks'][0]['ssid'] == 'net-00'
    run(go())


def test_wrong_key_is_refused_and_limited():
    async def go():
        phone = Phone(key='x' * 22)
        for _ in range(MAX_PAIR_FAILURES):
            reply = await phone.pair()
            assert not reply['ok'] and reply['error'] == 'wrong pairing key'
        phone.key = KEY
        reply = await phone.pair()
        assert not reply['ok'] and 'too many' in reply['error']
    run(go())


def test_a_challenge_works_once():
    async def go():
        phone = Phone()
        nonce = (await phone.ask('challenge'))['nonce']
        proof = crypto.app_proof(KEY, DUCK_ID, nonce, 'app-nonce-1')
        assert (await phone.ask('pair', nonce=nonce, app_nonce='app-nonce-1', proof=proof))['ok']
        reply = await phone.ask('pair', nonce=nonce, app_nonce='app-nonce-1', proof=proof)
        assert not reply['ok'] and 'challenge expired' in reply['error']
    run(go())


def test_wifi_connect_opens_the_sealed_password_and_reports_back():
    async def go():
        phone = Phone()
        await phone.pair()
        sealed = crypto.seal_secret(phone.session_key, 'home', 'correct horse')
        reply = await phone.ask('wifi_connect', ssid='home', password=sealed)
        assert reply['ok'] and reply['state'] == 'connecting'
        await asyncio.gather(*phone.session.tasks)
        assert ('connect', 'home', 'correct horse', False) in phone.wifi.calls
        event = [m for m in phone.sent if m.get('ev') == 'net'][-1]
        assert event['state'] == 'connected' and event['ip'] == '192.168.1.50'
        # A password sealed for another network is rejected before nmcli sees it.
        reply = await phone.ask('wifi_connect', ssid='cafe', password=sealed)
        assert not reply['ok'] and 'could not be opened' in reply['error']
        reply = await phone.ask('wifi_connect', ssid='home', password=crypto.seal_secret(phone.session_key, 'home', 'short'))
        assert not reply['ok'] and '8 to 63' in reply['error']
    run(go())


def test_control_goes_to_the_app_and_stops_on_disconnect():
    async def go():
        phone = Phone()
        await phone.pair()
        await phone.session.handle({'op': 'command', 'twist': [0.1, 0.0, 0.0]})  # no id: no reply
        assert phone.app.commands == [{'twist': [0.1, 0.0, 0.0]}] and not phone.sent[-1].get('op')
        assert (await phone.ask('mode', mode='hold'))['mode'] == 'hold'
        assert not (await phone.ask('mode', mode='calibrate'))['ok']
        assert (await phone.ask('action', name='pick'))['ok']
        await phone.session.close()
        assert phone.app.commands[-1] == {'twist': [0.0, 0.0, 0.0]} and not phone.session.paired
    run(go())


def test_errors_without_an_id_name_the_op():
    async def go():
        phone = Phone()
        await phone.session.handle({'op': 'command', 'twist': [0.1, 0, 0]})
        assert phone.sent[-1] == {'ok': False, 'error': 'pair first', 'op': 'command'}
        await phone.session.handle({'op': 'fly'})
        assert phone.sent[-1]['error'] == 'unknown op: fly'
    run(go())
