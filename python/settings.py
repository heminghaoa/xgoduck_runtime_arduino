"""Controller settings that survive restarts, kept as JSON in the app's data folder."""
import json
import math
import os
from pathlib import Path

# App Lab bind-mounts the app folder into the container; its data/ folder persists.
DATA_DIR = Path(os.environ.get('XGODUCK_DATA_DIR') or Path(__file__).resolve().parent.parent / 'data')
SETTINGS_FILE = DATA_DIR / 'settings.json'
VERSION = 1
NAME_MAX = 32
RANGES = {
    'walk': {'action_scale': (0, 2), 'action_alpha': (0, 1), 'action_alpha_head': (0, 1)},
    'roller': {'action_scale': (0, 2), 'action_alpha': (0, 1), 'action_alpha_head': (0, 1)},
    'imu': {'gyro_alpha': (0, 0.95), 'gravity_tau_s': (0.01, 2)},
}

def merge(current, update):
    """Return a copy of current with update applied, after checking every field."""
    if not isinstance(update, dict):
        raise ValueError('settings must be an object')
    unknown = set(update) - {'name', *RANGES}
    if unknown:
        raise ValueError('unknown setting: ' + ', '.join(sorted(unknown)))
    result = {k: dict(v) if isinstance(v, dict) else v for k, v in current.items()}
    if 'name' in update:
        name = update['name']
        if not isinstance(name, str) or not name.isprintable() or not 1 <= len(name.strip()) <= NAME_MAX:
            raise ValueError(f'name must be 1 to {NAME_MAX} printable characters')
        result['name'] = name.strip()
    for group, fields in RANGES.items():
        if group not in update:
            continue
        values = update[group]
        if not isinstance(values, dict) or set(values) - set(fields):
            raise ValueError(f'unknown {group} setting')
        for key, value in values.items():
            lo, hi = fields[key]
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or not lo <= value <= hi):
                raise ValueError(f'{group}.{key} must be within [{lo}, {hi}]')
            result[group][key] = float(value)
    return result

def load():
    """Return (saved settings or None, error message)."""
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None, ''
    except (OSError, ValueError) as exc:
        return None, f'settings not loaded: {exc}'
    if not isinstance(data, dict) or data.pop('version', None) != VERSION:
        return None, 'settings not loaded: unknown file version'
    return data, ''

def save(values):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps({'version': VERSION, **values}, ensure_ascii=False, indent=2),
                   encoding='utf-8')
    os.replace(tmp, SETTINGS_FILE)
