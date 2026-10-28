"""Who may control the duck.

A phone or browser proves it knows the sticker's pairing key by answering a
one-time challenge: proof = HMAC-SHA256(key, "xgoduck-pair:<id>:<nonce>"), hex.
The key itself never crosses the network. The duck then issues a bearer token
and keeps only its SHA-256.

Until require_pairing is switched on, requests without a token still work, so
the web console behaves as before. Deleting data/access.json reopens the duck.
"""
import hashlib
import hmac
import json
import secrets
import threading
import time
from datetime import datetime, timezone
from settings import DATA_DIR, write_json

ACCESS_FILE = DATA_DIR / 'access.json'
VERSION = 1
CHALLENGE_TTL_S = 60
MAX_CHALLENGES = 32
MAX_TOKENS = 20
NAME_MAX = 32
# Reachable without a token even when pairing is required.
PUBLIC_API = {('GET', '/api/status'), ('GET', '/api/identity'),
              ('GET', '/api/pair/challenge'), ('POST', '/api/pair')}

def _digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

class Access:
    def __init__(self, identity):
        self.identity = identity
        self.lock = threading.Lock()
        self.require_pairing = False
        self.tokens = []
        self.challenges = {}
        self.error = ''
        try:
            data = json.loads(ACCESS_FILE.read_text(encoding='utf-8'))
            if (not isinstance(data, dict) or data.get('version') != VERSION
                    or not isinstance(data.get('require_pairing'), bool) or not isinstance(data.get('tokens'), list)
                    or not all(isinstance(e, dict) and all(isinstance(e.get(k), str) for k in ('id', 'name', 'hash', 'created'))
                               for e in data['tokens'])):
                raise ValueError('unknown file version')
            self.require_pairing, self.tokens = data['require_pairing'], data['tokens']
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
            # Fail closed: a damaged file must not quietly open a locked duck.
            self.require_pairing = True
            self.error = f'access file not loaded ({exc}); delete data/access.json to reopen the duck'

    def _save_locked(self):
        write_json(ACCESS_FILE, dict(version=VERSION, require_pairing=self.require_pairing,
                                     tokens=self.tokens), mode=0o600)

    def challenge(self):
        if self.identity.error:
            raise ValueError(self.identity.error)
        now = time.monotonic()
        nonce = secrets.token_urlsafe(16)
        with self.lock:
            self.challenges = {n: t for n, t in self.challenges.items() if t > now}
            while len(self.challenges) >= MAX_CHALLENGES:
                self.challenges.pop(next(iter(self.challenges)))
            self.challenges[nonce] = now + CHALLENGE_TTL_S
        return dict(id=self.identity.id, nonce=nonce, ttl_s=CHALLENGE_TTL_S)

    def pair(self, nonce, proof, name='Phone'):
        if self.identity.error:
            raise ValueError(self.identity.error)
        if not isinstance(name, str) or not name.isprintable() or not 1 <= len(name.strip()) <= NAME_MAX:
            raise ValueError(f'name must be 1 to {NAME_MAX} printable characters')
        with self.lock:
            expires = self.challenges.pop(nonce, None) if isinstance(nonce, str) else None
            if expires is None or expires < time.monotonic():
                raise ValueError('challenge expired; request a new one')
            message = f'xgoduck-pair:{self.identity.id}:{nonce}'.encode()
            expected = hmac.new(self.identity.key.encode(), message, hashlib.sha256).hexdigest()
            if not isinstance(proof, str) or not hmac.compare_digest(expected, proof.lower()):
                raise PermissionError('wrong pairing key')
            token = secrets.token_urlsafe(32)
            entry = dict(id=secrets.token_hex(4), name=name.strip(), hash=_digest(token),
                         created=datetime.now(timezone.utc).isoformat(timespec='seconds'))
            tokens = (self.tokens + [entry])[-MAX_TOKENS:]
            previous, self.tokens = self.tokens, tokens
            try:
                self._save_locked()
            except OSError:
                self.tokens = previous
                raise
        return dict(token=token, token_id=entry['id'], duck_id=self.identity.id)

    def check(self, token):
        """Return the public entry for a valid token, else None."""
        if not token:
            return None
        digest = _digest(token)
        with self.lock:
            for entry in self.tokens:
                if hmac.compare_digest(entry['hash'], digest):
                    return {k: entry[k] for k in ('id', 'name', 'created')}
        return None

    def status(self, client=None):
        with self.lock:
            paired = [{k: e[k] for k in ('id', 'name', 'created')} for e in self.tokens]
            return dict(require_pairing=self.require_pairing, paired=paired, you=client, error=self.error)

    def set_require_pairing(self, enabled, client):
        if not isinstance(enabled, bool):
            raise ValueError('require_pairing must be true or false')
        # Only a paired client may lock, so whoever locks can still get in.
        if enabled and client is None:
            raise PermissionError('pair this browser or phone first, then turn this on')
        with self.lock:
            previous, self.require_pairing = self.require_pairing, enabled
            try:
                self._save_locked()
            except OSError:
                self.require_pairing = previous
                raise
        return self.status(client)

    def revoke(self, token_id):
        with self.lock:
            tokens = [e for e in self.tokens if e['id'] != token_id]
            if len(tokens) == len(self.tokens):
                raise ValueError('no such paired device')
            previous, self.tokens = self.tokens, tokens
            try:
                self._save_locked()
            except OSError:
                self.tokens = previous
                raise
        return self.status()

    def install(self, app):
        """Add the token check to a FastAPI app."""
        from fastapi.responses import JSONResponse

        @app.middleware('http')
        async def check_token(request, call_next):
            auth = request.headers.get('authorization', '')
            request.state.client = self.check(auth[7:] if auth[:7].lower() == 'bearer ' else '')
            path = request.url.path
            if (self.require_pairing and request.state.client is None and path.startswith('/api/')
                    and (request.method, path) not in PUBLIC_API):
                return JSONResponse({'detail': 'pairing required: pair this browser on the Pairing page'},
                                    status_code=401)
            return await call_next(request)
