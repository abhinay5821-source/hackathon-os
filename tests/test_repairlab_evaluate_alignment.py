import unittest

from repairlab.evaluate_alignment import evaluate_alignment


def prediction():
    return {
        "audio_sha256": "a" * 64,
        "duration_seconds": 2.0,
        "words": [
            {"word": "WE", "start_seconds": 0.1, "end_seconds": 0.4},
            {"word": "CHOOSE", "start_seconds": 0.5, "end_seconds": 0.9},
            {"word": "MOON", "start_seconds": 1.1, "end_seconds": 1.6},
        ],
    }


def reference():
    return {
        "evidence_type": "human_manual",
        "audio_sha256": "a" * 64,
        "duration_seconds": 2.0,
        "annotation_method": "Auditory review plus waveform inspection",
        "annotated_at": "2026-10-07T00:00:00Z",
        "words": [
            {"word_index": 0, "word": "WE", "start_seconds": 0.15, "end_seconds": 0.45},
            {"word_index": 2, "word": "MOON", "start_seconds": 1.2, "end_seconds": 1.8},
        ],
    }


class AlignmentEvaluationTests(unittest.TestCase):
    def test_metrics_for_labelled_subset(self):
        result = evaluate_alignment(prediction(), reference())
        self.assertEqual(result["labelled_words"], 2)
        self.assertAlmostEqual(result["labelled_fraction"], 2 / 3)
        self.assertAlmostEqual(result["boundary_median_absolute_error_seconds"], 0.075)
        self.assertAlmostEqual(result["boundary_max_absolute_error_seconds"], 0.2)
        self.assertAlmostEqual(result["boundaries_within_100ms_fraction"], 0.75)

    def test_rejects_nonhuman_reference_claim(self):
        labels = reference()
        labels["evidence_type"] = "model_generated"
        with self.assertRaisesRegex(ValueError, "human_manual"):
            evaluate_alignment(prediction(), labels)

    def test_rejects_word_mismatch_and_duplicate_index(self):
        labels = reference()
        labels["words"][0]["word"] = "US"
        with self.assertRaisesRegex(ValueError, "Word mismatch"):
            evaluate_alignment(prediction(), labels)
        labels = reference()
        labels["words"][1]["word_index"] = 0
        with self.assertRaisesRegex(ValueError, "unique"):
            evaluate_alignment(prediction(), labels)

    def test_rejects_invalid_boundaries(self):
        labels = reference()
        labels["words"][0]["end_seconds"] = 2.1
        with self.assertRaisesRegex(ValueError, "Invalid reference boundary"):
            evaluate_alignment(prediction(), labels)

    def test_rejects_prediction_for_different_audio(self):
        guessed = prediction()
        guessed["audio_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "audio_sha256 do not match"):
            evaluate_alignment(guessed, reference())

    def test_rejects_duration_mismatch(self):
        labels = reference()
        labels["duration_seconds"] = 2.1
        with self.assertRaisesRegex(ValueError, "duration_seconds do not match"):
            evaluate_alignment(prediction(), labels)
