"""Stand-ins for the identity file, nmcli and the XGO Duck app."""
DUCK_ID = '71577AA6'
KEY = 'q8Zr3VbN0xLwT5mHc2YkJa'


class FakeIdentity:
    def __init__(self, duck_id=DUCK_ID, key=KEY):
        self.id, self.key, self.error = duck_id, key, ''

    def reload(self):
        return self


class FakeWifi:
    def __init__(self):
        self.calls = []

    def scan(self):
        self.calls.append(('scan',))
        return [dict(ssid=f'net-{i:02d}', signal=90 - i, secure=True, security='WPA2', active=i == 0, saved=i < 2)
                for i in range(12)]

    def saved(self):
        return [dict(ssid='home', name='home', priority=10)]

    def status(self):
        return dict(state='connected', ssid='home', ip='192.168.1.45', device='wlan0')

    def connect(self, ssid, password=None, hidden=False):
        self.calls.append(('connect', ssid, password, hidden))
        return dict(state='connected', ssid=ssid, ip='192.168.1.50', device='wlan0')

    def forget(self, ssid):
        self.calls.append(('forget', ssid))
        return 1

    def set_priority(self, ssid, priority):
        self.calls.append(('priority', ssid, priority))
        return 1


class FakeApp:
    def __init__(self):
        self.commands, self.modes, self.actions = [], [], []

    def status(self):
        return dict(mode='shadow', enabled=False, servos=15, battery=dict(voltage=7.7, percent=55, level='ok'))

    def command(self, **fields):
        self.commands.append(fields)
        return {'ok': True}

    def mode(self, mode):
        self.modes.append(mode)
        return dict(mode=mode)

    def action(self, name):
        self.actions.append(name)
        return dict(model=f'xgoduck_{name}.onnx')
