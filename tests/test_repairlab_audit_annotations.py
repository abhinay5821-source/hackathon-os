import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from repairlab.audit_annotations import audit_annotations


def labels(annotator, shift=0.0):
    return {
        "evidence_type": "human_manual", "audio_sha256": "a" * 64,
        "duration_seconds": 2.0,
        "annotation_method": "Auditory review plus waveform inspection",
        "annotated_at": "2026-10-08T00:00:00Z", "annotator_id": annotator,
        "prediction_hidden": True,
        "words": [
            {"word_index": 0, "word": "WE", "start_seconds": 0.10 + shift, "end_seconds": 0.35 + shift},
            {"word_index": 2, "word": "MOON", "start_seconds": 0.80, "end_seconds": 1.20},
        ],
    }


class AnnotationAuditTests(unittest.TestCase):
    def test_reports_agreement_without_creating_consensus(self):
        result = audit_annotations(labels("ann-a"), labels("ann-b", 0.03))
        self.assertEqual(result["labelled_words"], 2)
        self.assertFalse(result["adjudication_required"])
        self.assertNotIn("words", result)
        self.assertAlmostEqual(result["boundary_max_disagreement_seconds"], 0.03)

    def test_queues_words_over_tolerance(self):
        second = labels("ann-b")
        second["words"][1]["end_seconds"] = 1.35
        result = audit_annotations(labels("ann-a"), second, 0.1)
        self.assertTrue(result["adjudication_required"])
        self.assertEqual(result["adjudication_queue"][0]["word_index"], 2)

    def test_rejects_unblinded_or_nonindependent_records(self):
        second = labels("ann-b")
        second["prediction_hidden"] = False
        with self.assertRaisesRegex(ValueError, "prediction_hidden"):
            audit_annotations(labels("ann-a"), second)
        with self.assertRaisesRegex(ValueError, "must differ"):
            audit_annotations(labels("ann-a"), labels("ann-a"))

    def test_rejects_different_audio_or_word_sets(self):
        second = labels("ann-b")
        second["audio_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "SHA256"):
            audit_annotations(labels("ann-a"), second)

    def test_rejects_boundaries_outside_audio_duration(self):
        second = labels("ann-b")
        second["words"][1]["end_seconds"] = 2.01
        with self.assertRaisesRegex(ValueError, "invalid boundary"):
            audit_annotations(labels("ann-a"), second)
        second = labels("ann-b")
        second["duration_seconds"] = 2.1
        with self.assertRaisesRegex(ValueError, "duration values must match"):
            audit_annotations(labels("ann-a"), second)
        second = labels("ann-b")
        second["words"].pop()
        with self.assertRaisesRegex(ValueError, "same predeclared"):
            audit_annotations(labels("ann-a"), second)

    def test_cli_outputs_strict_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.json").write_text(json.dumps(labels("ann-a")))
            (root / "b.json").write_text(json.dumps(labels("ann-b", 0.02)))
            run = subprocess.run([sys.executable, "-m", "repairlab.audit_annotations",
                                  str(root / "a.json"), str(root / "b.json")],
                                 check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(run.stdout)["labelled_words"], 2)


if __name__ == "__main__":
    unittest.main()
