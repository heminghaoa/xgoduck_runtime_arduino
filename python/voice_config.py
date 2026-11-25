"""Persistent product settings; credentials live in the separate private state directory."""
import json
import os
import threading
import tempfile
from pathlib import Path

from app_paths import DATA

CONFIG_PATH = DATA / 'voice_config.json'
WAKE_MODELS = Path(__file__).with_name('models')
# DRADUCK's Japanese wake words, trained like xiaoya.onnx (livekit-wakeword, same frontends), as
# (phrase, model, threshold); provenance/draduck-*-wakeword.json has how each was made and tested.
# - nee (default): 「ねえ、ドラダック」 with the nee4 model since 2026-11-25 (owner: 「改用 nee4」). Through the lab
#   duck's microphone the owner's eleven real calls scored 0.00-0.29 on the first model (none heard; a tester's
#   voice the day before 0.14-0.51) and woke nee4 nine times, nee3 ten; in 35 minutes of that room the first
#   model woke twice on Mandarin talk, nee4 and nee3 never (all with the guards below). nee4 was also trained
#   on Mandarin, English and Korean voices and on 「ねえ、…」 near misses; in clean synthetic tests it still
#   wakes on 8% of such near-miss clips (the first model 0%, nee3 14%), see its provenance.
# - nee1: the first model (the default until 2026-11-25); also answers 「ドラダック」 alone. Threshold .30.
# - strict: answers only 「ねえ、ドラダック」, at the cost of more misses and false wakes.
# - short: trained on 「ドラダック」.
# - nee3: nee4 without the near-miss negatives. nee4: the same model as nee, by its own name.
DRADUCK_WAKE = {
    'nee': ('ねえ、ドラダック', 'draduck_nee4.onnx', .35),
    'nee1': ('ねえ、ドラダック', 'draduck_nee.onnx', .30),
    'strict': ('ねえ、ドラダック', 'draduck_nee_strict.onnx', .50),
    'short': ('ドラダック', 'draduck_short.onnx', .70),
    'nee3': ('ねえ、ドラダック', 'draduck_nee3.onnx', .35),
    'nee4': ('ねえ、ドラダック', 'draduck_nee4.onnx', .35),
}
# False wakes (owner 2026-11-25: the lab duck woke three times in half an hour with nobody speaking, twice
# standing up; the recorded audio was its microphone's own noise at +12 dB, within 4 dB of the room's noise in
# every band, and scored up to 0.73 on nee3 and 0.63 on nee). Every DRADUCK model therefore also needs, in
# wakeword_manager.py: the score over the threshold in two windows in a row (a spoken wake word holds it for
# several; half the noise spikes were one window), and speech: at least 3 of the last two seconds' 80 ms frames
# 8 dB over the noise floor between 300 and 3000 Hz (SpeechGate). Replayed over 12.6 minutes of that room's
# microphone: nee 1 false wake and nee3 3 before, none after (those windows had 0 to 2 such frames; the owner's
# voice at about a metre had 15, peaking 20 dB over the floor). Synthetic wake phrases mixed into that noise:
# the gate costs nothing from 10 dB over the noise up, 1 of 52 at 6 dB, 4 of 52 at 3 dB; 10 dB and 4 frames
# cost 11 of 52 at 6 dB.
DRADUCK_CONFIRM_WINDOWS = 2
DRADUCK_SPEECH = (8, 3)         # (dB over the noise floor, frames)
# The choice lives in its own file, not in voice_config.json: Luwu's app drops that whole file when
# it meets a field it does not know, which would lose the cloud settings after a downgrade.
DRADUCK_SETTINGS = DATA / 'draduck.json'


def draduck_wake_choice(path=None):
    try:
        choice = json.loads(Path(path or DRADUCK_SETTINGS).read_text()).get('wake')
    except (OSError, ValueError, AttributeError):
        choice = None
    return choice if choice in DRADUCK_WAKE else 'nee'


DEFAULTS = dict(enabled=True, language='cn', enable_wakeword=True, enable_aec=False,
                input_device=None, output_device=None,
                voice_motion_enabled=False,  # Legacy setting kept for downgrade compatibility.
                volume=60, enable_camera=True, ota_url='', camera_device=None, remote_motion_enabled=False,
                cloud_region=None, input_auto_gain=None, input_gain_db=0, output_gain_db=0,
                tts_mouth_enabled=True, input_channel_mode='auto', input_sample_rate=None,
                aec_output_headroom_db=0)


