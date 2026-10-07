import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_repairlab_batch_detect import _alignment, _audio
from repairlab.ablate_detector import evaluate_ablations


class AblationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        base = _alignment([0.1, 0.4, 0.7, 1.0, 1.3])
        changed = _alignment([0.1, 0.4, 0.7, 1.0, 1.3])
        _audio(self.root / "base.wav", base["words"])
        _audio(self.root / "changed.wav", changed["words"], quiet=2)
        (self.root / "base.json").write_text(json.dumps(base))
        (self.root / "changed.json").write_text(json.dumps(changed))
        self.pairs = [{"derivative_id": "clip", "baseline_audio": "base.wav",
                       "participant_audio": "changed.wav", "baseline_alignment": "base.json",
                       "participant_alignment": "changed.json"}]
        self.truth = [{"derivative_id": "clip", "labels": [{"start_seconds": 0.7,
                       "end_seconds": 0.9, "flaw_type": "quiet"}]}]
        self.manifest = [{"derivative_id": "clip", "duration_seconds": 1.6}]

    def tearDown(self):
        self.temp.cleanup()

    def test_energy_ablation_removes_energy_signal(self):
        report = evaluate_ablations(self.pairs, self.root, self.truth, self.manifest)
        self.assertEqual(report["schema"], "repairlab-feature-ablation-v1")
        self.assertEqual(report["full"]["system"]["matched_regions"], 1)
        self.assertEqual(report["leave_one_group_out"]["energy"]["metrics"]["matched_regions"], 0)
        self.assertEqual(set(report["leave_one_group_out"]),
                         {"energy", "pitch", "spectrum", "timing"})

    def test_cli_writes_strict_report(self):
        paths = {}
        for name, rows in (("pairs", self.pairs), ("truth", self.truth),
                           ("manifest", self.manifest)):
            paths[name] = self.root / f"{name}.jsonl"
            paths[name].write_text("".join(json.dumps(row) + "\n" for row in rows))
        output = self.root / "ablation.json"
        completed = subprocess.run([sys.executable, "-m", "repairlab.ablate_detector",
                                    str(paths["pairs"]), str(paths["truth"]),
                                    str(paths["manifest"]), "--output", str(output)],
                                   check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(completed.stdout)["ablations"], 4)
        self.assertNotIn("NaN", output.read_text())


if __name__ == "__main__":
    unittest.main()
