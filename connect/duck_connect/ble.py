"""BLE peripheral on BlueZ over D-Bus: one GATT service with three characteristics.

  info (read)                 JSON {"proto", "duck_id", "name"}, no pairing needed
  rx   (write, write-no-resp) phone -> duck, framed messages (framing.py)
  tx   (notify)               duck -> phone, framed messages

BlueZ passes each write's sender ("device") and the link MTU, so every connected
phone gets its own Session, dropped when BlueZ reports the device disconnected.
Notifications go to every subscribed phone; the protocol expects one at a time.
"""
import asyncio
import json
import logging
from dbus_fast import BusType, Message, MessageType, Variant
from dbus_fast.aio import MessageBus
from dbus_fast.constants import PropertyAccess
from dbus_fast.service import ServiceInterface, dbus_property, method

from . import PROTOCOL_VERSION, avahi, framing
from .session import Session

log = logging.getLogger('duck-connect')

SERVICE_UUID = 'b5f1a6e0-6c1d-4f5e-9a37-2d0c8e4b7a10'
INFO_UUID = 'b5f1a6e1-6c1d-4f5e-9a37-2d0c8e4b7a10'
RX_UUID = 'b5f1a6e2-6c1d-4f5e-9a37-2d0c8e4b7a10'
TX_UUID = 'b5f1a6e3-6c1d-4f5e-9a37-2d0c8e4b7a10'
APP_PATH = '/org/xgoduck/connect'
ADV_PATH = '/org/xgoduck/connect/adv0'
STATUS_INTERVAL_S = 3.0


class GattService(ServiceInterface):
    def __init__(self, uuid):
        super().__init__('org.bluez.GattService1')
        self._uuid = uuid

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> 's':
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> 'b':
        return True


class Characteristic(ServiceInterface):
    def __init__(self, uuid, service_path, flags, on_read=None, on_write=None):
        super().__init__('org.bluez.GattCharacteristic1')
        self._uuid, self._service, self._flags = uuid, service_path, flags
        self._value = b''
        self.on_read, self.on_write = on_read, on_write
        self.notifying = False

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> 's':
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> 'o':
        return self._service

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> 'as':
        return self._flags

    @dbus_property(access=PropertyAccess.READ)
    def Value(self) -> 'ay':
        return self._value

    @method()
    def ReadValue(self, options: 'a{sv}') -> 'ay':
        data = self.on_read() if self.on_read else self._value
        offset = options.get('offset')
        return data[offset.value:] if offset else data

    @method()
    def WriteValue(self, value: 'ay', options: 'a{sv}'):
        if self.on_write:
            device, mtu = options.get('device'), options.get('mtu')
            self.on_write(device.value if device else '', bytes(value), mtu.value if mtu else None)

    @method()
    def StartNotify(self):
        self.notifying = True

    @method()
    def StopNotify(self):
        self.notifying = False

    def notify(self, data):
        self._value = bytes(data)
        if self.notifying:
            self.emit_properties_changed({'Value': self._value})


class Advertisement(ServiceInterface):
    def __init__(self, name):
        super().__init__('org.bluez.LEAdvertisement1')
        self._name = name

    @dbus_property(access=PropertyAccess.READ)
    def Type(self) -> 's':
        return 'peripheral'

    @dbus_property(access=PropertyAccess.READ)
    def ServiceUUIDs(self) -> 'as':
        return [SERVICE_UUID]

    @dbus_property(access=PropertyAccess.READ)
    def LocalName(self) -> 's':
        return self._name

    @method()
    def Release(self):
        log.info('advertisement released by BlueZ')


