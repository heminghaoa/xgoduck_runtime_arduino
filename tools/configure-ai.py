#!/usr/bin/env python3
"""Choose a cloud locally on the UNO Q; phone provisioning never changes it."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from app_paths import DATA
from voice_config import DRADUCK_WAKE, VoiceConfig, draduck_wake_choice


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument('--region', choices=('cn', 'global'), help='cn: WeChat Mini Program; global: international App')
    choice.add_argument('--show', action='store_true', help='Show the selected region without writing')
    choice.add_argument('--ota-url', help='Use a custom HTTPS voice server (DRADUCK) instead of a region')
    parser.add_argument('--language', choices=('cn', 'en'), help='Wake-word / conversation language, independent of cloud')
    parser.add_argument('--aec-output-headroom-db', type=float,
                        help='0–18 dB quieter playback during full-duplex AEC only; default 0')
    parser.add_argument('--draduck-wake', choices=sorted(DRADUCK_WAKE),
                        help='Wake word with a custom (DRADUCK) server: nee = ねえ、ドラダック (default; the nee4 model); '
                             'nee1 = the first model; strict = only ねえ、ドラダック; short = ドラダック')
    parser.add_argument('--data-dir', type=Path, default=DATA, help='Persistent App data directory')
    args = parser.parse_args()
    if (not args.region and not args.show and not args.ota_url and not args.draduck_wake
            and args.aec_output_headroom_db is None):
        parser.error('choose --region, --ota-url, --draduck-wake, --show, or --aec-output-headroom-db')
    if args.ota_url:
        try:
            VoiceConfig.validate({'ota_url': args.ota_url})
        except ValueError as exc:
            parser.error(str(exc))
    if args.language and not args.region:
        parser.error('--language requires --region')
    if args.show and args.aec_output_headroom_db is not None:
        parser.error('--show cannot change audio settings')
    if args.aec_output_headroom_db is not None:
        try:
            VoiceConfig.validate({'aec_output_headroom_db': args.aec_output_headroom_db})
        except ValueError as exc:
            parser.error(str(exc))
    config = VoiceConfig(args.data_dir / 'voice_config.json')
    # Refuse to replace malformed settings and silently lose the user's choices.
    try:
        if config.path.exists():
            VoiceConfig.validate(json.loads(config.path.read_text()))
        changes = {}
        if args.region:
            changes.update(cloud_region=args.region, ota_url='')
            if args.language:
                changes['language'] = args.language
        if args.ota_url:
            changes['ota_url'] = args.ota_url
        if args.aec_output_headroom_db is not None:
            changes['aec_output_headroom_db'] = args.aec_output_headroom_db
        if changes:
            config.update(changes)
        settings = config.get()
        draduck = args.data_dir / 'draduck.json'
        if args.draduck_wake:
            draduck.write_text(json.dumps({'wake': args.draduck_wake}) + '\n')
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f'Cannot use {config.path}: {type(exc).__name__}. Fix the settings file first.\n')
    print('Cloud:', 'custom HTTPS endpoint' if settings['ota_url'] else settings['cloud_region'] or 'not selected')
    print('Language:', settings['language'])
    if settings['ota_url']:
        print('DRADUCK wake word:', DRADUCK_WAKE[draduck_wake_choice(draduck)][0])
    print('AEC output headroom:', settings['aec_output_headroom_db'], 'dB')
    if args.region or args.ota_url or args.draduck_wake:
        print('Saved:', config.path)
        print('Restart the App after changing regions; bind using the matching client. Keep data/ intact.')
    elif args.aec_output_headroom_db is not None:
        print('Saved:', config.path)
        print('Chat reconnects to apply the audio setting. Cloud and speaker-volume settings are preserved.')


if __name__ == '__main__':
    main()
