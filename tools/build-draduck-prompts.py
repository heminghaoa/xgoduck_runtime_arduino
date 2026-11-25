#!/usr/bin/env python3
"""DRADUCK: the duck's fixed spoken prompts in Japanese (the maker ships Chinese and English only).

Owner, 2026-11-25, on hearing the low-battery warning on the lab duck: 「怎么在说英语…不应该说日语吗」.

    OPENAI_API_KEY=... python3 tools/build-draduck-prompts.py [--check]

Writes, in the voice the duck talks with on our voice server (OpenAI, voice cedar):
- python/assets/low-battery-ja.wav   24 kHz mono PCM16, like the maker's two (played by voice_media.py, 9 s limit);
- python/assets/bind-device-ja.wav   16 kHz mono PCM16 (binding_prompt.py, no address known);
- python/assets/bind-ip-parts-ja.zip ja/{prefix,suffix,dot,0..9}.pcm, 16 kHz mono PCM16 (binding_prompt.py speaks the
  duck's address digit by digit).
--check sends each clip back for transcription and prints what was heard. Texts and hashes go in
provenance/draduck-prompts.json.
"""
import argparse
import hashlib
import io
import json
import os
import struct
import sys
import urllib.request
import wave
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'python' / 'assets'
MODEL, VOICE = 'gpt-4o-mini-tts', 'cedar'
STYLE = '日本語。小さなアヒルのロボットが、明るく、はっきり、ふつうの速さで話す。間を長く取らない。'
LOW_BATTERY = 'バッテリーが少なくなりました。電源を切って、充電してください。いまから力を抜きます。'
BIND_DEVICE = 'ブラウザでダックのコックピットを開いてください。'
PREFIX, SUFFIX = 'ブラウザで、', 'を開いてください。'
DIGITS = dict(zip('0123456789', ('ゼロ', 'いち', 'に', 'さん', 'よん', 'ご', 'ろく', 'なな', 'はち', 'きゅう')))
DOT = 'てん'
SILENCE = 200          # |sample| under this is silence when trimming


def speak(key, text):
    """24 kHz mono PCM16 of `text`."""
    body = json.dumps({'model': MODEL, 'voice': VOICE, 'input': text, 'instructions': STYLE,
                       'response_format': 'pcm'}).encode()
    request = urllib.request.Request('https://api.openai.com/v1/audio/speech', body,
                                     {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=60) as r:
        return r.read()


def trim(pcm, lead_ms=20, tail_ms=60, rate=24000):
    samples = struct.unpack(f'<{len(pcm) // 2}h', pcm[:len(pcm) // 2 * 2])
    loud = [i for i, s in enumerate(samples) if abs(s) > SILENCE]
    if not loud:
        return pcm
    start = max(0, loud[0] - rate * lead_ms // 1000)
    end = min(len(samples), loud[-1] + rate * tail_ms // 1000)
    return struct.pack(f'<{end - start}h', *samples[start:end])


def to_16k(pcm):
    """24 kHz to 16 kHz (3:2) by linear interpolation: speech prompts, no library on hand."""
    s = struct.unpack(f'<{len(pcm) // 2}h', pcm)
    out = []
    for i in range(len(s) * 2 // 3):
        x = i * 1.5
        a = int(x)
        b = min(a + 1, len(s) - 1)
        out.append(int(s[a] + (s[b] - s[a]) * (x - a)))
    return struct.pack(f'<{len(out)}h', *out)


def wav_bytes(pcm, rate):
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as w:
        w.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        w.writeframes(pcm)
    return buffer.getvalue()


def heard(key, pcm, rate):
    boundary = 'draduckprompt'
    parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
             for k, v in (('model', 'gpt-4o-transcribe'), ('language', 'ja'))]
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="clip.wav"\r\n'
                 'Content-Type: audio/wav\r\n\r\n'.encode() + wav_bytes(pcm, rate) + b'\r\n')
    request = urllib.request.Request('https://api.openai.com/v1/audio/transcriptions',
                                     b''.join(parts) + f'--{boundary}--\r\n'.encode(),
                                     {'Authorization': f'Bearer {key}',
                                      'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(request, timeout=60) as r:
        return json.loads(r.read()).get('text', '')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        sys.exit('Set OPENAI_API_KEY.')
    record = {'date': '2026-11-25', 'source': 'OpenAI speech synthesis', 'model': MODEL, 'voice': VOICE,
              'style': STYLE, 'generator': 'tools/build-draduck-prompts.py'}

    low = trim(speak(key, LOW_BATTERY), 50, 150)
    seconds = len(low) / 48000
    if seconds > 8:
        sys.exit(f'low battery: {seconds:.1f} s, over the 9 s playback limit')
    (ASSETS / 'low-battery-ja.wav').write_bytes(wav_bytes(low, 24000))
    record['low_battery'] = {'path': 'python/assets/low-battery-ja.wav', 'text': LOW_BATTERY,
                             'format': '24 kHz mono PCM16', 'seconds': round(seconds, 2)}

    bind = to_16k(trim(speak(key, BIND_DEVICE), 50, 150))
    (ASSETS / 'bind-device-ja.wav').write_bytes(wav_bytes(bind, 16000))
    record['bind_device'] = {'path': 'python/assets/bind-device-ja.wav', 'text': BIND_DEVICE,
                             'format': '16 kHz mono PCM16'}

    texts = {'prefix': PREFIX, 'suffix': SUFFIX, 'dot': DOT, **DIGITS}
    clips = {name: to_16k(trim(speak(key, text))) for name, text in texts.items()}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(clips):
            z.writestr(zipfile.ZipInfo(f'ja/{name}.pcm', (1980, 1, 1, 0, 0, 0)), clips[name])
    (ASSETS / 'bind-ip-parts-ja.zip').write_bytes(buffer.getvalue())
    record['address_parts'] = {'path': 'python/assets/bind-ip-parts-ja.zip', 'format': '16 kHz mono PCM16',
                               'text': f'{PREFIX}［IP アドレス］{SUFFIX}', 'parts': texts}

    for entry in record.values():
        if isinstance(entry, dict):
            entry['sha256'] = hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest()
    (ROOT / 'provenance' / 'draduck-prompts.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')

    print(f'low battery {seconds:.1f} s; bind {len(bind) / 32000:.1f} s; parts '
          + ' '.join(f'{n}={len(c) / 32000:.2f}' for n, c in sorted(clips.items())))
    if args.check:
        print('low battery:', heard(key, low, 24000))
        print('bind:', heard(key, bind, 16000))
        address = '192.168.1.45'
        gap, pause = bytes(2 * int(16000 * .045)), bytes(2 * int(16000 * .18))
        spoken = gap.join(clips['dot' if c == '.' else c] for c in address)
        print(f'address {address}:', heard(key, pause.join((clips['prefix'], spoken, clips['suffix'])), 16000))


if __name__ == '__main__':
    main()
