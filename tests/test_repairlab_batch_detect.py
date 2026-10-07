import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from repairlab.batch_detect import detect_manifest


def _alignment(starts):
    return {"words": [{"word": f"W{i}", "start_seconds": start,
                       "end_seconds": start + 0.2} for i, start in enumerate(starts)]}


def _audio(path, words, quiet=None):
    samples = np.zeros(round((words[-1]["end_seconds"] + 0.1) * 16000), dtype=np.float32)
    for index, word in enumerate(words):
        start, end = round(word["start_seconds"] * 16000), round(word["end_seconds"] * 16000)
        time = np.arange(end - start) / 16000
        samples[start:end] = (0.03 if index == quiet else 0.3) * np.sin(2 * np.pi * 180 * time)
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1); target.setsampwidth(2); target.setframerate(16000)
        target.writeframes(np.round(samples * 32767).astype("<i2").tobytes())


class BatchDetectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        base = _alignment([0.1, 0.4, 0.7, 1.0, 1.3])
        changed = _alignment([0.1, 0.4, 1.1, 1.4, 1.7])
        _audio(self.root / "base.wav", base["words"])
        _audio(self.root / "changed.wav", changed["words"], quiet=2)
        (self.root / "base.json").write_text(json.dumps(base))
        (self.root / "changed.json").write_text(json.dumps(changed))
        self.row = {"derivative_id": "clip-b", "baseline_audio": "base.wav",
                    "participant_audio": "changed.wav", "baseline_alignment": "base.json",
                    "participant_alignment": "changed.json"}

    def tearDown(self):
        self.temp.cleanup()

    def test_detector_emits_evaluator_ready_prediction(self):
        rows = detect_manifest([self.row], self.root)
        self.assertEqual(rows[0]["schema"], "repairlab-detector-prediction-v1")
        self.assertEqual(rows[0]["derivative_id"], "clip-b")
        region = next(item for item in rows[0]["regions"] if item["word"] == "W2")
        self.assertIn(region["candidate_flaw_type"], {"quiet", "inserted_pause"})

    def test_cli_sorts_and_writes_strict_jsonl(self):
        first = dict(self.row, derivative_id="clip-z")
        second = dict(self.row, derivative_id="clip-a")
        pairs, output = self.root / "pairs.jsonl", self.root / "predictions.jsonl"
        pairs.write_text(json.dumps(first) + "\n" + json.dumps(second) + "\n")
        completed = subprocess.run([sys.executable, "-m", "repairlab.batch_detect", str(pairs),
                                    "--output", str(output)], check=True, text=True,
                                   capture_output=True)
        rows = [json.loads(line) for line in output.read_text().splitlines()]
        self.assertEqual([row["derivative_id"] for row in rows], ["clip-a", "clip-z"])
        self.assertEqual(json.loads(completed.stdout)["clips"], 2)
        self.assertNotIn("NaN", output.read_text())

    def test_rejects_duplicates_and_paths_outside_manifest(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            detect_manifest([self.row, self.row], self.root)
        unsafe = dict(self.row, baseline_audio="../outside.wav")
        with self.assertRaisesRegex(ValueError, "escapes"):
            detect_manifest([unsafe], self.root)


if __name__ == "__main__":
    unittest.main()
