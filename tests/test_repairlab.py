import unittest
import numpy as np
from repairlab.align import align
from repairlab.provenance import validate_source, validate_split


def emissions(sequence, size=3):
    scores = np.full((len(sequence), size), -np.inf)
    for frame, token in enumerate(sequence):
        scores[frame, token] = 0
    return scores


def source(speaker="a", text="x", recording="1"):
    return dict(source_url="https://example.invalid/audio", recording_id=recording,
                speaker_id=speaker, text_id=text, rights_url="https://example.invalid/rights",
                rights_basis="TEST metadata only", reviewed_on="2026-10-07",
                baseline_rationale="TEST only; not an approved recording",
                redistribution_allowed=True, derivatives_allowed=True, rights_review_complete=True)


class AlignmentTests(unittest.TestCase):
    def test_known_token_boundaries(self):
        result = align(emissions([0, 1, 1, 0, 2, 0]), [1, 2], 3)
        self.assertEqual([(t["start_seconds"], t["end_seconds"]) for t in result["tokens"]], [(0.5, 1.5), (2, 2.5)])

    def test_repeated_token_requires_blank(self):
        result = align(emissions([1, 0, 1]), [1, 1], 3)
        self.assertEqual([t["start_seconds"] for t in result["tokens"]], [0, 2])
        with self.assertRaises(ValueError):
            align(emissions([1, 1]), [1, 1], 2)

    def test_wrong_transcript_rejected_when_no_supported_path(self):
        with self.assertRaises(ValueError):
            align(emissions([0, 1, 0]), [2], 3)

    def test_invalid_input(self):
        for duration in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                align(emissions([1]), [1], duration)
        with self.assertRaises(ValueError):
            align(emissions([1]), [0], 1)


class ProvenanceTests(unittest.TestCase):
    def test_unreviewed_or_no_derivatives_source_blocked(self):
        for field in ("rights_review_complete", "derivatives_allowed", "redistribution_allowed"):
            data = source(); data[field] = False
            with self.assertRaises(ValueError):
                validate_source(data)

    def test_missing_baseline_rationale_blocked(self):
        data = source(); del data["baseline_rationale"]
        with self.assertRaises(ValueError):
            validate_source(data)

    def test_holdout_rejects_shared_speaker_or_text(self):
        for data in (source("a", "y", "2"), source("b", "x", "2")):
            with self.assertRaises(ValueError):
                validate_split([source()], [data])
        validate_split([source()], [source("b", "y", "2")])


if __name__ == "__main__":
    unittest.main()
