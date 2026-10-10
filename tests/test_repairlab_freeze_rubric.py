import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from repairlab.freeze_rubric import freeze_rubric, verify_rubric_config


def calibration(threshold=2.5):
    return {"schema": "repairlab-threshold-calibration-v1",
            "selection_partition": "development", "chosen_threshold": threshold,
            "candidate_results": [], "held_out": {}, "selection_rule": "fixture",
            "limitations": []}


class FrozenRubricTests(unittest.TestCase):
    def test_freeze_is_deterministic_and_detects_modification(self):
        first = freeze_rubric(calibration())
        second = freeze_rubric(calibration())
        self.assertEqual(first, second)
        self.assertTrue(verify_rubric_config(first))
        changed = dict(first); changed["threshold"] = 3.0
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            verify_rubric_config(changed)

    def test_rejects_nondevelopment_selection_and_bad_weights(self):
        report = calibration(); report["selection_partition"] = "held_out"
        with self.assertRaisesRegex(ValueError, "development"):
            freeze_rubric(report)
        with self.assertRaisesRegex(ValueError, "sum to 1"):
            freeze_rubric(calibration(), {"timing": .5, "energy": .5,
                                                   "pitch": .5, "spectral": .5})

    def test_cli_writes_strict_verified_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "calibration.json"; output = root / "rubric.json"
            source.write_text(json.dumps(calibration()))
            done = subprocess.run([sys.executable, "-m", "repairlab.freeze_rubric",
                                   str(source), "--output", str(output)],
                                  check=True, capture_output=True, text=True)
            config = json.loads(output.read_text())
            self.assertTrue(verify_rubric_config(config))
            self.assertEqual(json.loads(done.stdout)["config_sha256"], config["config_sha256"])
            self.assertNotIn("NaN", output.read_text())


if __name__ == "__main__":
    unittest.main()
