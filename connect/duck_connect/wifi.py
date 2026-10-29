"""Wi-Fi through NetworkManager's nmcli: scan, connect, saved networks and their priority.

All calls block; the session runs them in a worker thread. `run` is injectable so
tests can replay recorded nmcli output.
"""
import subprocess

WIFI_TYPE = '802-11-wireless'


def run_nmcli(args, timeout=40):
    p = subprocess.run(['nmcli', *args], capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def split_terse(line):
    """Split one line of `nmcli -t` output: ':' separates fields, '\\:' and '\\\\' are escapes."""
    fields, current, escaped = [], [], False
    for ch in line:
        if escaped:
            current.append(ch)
            escaped = False
        elif ch == '\\':
            escaped = True
        elif ch == ':':
            fields.append(''.join(current))
            current = []
        else:
            current.append(ch)
    fields.append(''.join(current))
    return fields


class Wifi:
    def __init__(self, run=run_nmcli):
        self.run = run

    def _ok(self, args, timeout=40):
        code, out, err = self.run(args, timeout)
        if code != 0:
            raise ValueError((err or out).strip().splitlines()[-1] if (err or out).strip() else f'nmcli exited {code}')
        return out

    def _rows(self, args):
        return [split_terse(line) for line in self._ok(args).splitlines() if line]

    def device(self):
        for dev, kind, *_ in self._rows(['-t', '-f', 'DEVICE,TYPE', 'device', 'status']):
            if kind == 'wifi':
                return dev
        raise ValueError('no Wi-Fi device found')

    def _profiles(self):
        """Saved Wi-Fi profiles as (name, ssid, priority)."""
        out = []
        for name, kind, priority in self._rows(['-t', '-f', 'NAME,TYPE,AUTOCONNECT-PRIORITY', 'connection', 'show']):
            if kind == WIFI_TYPE:
                ssid = self._ok(['-g', '802-11-wireless.ssid', 'connection', 'show', name]).strip()
                out.append((name, ssid, int(priority or 0)))
        return out

    def scan(self):
        saved = {ssid for _, ssid, _ in self._profiles()}
        best = {}
        for in_use, ssid, signal, security in self._rows(
                ['-t', '-f', 'IN-USE,SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list', '--rescan', 'yes']):
            if not ssid:
                continue  # hidden networks have no name to show
            entry = dict(ssid=ssid, signal=int(signal or 0), secure=bool(security.strip()),
                         security=security.strip() or 'open', active=in_use.strip() == '*', saved=ssid in saved)
            old = best.get(ssid)
            if old is None or entry['signal'] > old['signal'] or entry['active']:
                entry['active'] = entry['active'] or bool(old and old['active'])
                best[ssid] = entry
        return sorted(best.values(), key=lambda n: (not n['active'], -n['signal']))

    def saved(self):
        return [dict(ssid=ssid, name=name, priority=priority)
                for name, ssid, priority in sorted(self._profiles(), key=lambda p: -p[2])]

    def status(self):
        dev = self.device()
        state, connection = 'disconnected', ''
        for d, kind, st, conn in self._rows(['-t', '-f', 'DEVICE,TYPE,STATE,CONNECTION', 'device', 'status']):
            if d == dev:
                state, connection = st, conn
        ssid = ip = None
        if state == 'connected':
            ssid = self._ok(['-g', '802-11-wireless.ssid', 'connection', 'show', connection]).strip() or connection
            addresses = self._ok(['-g', 'IP4.ADDRESS', 'device', 'show', dev]).strip()
            ip = addresses.split('|')[0].split('/')[0].strip() or None
        return dict(state=state, ssid=ssid, ip=ip, device=dev)

    def connect(self, ssid, password=None, hidden=False):
        """Join a network and keep it as a saved profile. Returns the resulting status."""
        dev = self.device()
        if password is not None:
            # Replace an old profile for this SSID so a new password takes effect.
            for name, saved_ssid, _ in self._profiles():
                if saved_ssid == ssid:
                    self._ok(['connection', 'delete', name])
        args = ['--wait', '30', 'device', 'wifi', 'connect', ssid, 'ifname', dev]
        if password is not None:
            args += ['password', password]
        if hidden:
            args += ['hidden', 'yes']
        code, out, err = self.run(args, 45)
        if code != 0:
            message = (err or out).strip().splitlines()
            return dict(state='failed', ssid=ssid, error=message[-1] if message else f'nmcli exited {code}')
        return {**self.status(), 'ssid': ssid}

    def forget(self, ssid):
        removed = 0
        for name, saved_ssid, _ in self._profiles():
            if saved_ssid == ssid:
                self._ok(['connection', 'delete', name])
                removed += 1
        if not removed:
            raise ValueError(f'no saved network named {ssid}')
        return removed

    def set_priority(self, ssid, priority):
        updated = 0
        for name, saved_ssid, _ in self._profiles():
            if saved_ssid == ssid:
                self._ok(['connection', 'modify', name, 'connection.autoconnect-priority', str(priority)])
                updated += 1
        if not updated:
            raise ValueError(f'no saved network named {ssid}')
        return updated
