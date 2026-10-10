import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from repairlab.submission_gate import validate_submission


class SubmissionGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        records = {
            "technical_document": ("report.pdf", b"%PDF fixture"),
            "alignment_report": ("alignment.json", json.dumps({"schema": "repairlab-human-alignment-score-v1"}).encode()),
            "held_out_report": ("held.json", json.dumps({"schema": "repairlab-frozen-held-out-score-v1", "partition": "held_out"}).encode()),
            "dataset_verification": ("dataset.json", json.dumps({"verified": True, "files": {"build.json": "a"}}).encode()),
        }
        artifacts = {}
        for name, (filename, data) in records.items():
            (self.root / filename).write_bytes(data)
            artifacts[name] = {"path": filename, "sha256": hashlib.sha256(data).hexdigest()}
        self.manifest = {"schema": "repairlab-track-c-submission-v1",
                         "public_dataset_url": "https://example.org/repairlab-data",
                         "video_url": "https://example.org/repairlab-demo",
                         "technical_document_pages": 6, "video_duration_seconds": 300,
                         "video_english_or_subtitled": True, "artifacts": artifacts}

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_complete_hashed_bundle(self):
        self.assertTrue(validate_submission(self.root, self.manifest)["ready"])

    def test_rejects_document_or_video_limits(self):
        self.manifest["technical_document_pages"] = 7
        with self.assertRaisesRegex(ValueError, "between 1 and 6"):
            validate_submission(self.root, self.manifest)
        self.manifest["technical_document_pages"] = 6
        self.manifest["video_duration_seconds"] = 120
        with self.assertRaisesRegex(ValueError, "between 180 and 600"):
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
