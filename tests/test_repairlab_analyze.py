import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from repairlab.analyze import analyze_pair


def make_audio(path, words, quiet_index=None):
    rate = 16000
    length = round((words[-1]["end_seconds"] + 0.1) * rate)
    samples = np.zeros(length, dtype=np.float32)
    for index, item in enumerate(words):
        start, end = round(item["start_seconds"] * rate), round(item["end_seconds"] * rate)
        time = np.arange(end - start, dtype=float) / rate
        amplitude = 0.04 if index == quiet_index else 0.3
        samples[start:end] = amplitude * np.sin(2 * np.pi * 180 * time)
    pcm = np.round(samples * 32767).astype("<i2")
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1); target.setsampwidth(2); target.setframerate(rate)
        target.writeframes(pcm.tobytes())


def alignment(starts):
    return {"words": [{"word": f"W{index}", "start_seconds": start,
                       "end_seconds": start + 0.2} for index, start in enumerate(starts)]}


class AnalyzeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.baseline_alignment = alignment([0.1, 0.4, 0.7, 1.0, 1.3])
        self.participant_alignment = alignment([0.1, 0.4, 1.1, 1.4, 1.7])
        self.baseline = self.root / "baseline.wav"
        self.participant = self.root / "participant.wav"
        make_audio(self.baseline, self.baseline_alignment["words"])
        make_audio(self.participant, self.participant_alignment["words"], quiet_index=2)

    def tearDown(self):
        self.temp.cleanup()

    def test_pair_analysis_exports_overlay_and_grounded_region(self):
        result = analyze_pair(self.baseline, self.participant,
                              self.baseline_alignment, self.participant_alignment)
        self.assertEqual(result["schema"], "repairlab-pair-analysis-v1")
        self.assertEqual(len(result["baseline"]["frames"]["energy_db"]),
                         len(result["baseline"]["frames"]["frame_center_seconds"]))
        region = next(item for item in result["comparison"]["regions"] if item["word"] == "W2")
        self.assertEqual((region["start_seconds"], region["end_seconds"]), (1.1, 1.3))
        self.assertIn("energy_db", region["feature_deltas"])
        self.assertIn("preceding_pause_seconds", region["feature_deltas"])
        self.assertTrue(result["uncertainty"])

    def test_module_cli_writes_strict_json(self):
        baseline_json = self.root / "baseline.json"
        participant_json = self.root / "participant.json"
        output = self.root / "analysis.json"
        baseline_json.write_text(json.dumps(self.baseline_alignment))
        participant_json.write_text(json.dumps(self.participant_alignment))
        completed = subprocess.run(
            [sys.executable, "-m", "repairlab.analyze", str(self.baseline), str(self.participant),
             str(baseline_json), str(participant_json), "--output", str(output)],
            check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(completed.stdout)["flagged_regions"],
                         len(json.loads(output.read_text())["comparison"]["regions"]))
        self.assertNotIn("NaN", output.read_text())


if __name__ == "__main__":
    unittest.main()
