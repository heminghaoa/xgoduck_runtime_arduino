"""Read the duck's ID and pairing key from the XGO Duck app's data/identity.json.

The app creates the file on its first start (python/identity.py); duck-connect only
reads it, so the printed sticker keeps working for both.
"""
import json
import re
from pathlib import Path

ID_RE = re.compile(r'[0-9A-F]{8}')
KEY_RE = re.compile(r'[A-Za-z0-9_-]{22}')


class Identity:
    def __init__(self, path):
        self.path = Path(path)
        self.id = self.key = None
        self.error = ''
        self.reload()

    def reload(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if (not isinstance(data, dict) or data.get('version') != 1
                    or not ID_RE.fullmatch(str(data.get('id'))) or not KEY_RE.fullmatch(str(data.get('key')))):
                raise ValueError('unknown or damaged file')
            self.id, self.key, self.error = data['id'], data['key'], ''
        except FileNotFoundError:
            self.id = self.key = None
            self.error = f'{self.path} not found; start the XGO Duck app once to create it'
        except (OSError, ValueError) as exc:
            self.id = self.key = None
            self.error = f'{self.path}: {exc}'
        return self
