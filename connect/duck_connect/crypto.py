"""Pairing proofs and the session key, all derived from the sticker's pairing key.

The key string (22 base64url characters) is used as UTF-8 bytes, as in the web
console's pairing (python/access.py). Each side adds a random nonce; both prove
they know the key, so a fake duck learns nothing and cannot read a Wi-Fi password.
"""
import base64
import hashlib
import hmac
import secrets


def nonce():
    return secrets.token_urlsafe(16)


def _mac(key, label, duck_id, duck_nonce, app_nonce):
    message = f'{label}:{duck_id}:{duck_nonce}:{app_nonce}'.encode('utf-8')
    return hmac.new(key.encode('utf-8'), message, hashlib.sha256).digest()


def app_proof(key, duck_id, duck_nonce, app_nonce):
    return _mac(key, 'xgoduck-ble-app', duck_id, duck_nonce, app_nonce).hex()


def duck_proof(key, duck_id, duck_nonce, app_nonce):
    return _mac(key, 'xgoduck-ble-duck', duck_id, duck_nonce, app_nonce).hex()


def session_key(key, duck_id, duck_nonce, app_nonce):
    return _mac(key, 'xgoduck-ble-session', duck_id, duck_nonce, app_nonce)


def same(a, b):
    return isinstance(a, str) and isinstance(b, str) and hmac.compare_digest(a, b)


def _wifi_aad(ssid):
    return b'xgoduck-wifi:' + ssid.encode('utf-8')


def open_secret(session, ssid, sealed):
    """Decrypt a Wi-Fi password: base64(12-byte nonce + AES-256-GCM ciphertext and tag), bound to the SSID."""
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    try:
        raw = base64.b64decode(sealed, validate=True)
    except (ValueError, TypeError):
        raise ValueError('password is not base64')
    if len(raw) < 12 + 16:
        raise ValueError('password is too short to be sealed')
    try:
        return AESGCM(session).decrypt(raw[:12], raw[12:], _wifi_aad(ssid)).decode('utf-8')
    except (InvalidTag, UnicodeDecodeError):
        raise ValueError('password could not be opened; pair again')


def seal_secret(session, ssid, password):
    """The phone's side of open_secret, used by tests and the desktop test client."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    iv = secrets.token_bytes(12)
    return base64.b64encode(iv + AESGCM(session).encrypt(iv, password.encode('utf-8'), _wifi_aad(ssid))).decode()
