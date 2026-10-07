"""Analyze a transcript-matched baseline/participant pair for dashboard use."""
import argparse
import json
import math
from pathlib import Path

import numpy as np

from repairlab.audio_align import load_audio
from repairlab.features import compare_word_features, extract_frame_features, summarize_words


FRAME_FIELDS = ("frame_start_seconds", "frame_center_seconds", "energy_db", "f0_hz",
                "spectral_centroid_hz", "zero_crossing_rate")


def _alignment_words(alignment):
    if not isinstance(alignment, dict) or not isinstance(alignment.get("words"), list):
        raise ValueError("Alignment JSON must contain a words array")
    return alignment["words"]


def _serializable_frames(features):
    output = {}
    for field in FRAME_FIELDS:
        values = np.asarray(features[field], dtype=float)
        output[field] = [float(value) if math.isfinite(value) else None for value in values]
    return output


def analyze_pair(baseline_audio, participant_audio, baseline_alignment, participant_alignment,
                 threshold=2.5, active_features=None):
    """Return feature overlays, aligned-word summaries and grounded regions."""
    baseline_samples = load_audio(baseline_audio)
    participant_samples = load_audio(participant_audio)
    baseline_frames = extract_frame_features(baseline_samples)
    participant_frames = extract_frame_features(participant_samples)
    baseline_words = summarize_words(baseline_frames, _alignment_words(baseline_alignment))
    participant_words = summarize_words(participant_frames, _alignment_words(participant_alignment))
    comparison = compare_word_features(baseline_words, participant_words, threshold=threshold,
                                       active_features=active_features)
    return {
        "schema": "repairlab-pair-analysis-v1",
        "baseline": {"duration_seconds": len(baseline_samples) / 16000,
                     "frames": _serializable_frames(baseline_frames), "words": baseline_words},
        "participant": {"duration_seconds": len(participant_samples) / 16000,
                        "frames": _serializable_frames(participant_frames), "words": participant_words},
        "comparison": comparison,
        "uncertainty": [
            "Forced-alignment errors directly affect word regions and timing features.",
            "The development threshold is not calibrated on real delivery errors.",
            "Autocorrelation F0 can contain octave errors or missing unvoiced values.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline_audio", type=Path)
    parser.add_argument("participant_audio", type=Path)
    parser.add_argument("baseline_alignment", type=Path)
    parser.add_argument("participant_alignment", type=Path)
    parser.add_argument("--threshold", type=float, default=2.5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze_pair(args.baseline_audio, args.participant_audio,
                          json.loads(args.baseline_alignment.read_text()),
                          json.loads(args.participant_alignment.read_text()), args.threshold)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output),
                      "flagged_regions": len(result["comparison"]["regions"])}))


if __name__ == "__main__":
    main()
