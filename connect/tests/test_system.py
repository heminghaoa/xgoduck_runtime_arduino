"""nmcli parsing, the app bridge, Bonjour, and the BLE server logic without BlueZ."""
import asyncio
import io
import json
import os
import urllib.error

import pytest

from duck_connect import avahi, crypto, framing
from duck_connect.duck_app import AppError, DuckApp
from duck_connect.wifi import Wifi, split_terse
from fakes import DUCK_ID, KEY, FakeApp, FakeIdentity, FakeWifi


# ---- nmcli ----

class FakeNmcli:
    """Answers nmcli calls from a table of argument tuples; records everything it is asked."""

    def __init__(self, table):
        self.table, self.calls = table, []

    def __call__(self, args, timeout=40):
        self.calls.append(tuple(args))
        for key, result in self.table.items():
            if tuple(args[:len(key)]) == key:
                return result if isinstance(result, tuple) else (0, result, '')
        return 0, '', ''


DEVICES = 'eth0:ethernet:unavailable:\nwlan0:wifi:connected:home\nlo:loopback:connected (externally):lo\n'
PROFILES = 'home:802-11-wireless:10\nWired connection 1:802-3-ethernet:0\ncafe\\:2F:802-11-wireless:0\n'
SCAN = '*:home:82:WPA2\n :home:40:WPA2\n :cafe\\:2F:61:WPA1 WPA2\n ::70:WPA2\n :Free Wi-Fi:55:\n'


def nmcli(extra=None):
    table = {('-t', '-f', 'DEVICE,TYPE,STATE,CONNECTION'): DEVICES, ('-t', '-f', 'DEVICE,TYPE'): DEVICES,
             ('-t', '-f', 'NAME,TYPE,AUTOCONNECT-PRIORITY'): PROFILES,
             ('-g', '802-11-wireless.ssid', 'connection', 'show', 'home'): 'home\n',
             ('-g', '802-11-wireless.ssid', 'connection', 'show', 'cafe:2F'): 'cafe:2F\n',
             ('-g', 'IP4.ADDRESS'): '192.168.1.45/24\n',
             ('-t', '-f', 'IN-USE,SSID,SIGNAL,SECURITY'): SCAN}
    table.update(extra or {})
    return FakeNmcli(table)


def test_terse_split_handles_escapes():
    assert split_terse('cafe\\:2F:802-11-wireless:0') == ['cafe:2F', '802-11-wireless', '0']
    assert split_terse('a\\\\b::c') == ['a\\b', '', 'c']


def test_scan_merges_access_points_and_skips_hidden_networks():
    networks = Wifi(nmcli()).scan()
    assert [n['ssid'] for n in networks] == ['home', 'cafe:2F', 'Free Wi-Fi']
    home, cafe, free = networks
    assert home['active'] and home['signal'] == 82 and home['saved']
    assert cafe['saved'] and not cafe['active'] and cafe['security'] == 'WPA1 WPA2'
    assert not free['secure'] and free['security'] == 'open' and not free['saved']


def test_status_and_saved():
    wifi = Wifi(nmcli())
    assert wifi.status() == dict(state='connected', ssid='home', ip='192.168.1.45', device='wlan0')
    assert [n['ssid'] for n in wifi.saved()] == ['home', 'cafe:2F']


def test_connect_replaces_an_old_profile_and_passes_the_password():
    run = nmcli()
    result = Wifi(run).connect('home', 'correct horse')
    assert ('connection', 'delete', 'home') in run.calls
    connect = [c for c in run.calls if 'connect' in c][0]
    assert connect[:6] == ('--wait', '30', 'device', 'wifi', 'connect', 'home') and connect[-2:] == ('password', 'correct horse')
    assert result['state'] == 'connected' and result['ssid'] == 'home'


def test_connect_failure_is_reported_not_raised():
    run = nmcli({('--wait', '30', 'device', 'wifi', 'connect'): (4, '', 'Error: Connection activation failed: Secrets were required.\n')})
    result = Wifi(run).connect('cafe:2F', 'wrong password')
    assert result['state'] == 'failed' and 'Secrets were required' in result['error']


def test_forget_and_priority_need_a_saved_network():
    run = nmcli()
    wifi = Wifi(run)
    assert wifi.forget('cafe:2F') == 1 and ('connection', 'delete', 'cafe:2F') in run.calls
    assert wifi.set_priority('home', 20) == 1
    assert ('connection', 'modify', 'home', 'connection.autoconnect-priority', '20') in run.calls
    with pytest.raises(ValueError):
        wifi.forget('nowhere')


# ---- the XGO Duck app ----

