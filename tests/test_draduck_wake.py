"""DRADUCK: a custom voice server answers to 「ねえ、ドラダック」 (or 「ドラダック」 when chosen) once its
wake model is installed; Luwu's regions keep their own wake words."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

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


VENDOR = ROOT / 'python/vendor/luwu_os'


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'numpy is installed in the target userspace')
class FalseWakeGuardTest(unittest.TestCase):
    """Owner 2026-11-25: the lab duck woke three times in half an hour with nobody speaking, on its microphone's
    own noise. A wake now needs the score over two windows in a row, and speech over the noise floor."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('draduck_wake_guard_test', VENDOR / 'apps/ai/wakeword_manager.py')
        cls.module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, LUWU_ROOT=str(VENDOR)):
            spec.loader.exec_module(cls.module)

    def noise(self, seconds, level, seed=0):
        import numpy as np
        return (np.random.default_rng(seed).standard_normal(int(16000 * seconds)) * level).astype(np.float32)

    def test_speech_gate_hears_speech_over_the_noise_and_nothing_in_noise_alone(self):
        import numpy as np
        for gain in (1., 4., 1 / 32768):                    # relative levels: gain and PCM scale don't matter
            with self.subTest(gain=gain):
                gate = self.module.SpeechGate(*voice_config.DRADUCK_SPEECH)
                gate.feed(self.noise(1.5, .02) * gain)
                self.assertFalse(gate.spoke())              # under two seconds heard: nothing counts yet
                gate.feed(self.noise(8.5, .02, 1) * gain)
                self.assertLess(gate.loud_frames(), 2)
                self.assertFalse(gate.spoke())
                # Fluctuating noise (within a few dB, as before the lab duck's false wakes) is still no speech.
                wobble = self.noise(2, .02, 2) * np.repeat(np.random.default_rng(3).uniform(.7, 1.6, 25), 1280)
                gate.feed(wobble * gain)
                self.assertFalse(gate.spoke())
                gate.feed(np.concatenate([self.noise(.4, .02, 4), self.noise(.9, .2, 5), self.noise(.2, .02, 6)]) * gain)
                self.assertGreaterEqual(gate.loud_frames(), 10)
                self.assertTrue(gate.spoke())               # about a second, 20 dB over the noise
                gate.feed(self.noise(2.1, .02, 7) * gain)
                self.assertFalse(gate.spoke())              # and two seconds later it is forgotten
        # Blocks of any size give the same frames; a break in the stream forgets the two seconds, not the floor.
        gate = self.module.SpeechGate(*voice_config.DRADUCK_SPEECH)
        audio = np.concatenate([self.noise(6, .02), self.noise(1, .2, 1)])
        for start in range(0, len(audio), 960):
            gate.feed(audio[start:start + 960])
        self.assertTrue(gate.spoke())
        gate.reset()
        self.assertEqual(gate.loud_frames(), 0)
        gate.feed(self.noise(.8, .2, 2))
        self.assertTrue(gate.spoke())
        for bad in ((2, 4), (40, 4), (True, 4), (10, 0), (10, 26), (10, 4.)):
            with self.assertRaises(ValueError):
                self.module.SpeechGate(*bad)

    def listen(self, scores, audio, **settings):
        """Run the listening loop over `audio` (float, 16 kHz) with the model's scores scripted per window."""
        import numpy as np
        woke = Mock()
        manager = self.module.WakeWordManager(stride_duration=.08, shared_input=True, on_wakeup=woke, input_scale=1.,
                                              threshold=.3, cooldown_sec=2., **settings)
        manager._load_model = Mock(return_value=True)
        manager._running = True
        pcm = (np.clip(audio, -1, 1) * 32767).astype('<i2')
        blocks = [pcm[i:i + 960].tobytes() for i in range(0, len(pcm) - 959, 960)]
        left = iter(scores)

        def feed_next():
            if blocks:
                manager.feed_pcm(blocks.pop(0), 0., 0, feed_next.sequence)
                feed_next.sequence += 1
            else:
                manager._running = False
        feed_next.sequence = 1

        def predict(window):
            return next(left, 0.)

        manager._on_ready = feed_next
        manager._predict = predict
        with patch('time.monotonic', return_value=0.), patch('time.sleep', side_effect=lambda _: feed_next()), \
             patch('builtins.print'):
            manager._listen_loop()
        return woke.call_count

    def test_one_high_window_alone_does_not_wake_two_in_a_row_do(self):
        quiet = self.noise(6, .02)
        self.assertEqual(self.listen([0, .9, 0, 0, .9, 0], quiet), 1)                       # as before: the first spike
        self.assertEqual(self.listen([0, .9, 0, 0, .9, 0], quiet, confirm_windows=2), 0)
        self.assertEqual(self.listen([0, .9, .1, .9, .5, 0], quiet, confirm_windows=2), 1)
        self.assertEqual(self.listen([0, .9, .9, .9, .9, 0], quiet, confirm_windows=2), 1)  # one wake
        with self.assertRaises(ValueError):
            self.module.WakeWordManager(confirm_windows=0)

    def test_a_high_score_with_nobody_speaking_does_not_wake(self):
        import numpy as np
        high = [.9] * 200
        quiet = self.noise(8, .02)
        self.assertEqual(self.listen(high, quiet, confirm_windows=2), 1)                    # without the gate: a wake
        self.assertEqual(self.listen(high, quiet, confirm_windows=2, speech_rise_db=voice_config.DRADUCK_SPEECH[0], speech_frames=voice_config.DRADUCK_SPEECH[1]), 0)
        called = np.concatenate([self.noise(6, .02), self.noise(1, .2, 1), self.noise(1, .02, 2)])
        self.assertEqual(self.listen(high, called, confirm_windows=2, speech_rise_db=voice_config.DRADUCK_SPEECH[0], speech_frames=voice_config.DRADUCK_SPEECH[1]), 1)

    def test_draduck_profiles_carry_the_guards_and_luwus_do_not(self):
        models = Path(tempfile.mkdtemp())
        saved = voice_config.WAKE_MODELS
        voice_config.WAKE_MODELS = models
        try:
            (models / 'draduck_nee.onnx').write_bytes(b'onnx')
            (models / 'xiaoya.onnx').write_bytes(b'onnx')
            ours = wake_profile({'ota_url': 'https://voice.example/ota/'})[1]
            self.assertEqual((ours['confirm_windows'], ours['speech_rise_db'], ours['speech_frames']),
                             (voice_config.DRADUCK_CONFIRM_WINDOWS, *voice_config.DRADUCK_SPEECH))
            self.module.SpeechGate(*voice_config.DRADUCK_SPEECH)
            theirs = wake_profile({'cloud_region': 'cn'})[1]
            self.assertFalse({'confirm_windows', 'speech_rise_db', 'speech_frames'} & set(theirs))
        finally:
            voice_config.WAKE_MODELS = saved


if __name__ == '__main__':
    unittest.main()
