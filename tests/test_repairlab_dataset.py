import json
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from repairlab.dataset import build_dataset


def write_wav(path, frequency):
    time = np.arange(16000, dtype=np.float32) / 16000
    samples = (0.2 * np.sin(2 * np.pi * frequency * time) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1); target.setsampwidth(2); target.setframerate(16000)
        target.writeframes(samples.tobytes())


def source(path, recording, speaker, text="text-a"):
    return {"audio_path": path, "transcript": "ONE TWO THREE",
            "words": [{"word": "ONE", "start_seconds": 0.10, "end_seconds": 0.25},
                      {"word": "TWO", "start_seconds": 0.35, "end_seconds": 0.50},
                      {"word": "THREE", "start_seconds": 0.60, "end_seconds": 0.80}],
            "metadata": {"source_url": "https://example.test/audio", "recording_id": recording,
                         "speaker_id": speaker, "text_id": text,
                         "rights_url": "https://example.test/rights", "rights_basis": "test fixture",
                         "reviewed_on": "2026-10-07", "baseline_rationale": "test fixture",
                         "redistribution_allowed": True, "derivatives_allowed": True,
                         "rights_review_complete": True}}


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.a = self.root / "a.wav"; self.b = self.root / "b.wav"
        write_wav(self.a, 220); write_wav(self.b, 330)
        self.sources = [source(self.a, "rec-a", "speaker-a", "text-a"),
                        source(self.b, "rec-b", "speaker-b", "text-b")]

    def tearDown(self):
        self.temp.cleanup()

    def test_writes_separate_manifests_and_word_safe_labels(self):
        output = self.root / "dataset"
        plans = [{"recording_id": "rec-a", "partition": "train", "corruption": "clean"},
                 {"recording_id": "rec-a", "partition": "train", "corruption": "quiet",
                  "severity": "medium", "method": "cosine_envelope",
                  "start_word_index": 1, "end_word_index": 3},
                 {"recording_id": "rec-b", "partition": "held_out", "corruption": "inserted_pause",
                  "severity": "mild", "at_word_index": 1}]
        build = build_dataset(output, self.sources, plans)
        detector = [json.loads(line) for line in (output / "detector_manifest.jsonl").read_text().splitlines()]
        truth = [json.loads(line) for line in (output / "evaluation_truth.jsonl").read_text().splitlines()]
        self.assertEqual(build["entries"], 3)
        self.assertEqual(len(list((output / "audio").glob("*.wav"))), 3)
        self.assertFalse(any("corruption" in row or "labels" in row for row in detector))
        quiet = next(row for row in truth if row["corruption"] == "quiet")
        self.assertEqual(quiet["labels"][0]["word_region"],
                         {"start_word_index": 1, "end_word_index": 3})
        self.assertEqual(quiet["labels"][0]["start_seconds"], 0.35)
        self.assertEqual(quiet["labels"][0]["end_seconds"], 0.8)
        self.assertEqual(quiet["labels"][0]["parameters"]["method"], "cosine_envelope")

    def test_build_is_reproducible_with_immutable_ids(self):
        plans = [{"recording_id": "rec-a", "partition": "train", "corruption": "rushed",
                  "severity": "mild", "start_word_index": 0, "end_word_index": 2}]
        first = self.root / "first"; second = self.root / "second"
        self.assertEqual(build_dataset(first, self.sources, plans), build_dataset(second, self.sources, plans))
        self.assertEqual((first / "detector_manifest.jsonl").read_bytes(),
                         (second / "detector_manifest.jsonl").read_bytes())
        self.assertEqual(next((first / "audio").iterdir()).read_bytes(),
                         next((second / "audio").iterdir()).read_bytes())

    def test_rejects_source_partition_leakage(self):
        plans = [{"recording_id": "rec-a", "partition": "train", "corruption": "clean"},
                 {"recording_id": "rec-a", "partition": "held_out", "corruption": "clean"}]
        with self.assertRaisesRegex(ValueError, "share a partition"):
            build_dataset(self.root / "dataset", self.sources, plans)

    def test_rejects_speaker_or_text_leakage_between_sources(self):
        leaking = [source(self.a, "rec-a", "same-speaker", "text-a"),
                   source(self.b, "rec-b", "same-speaker", "text-b")]
        plans = [{"recording_id": "rec-a", "partition": "train", "corruption": "clean"},
                 {"recording_id": "rec-b", "partition": "held_out", "corruption": "clean"}]
        with self.assertRaisesRegex(ValueError, "speaker_id"):
            build_dataset(self.root / "dataset", leaking, plans)

    def test_rejects_partial_word_regions_and_nonempty_output(self):
        bad = [{"recording_id": "rec-a", "partition": "train", "corruption": "quiet",
                "severity": "mild", "start_seconds": 0.1, "end_seconds": 0.2}]
        with self.assertRaises(ValueError):
            build_dataset(self.root / "dataset", self.sources, bad)
        occupied = self.root / "occupied"; occupied.mkdir(); (occupied / "x").write_text("x")
        with self.assertRaisesRegex(ValueError, "empty"):
            build_dataset(occupied, self.sources, [{"recording_id": "rec-a", "partition": "train",
                                                    "corruption": "clean"}])

    def test_negative_control_is_hidden_from_detector_manifest(self):
        output = self.root / "dataset"
        plans = [{"recording_id": "rec-a", "partition": "train",
                  "corruption": "control_global_gain", "variant": "lower"}]
        build_dataset(output, self.sources, plans)
        detector = json.loads((output / "detector_manifest.jsonl").read_text())
        truth = json.loads((output / "evaluation_truth.jsonl").read_text())
        self.assertNotIn("control", detector)
        self.assertNotIn("expected_flaw", detector)
        self.assertFalse(truth["expected_flaw"])
        self.assertEqual(truth["control"]["control_type"], "global_gain")

    def test_enforces_declared_held_out_corruption_method(self):
        plans = [{"recording_id": "rec-a", "partition": "train", "corruption": "quiet",
                  "method": "hard_attenuation", "severity": "mild",
                  "start_word_index": 0, "end_word_index": 1},
                 {"recording_id": "rec-b", "partition": "held_out", "corruption": "quiet",
                  "method": "cosine_envelope", "holdout_method": True, "severity": "mild",
                  "start_word_index": 0, "end_word_index": 1}]
        build_dataset(self.root / "valid", self.sources, plans)
        plans[0]["method"] = "cosine_envelope"
        with self.assertRaisesRegex(ValueError, "leaked"):
            build_dataset(self.root / "invalid", self.sources, plans)