def wake_profile(config):
    """Choose the phrase and detector settings for the same voice session."""
    if config.get('ota_url'):
        # DRADUCK: a custom (our own Japanese) voice server answers to 「ねえ、ドラダック」, or to
        # 「ドラダック」 when data/draduck.json says {"wake": "short"}; the other model stands in
        # if the chosen one is not installed.
        choice = draduck_wake_choice()
        for key in (choice, *(k for k in DRADUCK_WAKE if k != choice)):
            phrase, model, threshold = DRADUCK_WAKE[key]
            if (WAKE_MODELS / model).is_file():
                return phrase, dict(shared_capture=True, model_path=str(WAKE_MODELS / model),
                                    threshold=threshold, input_scale=1., stride_duration=.08, cooldown_sec=2.,
                                    confirm_windows=DRADUCK_CONFIRM_WINDOWS, speech_rise_db=DRADUCK_SPEECH[0],
                                    speech_frames=DRADUCK_SPEECH[1])
    region = None if config.get('ota_url') else config.get('cloud_region')
    if region == 'global':
        phrase, model = 'Hey Ducky', 'hey_ducky.onnx'
    elif region == 'cn' or config.get('language', 'cn') == 'cn':
        phrase, model = '小鸭小鸭', 'xiaoya.onnx'
    else:
        # Custom servers keep the legacy language-based English profile.
        return 'Hi Luka', dict(shared_capture=True)
    profile = dict(shared_capture=True, model_path=str(WAKE_MODELS / model),
                   threshold=.50, input_scale=1., stride_duration=.08, cooldown_sec=2.)
    if model == 'xiaoya.onnx':
        profile['playback_threshold'] = .30
    return phrase, profile


class VoiceConfig:
    def __init__(self, path=CONFIG_PATH):
        self.path = Path(path)
        self.lock = threading.RLock()

    def get(self):
        with self.lock:
            config = dict(DEFAULTS)
            try:
                config.update(self.validate(json.loads(self.path.read_text())))
            except (OSError, ValueError, TypeError):
                pass
            return config

    @staticmethod
    def validate(changes):
        if not isinstance(changes, dict) or any(k not in DEFAULTS for k in changes):
            raise ValueError('unknown voice configuration field')
        for key, value in changes.items():
            if key == 'aec_output_headroom_db' and (isinstance(value, bool)
                    or not isinstance(value, (int, float)) or not 0 <= value <= 18):
                raise ValueError('aec_output_headroom_db must be 0–18 dB')
            if key == 'input_channel_mode' and value not in ('auto', 'left', 'right', 'average'):
                raise ValueError('input_channel_mode must be auto/left/right/average')
            if key == 'input_sample_rate' and value is not None and (
                    type(value) is not int or value not in (16000, 48000)):
                raise ValueError('input_sample_rate must be null, 16000 or 48000')
            if isinstance(DEFAULTS[key], bool) and not isinstance(value, bool):
                raise ValueError(key + ' must be boolean')
            if key == 'language' and value not in ('cn', 'en'):
                raise ValueError('language must be cn/en')
            if key == 'cloud_region' and value not in (None, 'cn', 'global'):
                raise ValueError('cloud_region must be cn/global (or null before setup)')
            if key == 'input_auto_gain' and value is not None and not isinstance(value, bool):
                raise ValueError('input_auto_gain must be boolean or null')
            if key in ('input_gain_db', 'output_gain_db') and (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not 0 <= value <= 12):
                raise ValueError(key + ' must be 0–12 dB')
            if key in ('input_device', 'output_device') and value is not None:
                if not isinstance(value, str) or not 1 <= len(value) <= 200:
                    raise ValueError('audio device must be a USB key, ALSA card name, or null')
            if key == 'volume' and (isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100):
                raise ValueError('volume must be 0–100')
            if key == 'ota_url' and (not isinstance(value, str) or (value and not value.startswith('https://'))):
                raise ValueError('ota_url must be HTTPS or empty')
            if key == 'camera_device' and value is not None and (
                    not isinstance(value, str) or not value.startswith('/dev/v4l/by-id/')):
                raise ValueError('camera_device must be a /dev/v4l/by-id/ path or null')
        return changes

    def region_status(self):
        """Read only public region metadata; never expose an advanced OTA URL."""
        with self.lock:
            config = dict(DEFAULTS)
            try:
                config.update(self.validate(json.loads(self.path.read_text())))
            except FileNotFoundError:
                pass
            except (OSError, ValueError, TypeError) as exc:
                raise ValueError('Saved voice configuration is invalid; repair it before switching servers.') from exc
            configured = bool(config['ota_url'] or config['cloud_region'])
            return dict(cloud_region=config['cloud_region'], custom_endpoint=bool(config['ota_url']),
                        configured=configured, wake_phrase=wake_profile(config)[0] if configured else None)

    def select_region(self, region, *, only_if_unconfigured=False):
        """Save a manual choice or fill in the region after automatic discovery."""
        if region not in ('cn', 'global'):
            raise ValueError('Select cn or global.')
        with self.lock:
            before = self.region_status()
            if only_if_unconfigured and before['configured']:
                return dict(before, changed=False, reconnecting=False)
            changed = before['cloud_region'] != region or before['custom_endpoint']
            if changed:
                self.update(dict(cloud_region=region, ota_url=''))
            return dict(self.region_status(), changed=changed, reconnecting=changed)

    def update(self, changes):
        self.validate(changes)
        with self.lock:
            config = self.get()
            config.update(changes)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', dir=self.path.parent, delete=False) as f:
                tmp = Path(f.name)
                f.write(json.dumps(config, indent=2) + '\n')
            try:
                os.chmod(tmp, 0o600)
                tmp.replace(self.path)
            finally:
                tmp.unlink(missing_ok=True)
            return config
