"""Bonjour: an avahi service file announcing _xgoduck._tcp with the duck's ID.

avahi-daemon watches /etc/avahi/services and picks up changes on its own.
"""
from pathlib import Path
from xml.sax.saxutils import escape

SERVICE_FILE = Path('/etc/avahi/services/xgoduck.service')


def service_xml(duck_id, port=9527):
    return f"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>XGO Duck {escape(duck_id)}</name>
  <service>
    <type>_xgoduck._tcp</type>
    <port>{int(port)}</port>
    <txt-record>id={escape(duck_id)}</txt-record>
    <txt-record>v=1</txt-record>
  </service>
</service-group>
"""


def publish(duck_id, port=9527, path=SERVICE_FILE):
    """Write the service file if it changed. Returns True when it was (re)written."""
    content = service_xml(duck_id, port)
    try:
        if path.read_text() == content:
            return False
    except OSError:
        pass
    path.write_text(content)
    return True
