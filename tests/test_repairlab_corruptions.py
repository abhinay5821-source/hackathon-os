import unittest

import numpy as np

from repairlab.corruptions import insert_pause, quiet_region, rush_region


class CorruptionTests(unittest.TestCase):
    def setUp(self):
        self.audio = np.linspace(-0.8, 0.8, 1000, dtype=np.float32)

    def test_quiet_preserves_duration_and_outside_samples(self):
        output, label = quiet_region(self.audio, 1000, 0.2, 0.5, "medium")
        self.assertEqual(len(output), len(self.audio))
        np.testing.assert_array_equal(output[:200], self.audio[:200])
        np.testing.assert_array_equal(output[500:], self.audio[500:])
        self.assertLess(np.max(np.abs(output[200:500])), np.max(np.abs(self.audio[200:500])))
        self.assertEqual((label["start_sample"], label["end_sample"]), (200, 500))
        self.assertEqual(label["parameters"]["attenuation_db"], 12.0)

    def test_pause_has_exact_label_and_shifts_suffix(self):
        output, label = insert_pause(self.audio, 1000, 0.4, "medium")
        self.assertEqual(len(output), 1450)
        np.testing.assert_array_equal(output[:400], self.audio[:400])
        np.testing.assert_array_equal(output[400:850], np.zeros(450, dtype=np.float32))
        np.testing.assert_array_equal(output[850:], self.audio[400:])
        self.assertEqual((label["start_seconds"], label["end_seconds"]), (0.4, 0.85))

    def test_rush_compresses_only_selected_region(self):
        output, label = rush_region(self.audio, 1000, 0.2, 0.74, "medium")
        expected = round(540 / 1.35)
        self.assertEqual(len(output), 1000 - 540 + expected)
        np.testing.assert_array_equal(output[:200], self.audio[:200])
        np.testing.assert_array_equal(output[200 + expected:], self.audio[740:])
        self.assertEqual((label["start_sample"], label["end_sample"]), (200, 200 + expected))
        self.assertIn("pitch_shifting", label["parameters"]["method"])

    def test_levels_create_strict_severity_gradient(self):
        quiet = [quiet_region(self.audio, 1000, 0.2, 0.5, level)[1]["parameters"]["attenuation_db"]
                 for level in ("mild", "medium", "severe")]
        pauses = [insert_pause(self.audio, 1000, 0.5, level)[1]["parameters"]["inserted_samples"]
                  for level in ("mild", "medium", "severe")]
        rushed = [rush_region(self.audio, 1000, 0.2, 0.8, level)[1]["parameters"]["speed_factor"]
                  for level in ("mild", "medium", "severe")]
        self.assertEqual(quiet, sorted(quiet))
        self.assertEqual(pauses, sorted(pauses))
        self.assertEqual(rushed, sorted(rushed))

    def test_rejects_invalid_audio_regions_and_severity(self):
        bad_audio = self.audio.copy(); bad_audio[0] = np.nan
        cases = [
            lambda: quiet_region(bad_audio, 1000, 0.2, 0.5, "mild"),
            lambda: quiet_region(self.audio, 1000, 0.5, 0.2, "mild"),
            lambda: quiet_region(self.audio, 1000, 0.2, 0.5, "unknown"),
            lambda: insert_pause(self.audio, 1000, 1.1, "mild"),
            lambda: rush_region(self.audio.astype(np.int16), 1000, 0.2, 0.5, "mild"),
        ]
        for case in cases:
            with self.assertRaises(ValueError):
                case()

    def test_labels_are_explicitly_evaluation_only(self):
        for result in (
            quiet_region(self.audio, 1000, 0.2, 0.5, "mild"),
            insert_pause(self.audio, 1000, 0.5, "mild"),
            rush_region(self.audio, 1000, 0.2, 0.5, "mild"),
        ):
            self.assertEqual(result[1]["provenance"], "synthetic_generator_truth_not_detector_input")
