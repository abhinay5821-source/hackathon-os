import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from repairlab.freeze_rubric import freeze_rubric
from repairlab.score_held_out import score_held_out
from test_repairlab_batch_detect import _alignment, _audio


def frozen_config():
    calibration = {"schema": "repairlab-threshold-calibration-v1",
                   "selection_partition": "development", "chosen_threshold": 2.5,
                   "candidate_results": [], "held_out": {}, "selection_rule": "fixture",
                   "limitations": []}
    return freeze_rubric(calibration)


class HeldOutScoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        alignment = _alignment([0.1, 0.4, 0.7, 1.0, 1.3])
        for prefix, quiet in (("base", None), ("dev", None), ("held", 2)):
            _audio(self.root / f"{prefix}.wav", alignment["words"], quiet=quiet)
            (self.root / f"{prefix}.json").write_text(json.dumps(alignment))
        self.pairs = [{"derivative_id": name, "baseline_audio": "base.wav",
                       "participant_audio": f"{name}.wav", "baseline_alignment": "base.json",
                       "participant_alignment": f"{name}.json"} for name in ("dev", "held")]
        label = {"start_seconds": 0.7, "end_seconds": 0.9, "flaw_type": "quiet"}
        self.truth = [{"derivative_id": "dev", "labels": []},
                      {"derivative_id": "held", "labels": [label]}]
        self.manifest = [{"derivative_id": "dev", "duration_seconds": 1.6,
                          "partition": "development"},
                         {"derivative_id": "held", "duration_seconds": 1.6,
                          "partition": "held_out"}]

    def tearDown(self):
        self.temp.cleanup()

    def test_scores_only_held_out_and_persists_fingerprints(self):
        config = frozen_config()
        result = score_held_out(self.pairs, self.root, self.truth, self.manifest, config)
        self.assertEqual(result["derivative_ids"], ["held"])
        self.assertEqual(result["rubric_config_sha256"], config["config_sha256"])
        self.assertEqual(result["calibration_sha256"], config["calibration_sha256"])
        self.assertNotIn("dev", json.dumps(result))

    def test_rejects_modified_config_and_empty_held_out(self):
        config = frozen_config(); config["threshold"] = 3.0
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            score_held_out(self.pairs, self.root, self.truth, self.manifest, config)
        manifest = [dict(row, partition="development") for row in self.manifest]
        with self.assertRaisesRegex(ValueError, "nonempty"):
            score_held_out(self.pairs, self.root, self.truth, manifest, frozen_config())

    def test_cli_writes_strict_json(self):
        paths = {}
        for name, rows in (("pairs", self.pairs), ("truth", self.truth),
                           ("manifest", self.manifest)):
            paths[name] = self.root / f"{name}.jsonl"
            paths[name].write_text("".join(json.dumps(row) + "\n" for row in rows))
        rubric = self.root / "rubric.json"; rubric.write_text(json.dumps(frozen_config()))
        output = self.root / "held-out.json"
        done = subprocess.run([sys.executable, "-m", "repairlab.score_held_out",
                               str(paths["pairs"]), str(paths["truth"]), str(paths["manifest"]),
                               str(rubric), "--output", str(output)],
                              check=True, capture_output=True, text=True)
        result = json.loads(output.read_text())
        self.assertEqual(json.loads(done.stdout)["rubric_config_sha256"],
                         result["rubric_config_sha256"])
        self.assertNotIn("NaN", output.read_text())


if __name__ == "__main__":
    unittest.main()
