import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from repairlab.dataset import build_dataset
from repairlab.verify_dataset import verify_dataset


class VerifyDatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        audio = self.root / "source.wav"
        samples = (np.zeros(16000) * 32767).astype("<i2")
        with wave.open(str(audio), "wb") as target:
            target.setnchannels(1); target.setsampwidth(2); target.setframerate(16000)
            target.writeframes(samples.tobytes())
        source = {"audio_path": audio, "transcript": "ONE",
                  "words": [{"word": "ONE", "start_seconds": 0.1, "end_seconds": 0.8}],
                  "metadata": {"source_url": "https://example.test/audio", "recording_id": "rec",
                               "speaker_id": "speaker", "text_id": "text",
                               "rights_url": "https://example.test/rights", "rights_basis": "fixture",
                               "reviewed_on": "2026-10-09", "baseline_rationale": "fixture",
                               "redistribution_allowed": True, "derivatives_allowed": True,
                               "rights_review_complete": True}}
        self.dataset = self.root / "dataset"
        build_dataset(self.dataset, [source], [
            {"recording_id": "rec", "partition": "held_out", "corruption": "clean"}
        ])

    def tearDown(self):
        self.temp.cleanup()

    def test_verifies_complete_dataset_and_cli(self):
        self.assertTrue(verify_dataset(self.dataset)["verified"])
        completed = subprocess.run(
            [sys.executable, "-m", "repairlab.verify_dataset", str(self.dataset)],
            check=True, capture_output=True, text=True)
        self.assertTrue(json.loads(completed.stdout)["verified"])

    def test_rejects_changed_missing_and_extra_audio(self):
        audio = next((self.dataset / "audio").glob("*.wav"))
        original = audio.read_bytes()
        audio.write_bytes(original + b"changed")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            verify_dataset(self.dataset)
        audio.write_bytes(original)
        extra = self.dataset / "audio" / "extra.wav"
        extra.write_bytes(original)
        with self.assertRaisesRegex(ValueError, "file set"):
            verify_dataset(self.dataset)
        extra.unlink()
        audio.unlink()
        with self.assertRaisesRegex(ValueError, "file set"):
            verify_dataset(self.dataset)

    def test_rejects_changed_manifest(self):
        manifest = self.dataset / "detector_manifest.jsonl"
        manifest.write_text(manifest.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            verify_dataset(self.dataset)
