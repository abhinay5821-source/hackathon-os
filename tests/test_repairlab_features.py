import unittest

import numpy as np

from repairlab.features import compare_word_features, extract_frame_features, summarize_words


def tone(frequency, seconds=1.0, amplitude=0.3, rate=16000):
    time = np.arange(round(seconds * rate), dtype=float) / rate
    return (amplitude * np.sin(2 * np.pi * frequency * time)).astype(np.float32)


def rows(energy_pattern, durations=None, pauses=None):
    durations = durations or [0.20] * len(energy_pattern)
    pauses = pauses or [0.10] * len(energy_pattern)
    output, cursor = [], 0.0
    for index, energy in enumerate(energy_pattern):
        cursor += pauses[index]
        output.append({"word": f"W{index}", "start_seconds": cursor,
                       "end_seconds": cursor + durations[index], "duration_seconds": durations[index],
                       "preceding_pause_seconds": pauses[index], "energy_db": energy,
                       "f0_hz": 180.0, "spectral_centroid_hz": 900.0,
                       "zero_crossing_rate": 0.05})
        cursor += durations[index]
    return output


class FeatureTests(unittest.TestCase):
    def test_tone_pitch_energy_and_centroid(self):
        features = extract_frame_features(tone(200))
        self.assertAlmostEqual(float(np.nanmedian(features["f0_hz"])), 200.0, delta=5.0)
        self.assertAlmostEqual(float(np.median(features["spectral_centroid_hz"])), 200.0, delta=15.0)
        louder = extract_frame_features(tone(200, amplitude=0.6))
        delta = np.median(louder["energy_db"]) - np.median(features["energy_db"])
        self.assertAlmostEqual(float(delta), 6.02, delta=0.15)

    def test_word_summaries_include_acoustic_and_timing_features(self):
        features = extract_frame_features(tone(180))
        words = [{"word": "ONE", "start_seconds": 0.10, "end_seconds": 0.30},
                 {"word": "TWO", "start_seconds": 0.45, "end_seconds": 0.75}]
        summary = summarize_words(features, words)
        self.assertEqual([row["word"] for row in summary], ["ONE", "TWO"])
        self.assertAlmostEqual(summary[1]["preceding_pause_seconds"], 0.15)
        self.assertAlmostEqual(summary[0]["f0_hz"], 180.0, delta=5.0)

    def test_global_gain_is_cancelled_by_within_speaker_normalization(self):
        baseline = rows([-20, -18, -16, -19, -17])
        participant = rows([-14, -12, -10, -13, -11])
        result = compare_word_features(baseline, participant)
        self.assertEqual(result["regions"], [])

    def test_local_energy_and_pause_outliers_have_grounded_explanations(self):
        baseline = rows([-20, -20, -20, -20, -20])
        participant = rows([-20, -20, -32, -20, -20], pauses=[0.1, 0.1, 0.5, 0.1, 0.1])
        result = compare_word_features(baseline, participant, threshold=2.5)
        region = next(item for item in result["regions"] if item["word"] == "W2")
        self.assertEqual((region["start_seconds"], region["end_seconds"]),
                         (participant[2]["start_seconds"], participant[2]["end_seconds"]))
        self.assertIn("energy_db", region["feature_deltas"])
        self.assertIn("preceding_pause_seconds", region["feature_deltas"])
        self.assertEqual(region["candidate_flaw_type"], "inserted_pause")
        self.assertTrue(all("normalized value minus baseline" in text for text in region["explanations"]))

    def test_rejects_mismatched_transcript_and_bad_audio(self):
        baseline = rows([-20] * 5); participant = rows([-20] * 5)
        participant[2]["word"] = "OTHER"
        with self.assertRaisesRegex(ValueError, "match"):
            compare_word_features(baseline, participant)
        with self.assertRaises(ValueError):
            extract_frame_features(np.array([1, 2], dtype=np.int16))

    def test_feature_subset_is_declared_and_validated(self):
        baseline = rows([-20, -20, -20, -20, -20])
        participant = rows([-20, -20, -32, -20, -20])
        result = compare_word_features(baseline, participant, active_features=["f0_hz"])
        self.assertEqual(result["active_features"], ["f0_hz"])
        self.assertEqual(result["regions"], [])
        with self.assertRaisesRegex(ValueError, "active_features"):
            compare_word_features(baseline, participant, active_features=[])


if __name__ == "__main__":
    unittest.main()
