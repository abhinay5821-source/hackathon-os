import unittest
import wave
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
from repairlab.audio_align import load_audio, normalize_transcript


class AudioInputTests(unittest.TestCase):
    def test_pcm_conversion_preserves_samples(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "clip.wav"
            with wave.open(str(path), "wb") as audio:
                audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                audio.writeframes(np.array([-32768, 0, 16384], dtype="<i2").tobytes())
            np.testing.assert_array_equal(load_audio(path), [-1, 0, 0.5])

    def test_wrong_sample_rate_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "clip.wav"
            with wave.open(str(path), "wb") as audio:
                audio.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
                audio.writeframes(b"\x00\x00")
            with self.assertRaises(ValueError):
                load_audio(path)

    def test_transcript_normalization_and_unsupported_input(self):
        self.assertEqual(normalize_transcript("We choose\nthe moon!"), "WE CHOOSE THE MOON")
        for text in ("1962", "", "こんにちは"):
            with self.assertRaises(ValueError):
                normalize_transcript(text)
