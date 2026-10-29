"""Messages over a BLE characteristic: a 2-byte big-endian length, then compact UTF-8 JSON.

The stream of frames is cut into chunks that fit one ATT write or notification
(MTU - 3 bytes). GATT delivers them in order, so the receiver only has to join
the bytes back up.
"""
import json

MAX_MESSAGE = 8192
DEFAULT_CHUNK = 20  # ATT_MTU 23 - 3, until the link reports a larger MTU


def encode(message):
    body = json.dumps(message, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    if len(body) > MAX_MESSAGE:
        raise ValueError('message too large')
    return len(body).to_bytes(2, 'big') + body


def chunks(data, size):
    size = max(1, int(size))
    return [data[i:i + size] for i in range(0, len(data), size)]


class Reassembler:
    """Collects chunks from one central and yields complete messages."""

    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        """Add one chunk; return (messages, error). On a bad frame the buffer is dropped."""
        self.buffer.extend(data)
        messages, error = [], None
        while len(self.buffer) >= 2:
            size = int.from_bytes(self.buffer[:2], 'big')
            if size > MAX_MESSAGE:
                self.buffer.clear()
                return messages, 'message too large'
            if len(self.buffer) < 2 + size:
                break
            body = bytes(self.buffer[2:2 + size])
            del self.buffer[:2 + size]
            try:
                message = json.loads(body.decode('utf-8'))
            except (UnicodeDecodeError, ValueError):
                error = 'message is not JSON'
                continue
            if isinstance(message, dict):
                messages.append(message)
            else:
                error = 'message must be an object'
        return messages, error
