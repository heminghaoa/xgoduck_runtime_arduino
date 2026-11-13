"""DRADUCK: a custom voice server answers to 「ねえ、ドラダック」 (or 「ドラダック」 when chosen) once its
wake model is installed; Luwu's regions keep their own wake words."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))

import voice_config
from voice_config import wake_profile


class DraduckWakeTest(unittest.TestCase):
    def setUp(self):
        self.models = Path(tempfile.mkdtemp())
        self.settings = Path(tempfile.mkdtemp()) / 'draduck.json'
        self.saved = voice_config.WAKE_MODELS, voice_config.DRADUCK_SETTINGS
        voice_config.WAKE_MODELS, voice_config.DRADUCK_SETTINGS = self.models, self.settings

    def tearDown(self):
        voice_config.WAKE_MODELS, voice_config.DRADUCK_SETTINGS = self.saved

    def test_main_wake_word_by_default_short_when_chosen(self):
        custom = {'ota_url': 'https://voice.example/ota/', 'language': 'cn'}
        self.assertEqual(wake_profile(custom)[0], '小鸭小鸭')          # no DRADUCK model installed
        (self.models / 'draduck_short.onnx').write_bytes(b'onnx')
        self.assertEqual(wake_profile(custom)[0], 'ドラダック')        # main missing: short stands in
        (self.models / 'draduck_nee.onnx').write_bytes(b'onnx')
        phrase, settings = wake_profile(custom)
        self.assertEqual(phrase, 'ねえ、ドラダック')
        self.assertEqual(Path(settings['model_path']).name, 'draduck_nee.onnx')
        self.assertEqual(settings['input_scale'], 1.)
        self.settings.write_text(json.dumps({'wake': 'short'}))
        self.assertEqual(wake_profile(custom)[0], 'ドラダック')
        self.assertEqual(wake_profile(custom)[1]['threshold'], .70)
        self.settings.write_text(json.dumps({'wake': 'strict'}))     # not installed: main stands in
        self.assertEqual(Path(wake_profile(custom)[1]['model_path']).name, 'draduck_nee.onnx')
        (self.models / 'draduck_nee_strict.onnx').write_bytes(b'onnx')
        self.assertEqual(Path(wake_profile(custom)[1]['model_path']).name, 'draduck_nee_strict.onnx')
        self.settings.write_text('not json')
        self.assertEqual(wake_profile(custom)[0], 'ねえ、ドラダック')

    def test_installed_models_match_their_provenance(self):
        import hashlib
        for key, (phrase, model, threshold) in voice_config.DRADUCK_WAKE.items():
            info = json.loads((ROOT / f'provenance/draduck-{key}-wakeword.json').read_text())
            path = ROOT / 'python/models' / model
            self.assertEqual(info['classifier']['path'], f'python/models/{model}')
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), info['classifier']['sha256'])
            self.assertEqual(info['preprocessing']['threshold'], threshold)
            self.assertEqual(info['wake_phrase'], phrase)

    def test_regions_keep_luwus_wake_words(self):
        (self.models / 'draduck_nee.onnx').write_bytes(b'onnx')
        self.assertEqual(wake_profile({'cloud_region': 'cn'})[0], '小鸭小鸭')
        self.assertEqual(wake_profile({'cloud_region': 'global'})[0], 'Hey Ducky')

    def test_configure_tool_sets_server_and_wake_word(self):
        data = Path(tempfile.mkdtemp())
        run = lambda *a: subprocess.run([sys.executable, str(ROOT / 'tools/configure-ai.py'), '--data-dir', str(data), *a],
                                        capture_output=True, text=True)
        self.assertEqual(run('--ota-url', 'http://plain.example/ota/').returncode, 2)
        done = run('--ota-url', 'https://voice.example/ota/', '--draduck-wake', 'short')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads((data / 'voice_config.json').read_text())['ota_url'], 'https://voice.example/ota/')
        self.assertEqual(json.loads((data / 'draduck.json').read_text()), {'wake': 'short'})
        self.assertIn('DRADUCK wake word: ドラダック', done.stdout)
        # voice_config.json keeps only fields Luwu's app knows, so a downgrade still reads it.
        self.assertEqual(set(json.loads((data / 'voice_config.json').read_text())) - set(voice_config.DEFAULTS), set())


if __name__ == '__main__':
    unittest.main()
