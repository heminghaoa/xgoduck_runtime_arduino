"""duck-connect: Bluetooth pairing, Wi-Fi setup and Bonjour for the XGO Duck.

Runs on the Uno Q's Linux side as a systemd service, outside App Lab's container,
and talks to the XGO Duck app over http://127.0.0.1:9527. See docs/duck-connect.md.
"""
PROTOCOL_VERSION = 1
