import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from repairlab.calibrate_threshold import calibrate
from test_repairlab_batch_detect import _alignment, _audio


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        base = _alignment([0.1, 0.4, 0.7, 1.0, 1.3])
        for prefix, quiet in (("base", None), ("dev", 2), ("held", 2)):
            _audio(self.root / f"{prefix}.wav", base["words"], quiet=quiet)
            (self.root / f"{prefix}.json").write_text(json.dumps(base))
        self.pairs = []
        for identifier in ("dev", "held"):
            self.pairs.append({"derivative_id": identifier, "baseline_audio": "base.wav",
                "participant_audio": f"{identifier}.wav", "baseline_alignment": "base.json",
                "participant_alignment": f"{identifier}.json"})
        label = {"start_seconds": 0.7, "end_seconds": 0.9, "flaw_type": "quiet"}
        self.truth = [{"derivative_id": identifier, "labels": [label]}
                      for identifier in ("dev", "held")]
        self.manifest = [{"derivative_id": "dev", "duration_seconds": 1.6,
                          "partition": "development"},
                         {"derivative_id": "held", "duration_seconds": 1.6,
                          "partition": "held_out"}]

    def tearDown(self):
        self.temp.cleanup()

    def test_held_out_truth_cannot_change_threshold_selection(self):
        first = calibrate(self.pairs, self.root, self.truth, self.manifest, [1.5, 2.5, 10.0])
        altered = [dict(row) for row in self.truth]
        altered[1] = {"derivative_id": "held", "labels": []}
        second = calibrate(self.pairs, self.root, altered, self.manifest, [1.5, 2.5, 10.0])
        self.assertEqual(first["chosen_threshold"], second["chosen_threshold"])
        self.assertNotEqual(first["held_out"]["system"], second["held_out"]["system"])

    def test_rejects_missing_partition_and_cli_is_strict_json(self):
        with self.assertRaisesRegex(ValueError, "nonempty"):
            calibrate(self.pairs[:1], self.root, self.truth[:1], self.manifest[:1], [2.5])
        paths = {}
        for name, rows in (("pairs", self.pairs), ("truth", self.truth),
                           ("manifest", self.manifest)):
            paths[name] = self.root / f"{name}.jsonl"
            paths[name].write_text("".join(json.dumps(row) + "\n" for row in rows))
        output = self.root / "calibration.json"
        done = subprocess.run([sys.executable, "-m", "repairlab.calibrate_threshold",
                               str(paths["pairs"]), str(paths["truth"]), str(paths["manifest"]),
                               "--candidates", "1.5", "2.5", "10", "--output", str(output)],
                              check=True, capture_output=True, text=True)
        report = json.loads(output.read_text())
        self.assertEqual(json.loads(done.stdout)["chosen_threshold"], report["chosen_threshold"])
        self.assertNotIn("NaN", output.read_text())


if __name__ == "__main__":
    unittest.main()