class Server:
    def __init__(self, identity, wifi, app, name='XGO Duck', publish_bonjour=True):
        self.identity, self.wifi, self.app, self.name = identity, wifi, app, name
        self.publish_bonjour = publish_bonjour
        self.sessions = {}   # device path -> (Session, Reassembler)
        self.mtu = {}        # device path -> ATT MTU reported by BlueZ
        self.writes = None   # asyncio.Queue, made inside the running loop
        self.tx = None

    # -- characteristic callbacks (D-Bus thread == event loop thread) --
    def read_info(self):
        self.identity.reload()
        return json.dumps(dict(proto=PROTOCOL_VERSION, duck_id=self.identity.id, name=self.name),
                          separators=(',', ':')).encode()

    def on_write(self, device, data, mtu):
        if mtu:
            self.mtu[device] = mtu
        self.writes.put_nowait((device, data))

    # -- sessions --
    def _session(self, device):
        if device not in self.sessions:
            log.info('phone connected: %s', device)
            send = lambda message, device=device: self.send(device, message)
            self.sessions[device] = (Session(self.identity, self.wifi, self.app, send), framing.Reassembler())
        return self.sessions[device]

    async def device_gone(self, device):
        entry = self.sessions.pop(device, None)
        self.mtu.pop(device, None)
        if entry:
            log.info('phone disconnected: %s', device)
            await entry[0].close()

    async def send(self, device, message):
        session = self.sessions.get(device, (None,))[0]
        size = (self.mtu[device] - 3) if device in self.mtu else (session.chunk if session and session.chunk else None)
        for chunk in framing.chunks(framing.encode(message), size or framing.DEFAULT_CHUNK):
            self.tx.notify(chunk)
            await asyncio.sleep(0)

    async def _handle_writes(self):
        while True:
            device, data = await self.writes.get()
            session, reassembler = self._session(device)
            messages, error = reassembler.feed(data)
            for message in messages:
                await session.handle(message)
            if error:
                await self.send(device, {'ok': False, 'error': error})

    async def _status_loop(self):
        published = None
        while True:
            await asyncio.sleep(STATUS_INTERVAL_S)
            self.identity.reload()
            if self.publish_bonjour and self.identity.id and self.identity.id != published:
                try:
                    avahi.publish(self.identity.id)
                    published = self.identity.id
                except OSError as exc:
                    log.warning('bonjour not published: %s', exc)
            greeted = [d for d, (s, _) in self.sessions.items() if s.greeted]
            if not greeted:
                continue
            try:
                status = await asyncio.to_thread(self.app.status)
            except (ValueError, OSError) as exc:
                status = dict(error=str(exc))
            for device in greeted:
                await self.send(device, {'ev': 'status', **status})

    # -- BlueZ plumbing --
    async def _watch_disconnects(self, bus):
        rule = ("type='signal',sender='org.bluez',interface='org.freedesktop.DBus.Properties',"
                "member='PropertiesChanged',arg0='org.bluez.Device1'")
        await bus.call(Message(destination='org.freedesktop.DBus', path='/org/freedesktop/DBus',
                               interface='org.freedesktop.DBus', member='AddMatch', signature='s', body=[rule]))
        loop = asyncio.get_running_loop()

        def handler(msg):
            if (msg.message_type == MessageType.SIGNAL and msg.member == 'PropertiesChanged'
                    and msg.body and msg.body[0] == 'org.bluez.Device1'):
                connected = msg.body[1].get('Connected')
                if connected is not None and not connected.value:
                    loop.create_task(self.device_gone(msg.path))
        bus.add_message_handler(handler)

    async def run(self, adapter='hci0'):
        self.writes = asyncio.Queue()
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        service_path = APP_PATH + '/service0'
        self.tx = Characteristic(TX_UUID, service_path, ['notify'])
        bus.export(service_path, GattService(SERVICE_UUID))
        bus.export(service_path + '/char0', Characteristic(INFO_UUID, service_path, ['read'], on_read=self.read_info))
        bus.export(service_path + '/char1', Characteristic(RX_UUID, service_path, ['write', 'write-without-response'],
                                                           on_write=self.on_write))
        bus.export(service_path + '/char2', self.tx)
        bus.export(ADV_PATH, Advertisement(self.name))

        adapter_path = '/org/bluez/' + adapter
        proxy = bus.get_proxy_object('org.bluez', adapter_path, await bus.introspect('org.bluez', adapter_path))
        await proxy.get_interface('org.freedesktop.DBus.Properties').call_set(
            'org.bluez.Adapter1', 'Powered', Variant('b', True))
        await proxy.get_interface('org.bluez.GattManager1').call_register_application(APP_PATH, {})
        await proxy.get_interface('org.bluez.LEAdvertisingManager1').call_register_advertisement(ADV_PATH, {})
        await self._watch_disconnects(bus)
        log.info('advertising as "%s" (duck %s) on %s', self.name, self.identity.id, adapter)
        await asyncio.gather(self._handle_writes(), self._status_loop(), bus.wait_for_disconnect())
