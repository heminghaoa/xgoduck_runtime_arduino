"""Socket.IO channel for the phone app, on the WebUI brick's /socket.io.

The duck pushes "status" to every client STATUS_HZ times a second. Clients send
(each reply arrives as "<name>_response"; command replies only on failure):
  hello   {token?}                  -> {duck_id, require_pairing, paired, status_hz}
  command {twist?, head?, mouth?}    -> {ok: false, error} on failure
  mode    {mode}                    -> {ok, mode} or {ok: false, error}
  action  {name: "pick"|"roulade"}  -> {ok, ...} or {ok: false, error}
Status carries the measured servo angles (degrees, in "motors" order) and the filtered
gravity vector, so the app can pose its 3D duck like the web page's 3D view.
When pairing is required, control needs the token sent in hello. It is checked
again on every message, so a removed client loses control at once.
"""
import threading

STATUS_HZ = 10
REMOTE_MODES = ('shadow', 'off', 'hold', 'policy')
STATUS_KEYS = ('mode', 'enabled', 'control_ready', 'full_robot_ready', 'feedback_hz', 'inference_hz',
               'imu_ok', 'servo_ids', 'missing_joint_ids', 'battery', 'active_model', 'last_error',
               'settings_error', 'command', 'head', 'mouth', 'motors')

def compact_status(s):
    out = {k: s.get(k) for k in STATUS_KEYS}
    out['recovery'] = {k: s['recovery'].get(k) for k in ('active', 'phase', 'angle_deg')}
    out.update(pick_active=s['pick']['active'], roulade_active=s['roulade']['active'],
               roller=s['roller']['enabled'])
    # Rounded: ten times a second to every phone, a tenth of a degree is plenty to draw with.
    angles, gravity, age = s.get('angles'), s.get('gravity'), s.get('feedback_age_ms')
    out.update(angles=[round(a, 1) for a in angles] if angles else None,
               gravity=[round(g, 3) for g in gravity] if gravity else None,
               feedback_age_ms=round(age) if age is not None else None)
    return out

class Realtime:
    def __init__(self, ui, controller, access, identity):
        self.ui, self.controller, self.access, self.identity = ui, controller, access, identity
        self.lock = threading.Lock()
        self.tokens = {}       # sid -> token sent in hello ('' if none)
        self.drivers = set()   # sids that have sent motion commands
        self.stop_event = threading.Event()
        ui.on_connect(self._connect)
        ui.on_disconnect(self._disconnect)
        ui.on_message('hello', self._hello)
        ui.on_message('command', self._command)
        ui.on_message('mode', self._mode)
        ui.on_message('action', self._action)

    def _connect(self, sid):
        with self.lock:
            self.tokens[sid] = ''

    def _disconnect(self, sid):
        with self.lock:
            self.tokens.pop(sid, None)
            drove = sid in self.drivers
            self.drivers.discard(sid)
        if drove:
            # Stop travel now instead of waiting for the 1 s command timeout.
            try:
                self.controller.command(twist=[0.0]*3)
            except ValueError:
                pass

    def _hello(self, sid, data):
        token = data.get('token', '') if isinstance(data, dict) else ''
        token = token if isinstance(token, str) else ''
        with self.lock:
            self.tokens[sid] = token
        return dict(duck_id=self.identity.id, require_pairing=self.access.require_pairing,
                    paired=self.access.check(token) is not None, status_hz=STATUS_HZ)

    def _guarded(self, sid, run):
        with self.lock:
            token = self.tokens.get(sid, '')
        if self.access.require_pairing and self.access.check(token) is None:
            return dict(ok=False, error='pairing required')
        try:
            return run()
        except (TypeError, ValueError) as exc:
            return dict(ok=False, error=str(exc))

    def _command(self, sid, data):
        def run():
            if not isinstance(data, dict):
                raise ValueError('command must be an object')
            self.controller.command(**data)
            with self.lock:
                self.drivers.add(sid)
        return self._guarded(sid, run)

    def _mode(self, sid, data):
        def run():
            mode = data.get('mode') if isinstance(data, dict) else None
            if mode not in REMOTE_MODES:
                raise ValueError('mode must be one of ' + ', '.join(REMOTE_MODES))
            return dict(ok=True, **self.controller.set_mode(mode))
        return self._guarded(sid, run)

    def _action(self, sid, data):
        actions = {'pick': self.controller.start_pick, 'roulade': self.controller.start_roulade}
        def run():
            name = data.get('name') if isinstance(data, dict) else None
            if name not in actions:
                raise ValueError('action must be pick or roulade')
            return dict(actions[name](), ok=True)
        return self._guarded(sid, run)

    def start(self):
        threading.Thread(target=self._push, name='realtime10', daemon=True).start()

    def stop(self):
        self.stop_event.set()

    def _push(self):
        while not self.stop_event.wait(1 / STATUS_HZ):
            with self.lock:
                if not self.tokens:
                    continue
            try:
                status = compact_status(self.controller.status())
                status['require_pairing'] = self.access.require_pairing
                self.ui.send_message('status', status)
            except Exception:
                # A failed push must not end the loop; the next tick tries again.
                pass
