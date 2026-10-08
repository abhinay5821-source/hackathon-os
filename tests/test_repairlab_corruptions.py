import unittest

import numpy as np

from repairlab.corruptions import (flat_pitch_region, global_gain_control, global_vibrato_control,
                                   insert_pause, quiet_region, rush_region, smooth_quiet_region)
from repairlab.features import extract_frame_features


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

    def test_smooth_quiet_is_distinct_duration_preserving_method(self):
        hard, _ = quiet_region(self.audio, 1000, 0.2, 0.8, "medium")
        smooth, label = smooth_quiet_region(self.audio, 1000, 0.2, 0.8, "medium")
        self.assertEqual(len(smooth), len(self.audio))
        np.testing.assert_array_equal(smooth[:200], self.audio[:200])
        np.testing.assert_array_equal(smooth[800:], self.audio[800:])
        self.assertFalse(np.array_equal(smooth[200:800], hard[200:800]))
        self.assertEqual(label["parameters"]["method"], "cosine_envelope")

    def test_global_gain_control_has_no_flaw_claim(self):
        output, control = global_gain_control(self.audio * 0.5, 1000, "raise")
        self.assertGreater(np.max(np.abs(output)), np.max(np.abs(self.audio * 0.5)))
        self.assertFalse(control["expected_flaw"])
        self.assertEqual(control["parameters"]["gain_db"], 3.0)

    def test_global_gain_rejects_clipping_and_unknown_variant(self):
        with self.assertRaisesRegex(ValueError, "clip"):
            global_gain_control(self.audio, 1000, "raise")
        with self.assertRaisesRegex(ValueError, "variant"):
            global_gain_control(self.audio, 1000, "unknown")

    def test_vibrato_control_preserves_duration_and_has_no_flaw_claim(self):
        time = np.arange(16000, dtype=np.float32) / 16000
        speech_like = (0.3 * np.sin(2 * np.pi * 180 * time)).astype(np.float32)
        output, control = global_vibrato_control(speech_like, 16000, "subtle")
        self.assertEqual(len(output), len(speech_like))
        self.assertFalse(np.array_equal(output, speech_like))
        self.assertLessEqual(np.max(np.abs(output)), 1.0)
        self.assertFalse(control["expected_flaw"])
        self.assertEqual(control["control_type"], "global_pitch_vibrato")
        self.assertEqual(control["parameters"]["depth_cents"], 20.0)

    def test_vibrato_control_rejects_unknown_variant(self):
        with self.assertRaisesRegex(ValueError, "vibrato"):
            global_vibrato_control(self.audio, 1000, "unknown")

    def test_flat_pitch_preserves_duration_region_and_reduces_f0_spread(self):
        rate = 16000
        time = np.arange(rate * 2, dtype=np.float64) / rate
        instantaneous = 120.0 + 90.0 * time / time[-1]
        phase = 2.0 * np.pi * np.cumsum(instantaneous) / rate
        source = (0.3 * np.sin(phase)).astype(np.float32)
        output, label = flat_pitch_region(source, rate, 0.2, 1.8, "severe")
        self.assertEqual(len(output), len(source))
        np.testing.assert_array_equal(output[:3200], source[:3200])
        np.testing.assert_array_equal(output[28800:], source[28800:])
        before = extract_frame_features(source[3200:28800], rate)["f0_hz"]
        after = extract_frame_features(output[3200:28800], rate)["f0_hz"]
        before, after = before[np.isfinite(before)], after[np.isfinite(after)]
        self.assertLess(np.std(after), np.std(before))
        self.assertEqual(label["flaw_type"], "flat_pitch")
        self.assertEqual(label["parameters"]["strength"], 1.0)

    def test_flat_pitch_rejects_unvoiced_and_unknown_severity(self):
        silent = np.zeros(16000, dtype=np.float32)
        with self.assertRaisesRegex(ValueError, "voiced"):
            flat_pitch_region(silent, 16000, 0.1, 0.9, "medium")
        with self.assertRaisesRegex(ValueError, "severity"):
            flat_pitch_region(self.audio, 1000, 0.2, 0.8, "unknown")
