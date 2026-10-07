import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from repairlab.evaluate_detector import evaluate_with_baselines, score_records, temporal_iou


class DetectorEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.truth = [
            {"derivative_id": "a", "labels": [{"start_seconds": 1.0, "end_seconds": 2.0,
                                                  "flaw_type": "quiet"}]},
            {"derivative_id": "b", "labels": [{"start_seconds": 0.5, "end_seconds": 1.0,
                                                  "flaw_type": "inserted_pause"}]},
            {"derivative_id": "c", "labels": [], "control": {"expected_flaw": False}},
        ]
        self.predictions = [
            {"derivative_id": "a", "regions": [{"start_seconds": 1.1, "end_seconds": 2.1,
                                                    "candidate_flaw_type": "quiet"}]},
            {"derivative_id": "b", "regions": [{"start_seconds": 0.5, "end_seconds": 1.0,
                                                    "candidate_flaw_type": "quiet"}]},
            {"derivative_id": "c", "regions": []},
        ]
        self.manifest = [{"derivative_id": key, "duration_seconds": 3.0} for key in "abc"]

    def test_temporal_metrics_type_confusion_and_control_rate(self):
        report = score_records(self.truth, self.predictions, 0.3)
        self.assertEqual(report["matched_regions"], 2)
        self.assertAlmostEqual(report["region_f1"], 1.0)
        self.assertAlmostEqual(report["mean_boundary_error_seconds_on_matches"], 0.05)
        self.assertAlmostEqual(report["exact_type_accuracy_on_matches"], 0.5)
        self.assertEqual(report["confusion_matrix"]["inserted_pause"]["quiet"], 1)
        self.assertEqual(report["control_clip_false_positive_rate"], 0.0)

    def test_unmatched_regions_and_false_positive_control(self):
        predictions = [dict(row) for row in self.predictions]
        predictions[0] = {"derivative_id": "a", "regions": []}
        predictions[2] = {"derivative_id": "c", "regions": [{"start_seconds": 0.1,
                          "end_seconds": 0.2, "candidate_flaw_type": "quiet"}]}
        report = score_records(self.truth, predictions)
        self.assertEqual(report["confusion_matrix"]["quiet"]["__missed__"], 1)
        self.assertEqual(report["confusion_matrix"]["__none__"]["quiet"], 1)
        self.assertEqual(report["control_clip_false_positive_rate"], 1.0)

    def test_baselines_are_seeded_and_reported(self):
        first = evaluate_with_baselines(self.truth, self.predictions, self.manifest, seed=9)
        second = evaluate_with_baselines(self.truth, self.predictions, self.manifest, seed=9)
        self.assertEqual(first, second)
        self.assertEqual(set(first["baselines"]), {"predict_no_flaws", "predict_full_clip",
                                                   "random_quarter_clip"})
        json.dumps(first, allow_nan=False)

    def test_rejects_id_mismatch_invalid_regions_and_threshold(self):
        with self.assertRaisesRegex(ValueError, "identical"):
            score_records(self.truth, self.predictions[:-1])
        broken = [dict(row) for row in self.predictions]
        broken[0] = {"derivative_id": "a", "regions": [{"start_seconds": 2.0,
                     "end_seconds": 1.0, "candidate_flaw_type": "quiet"}]}
        with self.assertRaisesRegex(ValueError, "boundaries"):
            score_records(self.truth, broken)
        with self.assertRaisesRegex(ValueError, "iou_threshold"):
            score_records(self.truth, self.predictions, 0)

    def test_cli_writes_strict_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, rows in (("truth", self.truth), ("predictions", self.predictions),
                               ("manifest", self.manifest)):
                (root / f"{name}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
            output = root / "report.json"
            subprocess.run([sys.executable, "-m", "repairlab.evaluate_detector",
                            str(root / "truth.jsonl"), str(root / "predictions.jsonl"),
                            str(root / "manifest.jsonl"), "--output", str(output)],
                           check=True, capture_output=True, text=True)
            report = json.loads(output.read_text())
            self.assertEqual(report["schema"], "repairlab-detector-evaluation-v1")

    def test_iou(self):
        self.assertAlmostEqual(temporal_iou({"start_seconds": 0, "end_seconds": 2},
                                           {"start_seconds": 1, "end_seconds": 3}), 1 / 3)


if __name__ == "__main__":
    unittest.main()
