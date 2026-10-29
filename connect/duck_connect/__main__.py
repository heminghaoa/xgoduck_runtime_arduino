"""Start duck-connect: python -m duck_connect [options]. Installed as a systemd service by
tools/install-connect.sh; run it by hand with --help to see the options."""
import argparse
import asyncio
import logging

from .duck_app import DuckApp
from .identity import Identity
from .wifi import Wifi


def main():
    p = argparse.ArgumentParser(prog='duck-connect')
    p.add_argument('--identity', default='/home/arduino/ArduinoApps/xgoduck_runtime_arduino/data/identity.json',
                   help="the XGO Duck app's identity file (ID and pairing key)")
    p.add_argument('--app', default='http://127.0.0.1:9527', help='XGO Duck app base URL')
    p.add_argument('--token-file', default='/var/lib/duck-connect/app-token',
                   help='where to keep the token for the app when it requires pairing')
    p.add_argument('--adapter', default='hci0')
    p.add_argument('--name', default='XGO Duck', help='Bluetooth advertising name')
    p.add_argument('--no-bonjour', action='store_true', help='do not write the avahi service file')
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    from .ble import Server  # needs dbus-fast, installed on the board
    identity = Identity(args.identity)
    if identity.error:
        logging.warning('%s', identity.error)
    server = Server(identity, Wifi(), DuckApp(identity, args.app, args.token_file), args.name,
                    publish_bonjour=not args.no_bonjour)
    asyncio.run(server.run(args.adapter))


if __name__ == '__main__':
    main()
