"""The XGO Duck app's REST API on 127.0.0.1:9527, as seen by duck-connect.

When the app requires pairing, duck-connect pairs itself like a browser would: it
answers the app's challenge with the sticker key and keeps the token in a file,
so restarts reuse one token instead of filling the app's list of paired clients.
"""
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

CLIENT_NAME = 'duck-connect'


class AppError(ValueError):
    pass


class DuckApp:
    def __init__(self, identity, base='http://127.0.0.1:9527', token_file=None, opener=urllib.request.urlopen):
        self.identity, self.base, self.opener = identity, base.rstrip('/'), opener
        self.token_file = Path(token_file) if token_file else None
        self.token = self._read_token()

    def _read_token(self):
        try:
            return self.token_file.read_text().strip() if self.token_file else ''
        except OSError:
            return ''

    def _save_token(self, token):
        self.token = token
        if self.token_file:
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(self.token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'w') as f:
                f.write(token)

    def _call(self, method, path, body=None, auth=True):
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            request.add_header('Content-Type', 'application/json')
        if auth and self.token:
            request.add_header('Authorization', 'Bearer ' + self.token)
        try:
            with self.opener(request, timeout=3) as response:
                return json.loads(response.read() or b'{}')
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read() or b'{}').get('detail')
            except ValueError:
                detail = None
            error = AppError(detail or f'app answered {exc.code}')
            error.status = exc.code
            raise error
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f'XGO Duck app not reachable: {getattr(exc, "reason", exc)}')

    def _pair(self):
        self.identity.reload()
        if not self.identity.key:
            raise AppError(self.identity.error or 'duck identity unavailable')
        c = self._call('GET', '/api/pair/challenge', auth=False)
        message = f'xgoduck-pair:{c["id"]}:{c["nonce"]}'.encode()
        proof = hmac.new(self.identity.key.encode(), message, hashlib.sha256).hexdigest()
        self._save_token(self._call('POST', '/api/pair', dict(nonce=c['nonce'], proof=proof, name=CLIENT_NAME),
                                    auth=False)['token'])

    def _control(self, path, body):
        """POST that needs control rights; pairs once and retries if the app asks for it."""
        try:
            return self._call('POST', path, body)
        except AppError as exc:
            if getattr(exc, 'status', None) not in (401, 403):
                raise
        self._pair()
        return self._call('POST', path, body)

    def status(self):
        s = self._call('GET', '/api/status', auth=False)
        battery = s.get('battery') or {}
        recovery = s.get('recovery') or {}
        return dict(mode=s.get('mode'), enabled=s.get('enabled'), control_ready=s.get('control_ready'),
                    servos=len(s.get('servo_ids') or []), missing=s.get('missing_joint_ids') or [],
                    imu_ok=s.get('imu_ok'), feedback_hz=round(s.get('feedback_hz') or 0, 1),
                    battery=dict(voltage=battery.get('voltage'), percent=battery.get('percent'),
                                 level=battery.get('level')),
                    phase=recovery.get('phase'), error=s.get('last_error') or None)

    def command(self, **fields):
        return self._control('/api/command', fields)

    def mode(self, mode):
        return self._control('/api/mode', dict(mode=mode))

    def action(self, name):
        return self._control('/api/' + name, {})
