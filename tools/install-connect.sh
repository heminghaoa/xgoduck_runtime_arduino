#!/bin/bash
set -euo pipefail
# Install duck-connect (connect/) as a systemd service. Run with sudo on Uno Q from this app folder:
#   sudo bash tools/install-connect.sh            also sets this app to start at boot
#   sudo bash tools/install-connect.sh --no-autostart
# Running it again updates the code and restarts the service.
autostart=1
[ "${1:-}" = "--no-autostart" ] && autostart=0
[ "$(id -u)" -eq 0 ] || { echo "Run with sudo." >&2; exit 1; }
app_dir=$(cd "$(dirname "$0")/.." && pwd)
prefix=/opt/duck-connect
for tool in python3 nmcli bluetoothctl; do
  command -v "$tool" >/dev/null || { echo "Missing $tool; duck-connect needs it." >&2; exit 1; }
done
python3 -c 'import ensurepip, venv' 2>/dev/null || apt-get install -y python3-venv

mkdir -p "$prefix" /var/lib/duck-connect
chmod 700 /var/lib/duck-connect
[ -x "$prefix/venv/bin/python" ] || python3 -m venv "$prefix/venv"
"$prefix/venv/bin/pip" install --quiet --upgrade pip
"$prefix/venv/bin/pip" install --quiet -r "$app_dir/connect/requirements.txt"
rm -rf "$prefix/duck_connect"
cp -r "$app_dir/connect/duck_connect" "$prefix/"
sed "s|@IDENTITY@|$app_dir/data/identity.json|" "$app_dir/connect/duck-connect.service" \
  > /etc/systemd/system/duck-connect.service
systemctl daemon-reload
systemctl enable duck-connect
systemctl restart duck-connect

if [ "$autostart" -eq 1 ] && [ -n "${SUDO_USER:-}" ]; then
  # duck-connect forwards to the app, so the app should be running after every boot too.
  sudo -u "$SUDO_USER" arduino-app-cli properties set default "user:$(basename "$app_dir")" \
    || echo "Could not set the app to start at boot; set it in App Lab." >&2
fi
sleep 2
systemctl --no-pager --lines=8 status duck-connect || true
