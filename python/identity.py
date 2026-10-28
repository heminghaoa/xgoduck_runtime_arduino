"""This duck's ID and pairing key: created on first start, kept in the data folder.

The key is printed on the pairing sticker and never leaves the duck over the
network once the sticker is claimed.
"""
import json
import re
import secrets
import threading
from datetime import datetime, timezone
from settings import DATA_DIR, write_json

IDENTITY_FILE = DATA_DIR / 'identity.json'
VERSION = 1
ID_RE = re.compile(r'[0-9A-F]{8}')
KEY_RE = re.compile(r'[A-Za-z0-9_-]{22}')

class Identity:
    def __init__(self):
        self.lock = threading.Lock()
        self.id = self.key = self.created = None
        self.claimed = False
        self.error = ''
        try:
            self._load_or_create()
        except (OSError, ValueError) as exc:
            self.error = f'identity unavailable: {exc}'

    def _load_or_create(self):
        try:
            data = json.loads(IDENTITY_FILE.read_text(encoding='utf-8'))
        except FileNotFoundError:
            # 32-bit ID for display and discovery; 128-bit key for pairing.
            data = dict(version=VERSION, id=secrets.token_hex(4).upper(), key=secrets.token_urlsafe(16),
                        created=datetime.now(timezone.utc).isoformat(timespec='seconds'), claimed=False)
            write_json(IDENTITY_FILE, data, mode=0o600)
        # A damaged file is never replaced silently: that would void the printed sticker.
        if (not isinstance(data, dict) or data.get('version') != VERSION
                or not ID_RE.fullmatch(str(data.get('id'))) or not KEY_RE.fullmatch(str(data.get('key')))
                or not isinstance(data.get('claimed'), bool)):
            raise ValueError(f'{IDENTITY_FILE.name} is damaged; delete it to create a new ID and sticker')
        self.id, self.key, self.claimed = data['id'], data['key'], data['claimed']
        self.created = data.get('created')

    def public(self):
        return dict(id=self.id, claimed=self.claimed, created=self.created, error=self.error)

    def pairing_uri(self):
        return f'xgoduck://pair?id={self.id}&k={self.key}&v={VERSION}'

    def sticker(self):
        """Pairing QR as inline SVG, only until the sticker is claimed."""
        if self.error:
            raise ValueError(self.error)
        if self.claimed:
            raise PermissionError('the sticker was already claimed')
        import segno
        qr = segno.make(self.pairing_uri(), error='m', micro=False)
        return dict(id=self.id, uri=self.pairing_uri(), svg=qr.svg_inline(border=2, omitsize=True))

    def claim(self):
        with self.lock:
            if self.error:
                raise ValueError(self.error)
            if not self.claimed:
                write_json(IDENTITY_FILE, dict(version=VERSION, id=self.id, key=self.key,
                                               created=self.created, claimed=True), mode=0o600)
                self.claimed = True
        return self.public()