class FakeHttp:
    """urlopen stand-in for the app: requires pairing for POSTs when locked."""

    def __init__(self, locked):
        self.locked, self.token, self.requests = locked, None, []

    def __call__(self, request, timeout=None):
        body = json.loads(request.data) if request.data else None
        auth = request.headers.get('Authorization')
        self.requests.append((request.get_method(), request.full_url, body, auth))
        path = request.full_url.split('9527', 1)[1]
        if path == '/api/pair/challenge':
            return self._json(dict(id=DUCK_ID, nonce='n1', ttl_s=60))
        if path == '/api/pair':
            expected = crypto.hmac.new(KEY.encode(), f'xgoduck-pair:{DUCK_ID}:n1'.encode(), crypto.hashlib.sha256).hexdigest()
            if body['proof'] != expected:
                raise self._error(403, 'wrong key')
            self.token = 'tok-1'
            return self._json(dict(token='tok-1', id='c1'))
        if path == '/api/status':
            return self._json(dict(mode='shadow', enabled=False, servo_ids=list(range(15)), imu_ok=True,
                                   feedback_hz=99.84, battery=dict(voltage=7.7, percent=55, level='ok'),
                                   recovery=dict(phase='walk')))
        if self.locked and auth != f'Bearer {self.token}':
            raise self._error(401, 'pairing required')
        return self._json({'ok': True})

    @staticmethod
    def _json(data):
        return io.BytesIO(json.dumps(data).encode())

    @staticmethod
    def _error(code, detail):
        return urllib.error.HTTPError('http://x', code, 'err', {}, io.BytesIO(json.dumps({'detail': detail}).encode()))


def test_app_status_is_compacted():
    s = DuckApp(FakeIdentity(), opener=FakeHttp(False)).status()
    assert s['servos'] == 15 and s['battery']['percent'] == 55 and s['phase'] == 'walk' and s['feedback_hz'] == 99.8


def test_app_pairs_itself_once_when_locked(tmp_path):
    http, token_file = FakeHttp(True), tmp_path / 'app-token'
    app = DuckApp(FakeIdentity(), opener=http, token_file=token_file)
    assert app.command(twist=[0.1, 0, 0]) == {'ok': True}
    assert token_file.read_text() == 'tok-1' and oct(os.stat(token_file).st_mode & 0o777) == '0o600'
    pairs = [r for r in http.requests if r[1].endswith('/api/pair')]
    app.mode('hold')  # reuses the token
    assert len([r for r in http.requests if r[1].endswith('/api/pair')]) == len(pairs) == 1
    assert DuckApp(FakeIdentity(), opener=http, token_file=token_file).token == 'tok-1'


def test_app_unreachable_is_a_clear_error():
    def refuse(request, timeout=None):
        raise urllib.error.URLError('Connection refused')
    with pytest.raises(AppError, match='not reachable'):
        DuckApp(FakeIdentity(), opener=refuse).status()


# ---- Bonjour ----

def test_bonjour_file_is_written_once(tmp_path):
    path = tmp_path / 'xgoduck.service'
    assert avahi.publish(DUCK_ID, path=path) and not avahi.publish(DUCK_ID, path=path)
    text = path.read_text()
    assert '<type>_xgoduck._tcp</type>' in text and f'id={DUCK_ID}' in text and '<port>9527</port>' in text


# ---- BLE server logic, with the transport replaced ----

class FakeTx:
    def __init__(self):
        self.chunks = []

    def notify(self, data):
        self.chunks.append(bytes(data))


def test_server_frames_replies_to_the_link_mtu_and_cleans_up():
    from duck_connect.ble import Server

    async def go():
        app, wifi = FakeApp(), FakeWifi()
        server = Server(FakeIdentity(), wifi, app, publish_bonjour=False)
        server.writes, server.tx = asyncio.Queue(), FakeTx()
        worker = asyncio.ensure_future(server._handle_writes())
        phone, inbox, reader = '/org/bluez/hci0/dev_11_22', [], framing.Reassembler()

        async def ask(message, mtu=23):
            for chunk in framing.chunks(framing.encode(message), 20):
                server.on_write(phone, chunk, mtu)
            for _ in range(50):
                await asyncio.sleep(0)
            while server.tx.chunks:
                chunk = server.tx.chunks.pop(0)
                assert len(chunk) <= mtu - 3
                inbox.extend(reader.feed(chunk)[0])
            return inbox[-1]

        assert (await ask({'op': 'hello', 'id': 1, 'chunk': 182}))['duck_id'] == DUCK_ID
        nonce = (await ask({'op': 'challenge', 'id': 2}))['nonce']
        proof = crypto.app_proof(KEY, DUCK_ID, nonce, 'phone-nonce')
        assert (await ask({'op': 'pair', 'id': 3, 'nonce': nonce, 'app_nonce': 'phone-nonce', 'proof': proof}))['ok']
        networks = await ask({'op': 'wifi_scan', 'id': 4}, mtu=185)
        assert len(networks['networks']) == 12
        await ask({'op': 'command', 'id': 5, 'twist': [0.2, 0, 0]})
        assert json.loads(server.read_info()) == dict(proto=1, duck_id=DUCK_ID, name='XGO Duck')

        await server.device_gone(phone)
        assert app.commands[-1] == {'twist': [0.0, 0.0, 0.0]} and phone not in server.sessions
        # The next connection from the same phone starts unpaired.
        reply = await ask({'op': 'wifi_scan', 'id': 6})
        assert not reply['ok'] and reply['error'] == 'pair first'
        worker.cancel()
    asyncio.run(go())
