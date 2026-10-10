import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from repairlab.submission_gate import validate_submission
from repairlab.freeze_rubric import freeze_rubric


class SubmissionGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        rubric = freeze_rubric({"schema": "repairlab-threshold-calibration-v1",
                                "selection_partition": "development", "chosen_threshold": 0.25})
        alignment = {"schema": "repairlab-human-alignment-score-v1", "labelled_words": 15,
                     "labelled_fraction": 0.1, "start_mae_seconds": 0.08,
                     "end_mae_seconds": 0.09, "boundary_median_absolute_error_seconds": 0.07,
                     "boundary_p95_absolute_error_seconds": 0.2,
                     "boundary_max_absolute_error_seconds": 0.3,
                     "boundaries_within_100ms_fraction": 0.7}
        evaluation = {"schema": "repairlab-detector-evaluation-v1", "system": {"matched_regions": 1},
                      "baselines": {"predict_no_flaws": {"matched_regions": 0}}}
        held = {"schema": "repairlab-frozen-held-out-score-v1", "partition": "held_out",
                "rubric_config_sha256": rubric["config_sha256"],
                "calibration_sha256": rubric["calibration_sha256"],
                "derivative_ids": ["held-1"], "report": evaluation}
        records = {
            "technical_document": ("report.pdf", b"%PDF-1.4\n1 0 obj <</Type /Page>> endobj\n2 0 obj <</Type /Page>> endobj\n%%EOF"),
            "alignment_report": ("alignment.json", json.dumps(alignment).encode()),
            "held_out_report": ("held.json", json.dumps(held).encode()),
            "dataset_verification": ("dataset.json", json.dumps({"verified": True, "files": {"build.json": "a"}}).encode()),
            "rubric_config": ("rubric.json", json.dumps(rubric).encode()),
        }
        artifacts = {}
        for name, (filename, data) in records.items():
            (self.root / filename).write_bytes(data)
            artifacts[name] = {"path": filename, "sha256": hashlib.sha256(data).hexdigest()}
        self.manifest = {"schema": "repairlab-track-c-submission-v1",
                         "public_dataset_url": "https://example.org/repairlab-data",
                         "video_url": "https://example.org/repairlab-demo",
                         "technical_document_pages": 2, "video_duration_seconds": 300,
                         "video_english_or_subtitled": True, "artifacts": artifacts}

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_complete_hashed_bundle(self):
        result = validate_submission(self.root, self.manifest)
        self.assertTrue(result["evidence_bundle_valid"])
        self.assertEqual(result["checked_artifacts"], 5)
        self.assertEqual(result["measured_pdf_pages"], 2)

    def _replace_json(self, artifact, value):
        record = self.manifest["artifacts"][artifact]
        data = json.dumps(value).encode()
        (self.root / record["path"]).write_bytes(data)
        record["sha256"] = hashlib.sha256(data).hexdigest()

    def test_rejects_schema_only_measurement_reports(self):
        self._replace_json("alignment_report", {"schema": "repairlab-human-alignment-score-v1"})
        with self.assertRaisesRegex(ValueError, "labelled_words"):
            validate_submission(self.root, self.manifest)

    def test_rejects_empty_held_out_measurements(self):
        held = json.loads((self.root / "held.json").read_text())
        held["report"] = {}
        self._replace_json("held_out_report", held)
        with self.assertRaisesRegex(ValueError, "detector and baseline"):
            validate_submission(self.root, self.manifest)

    def test_rejects_rubric_fingerprint_mismatch(self):
        held = json.loads((self.root / "held.json").read_text())
        held["rubric_config_sha256"] = "0" * 64
        self._replace_json("held_out_report", held)
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            validate_submission(self.root, self.manifest)

    def test_rejects_document_or_video_limits(self):
        self.manifest["technical_document_pages"] = 7
        with self.assertRaisesRegex(ValueError, "between 1 and 6"):
            validate_submission(self.root, self.manifest)
        self.manifest["technical_document_pages"] = 2
        self.manifest["video_duration_seconds"] = 120
        with self.assertRaisesRegex(ValueError, "between 180 and 600"):
            validate_submission(self.root, self.manifest)

    def test_rejects_declared_page_count_that_differs_from_pdf(self):
        self.manifest["technical_document_pages"] = 1
        with self.assertRaisesRegex(ValueError, "does not match measured"):
            validate_submission(self.root, self.manifest)

    def test_rejects_placeholder_pdf(self):
        data = b"%PDF fixture"
        (self.root / "report.pdf").write_bytes(data)
        self.manifest["artifacts"]["technical_document"]["sha256"] = hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(ValueError, "structurally recognizable"):
            validate_submission(self.root, self.manifest)

    def test_rejects_tampering_and_nonpublic_url(self):
        (self.root / "held.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            validate_submission(self.root, self.manifest)
        self.manifest["public_dataset_url"] = "http://localhost/data"
        with self.assertRaisesRegex(ValueError, "public HTTPS URL"):
            validate_submission(self.root, self.manifest)


if __name__ == "__main__":
    unittest.main()
