"""Audit two blind human word-boundary files before alignment scoring.

This module never manufactures a reference by averaging annotators. It checks
that both files cover the same predeclared words from the same audio and reports
boundary disagreements that require explicit adjudication.
"""
import argparse
import json
import math
import statistics
from pathlib import Path


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _validate(reference, name):
    if reference.get("evidence_type") != "human_manual":
        raise ValueError(f"{name} evidence_type must be human_manual")
    for field in ("audio_sha256", "annotation_method", "annotated_at", "annotator_id"):
        if not isinstance(reference.get(field), str) or not reference[field].strip():
            raise ValueError(f"{name} {field} is required")
    if reference.get("prediction_hidden") is not True:
        raise ValueError(f"{name} prediction_hidden must be true")
    duration = _number(reference.get("duration_seconds"), f"{name} duration_seconds")
    if duration <= 0:
        raise ValueError(f"{name} duration_seconds must be positive")
    words = reference.get("words")
    if not isinstance(words, list) or not words:
        raise ValueError(f"{name} needs a nonempty words array")
    indexed = {}
    for item in words:
        index = item.get("word_index")
        if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index in indexed:
            raise ValueError(f"{name} word_index must be a unique nonnegative integer")
        word = item.get("word")
        if not isinstance(word, str) or not word:
            raise ValueError(f"{name} word is required")
        start = _number(item.get("start_seconds"), f"{name} start_seconds")
        end = _number(item.get("end_seconds"), f"{name} end_seconds")
        if not 0 <= start < end <= duration:
            raise ValueError(f"{name} has an invalid boundary at index {index}")
        indexed[index] = (word, start, end)
    return indexed


def audit_annotations(first, second, tolerance_seconds=0.1):
    """Return inter-annotator boundary agreement and an adjudication queue."""
    tolerance = _number(tolerance_seconds, "tolerance_seconds")
    if tolerance <= 0:
        raise ValueError("tolerance_seconds must be positive")
    a = _validate(first, "first")
    b = _validate(second, "second")
    if first["annotator_id"] == second["annotator_id"]:
        raise ValueError("Annotator IDs must differ")
    if first["audio_sha256"] != second["audio_sha256"]:
        raise ValueError("Audio SHA256 values must match")
    if first["duration_seconds"] != second["duration_seconds"]:
        raise ValueError("Audio duration values must match")
    if set(a) != set(b):
        raise ValueError("Annotators must label the same predeclared word indexes")

    boundary_errors = []
    queue = []
    for index in sorted(a):
        aword, astart, aend = a[index]
        bword, bstart, bend = b[index]
        if aword != bword:
            raise ValueError(f"Word mismatch at index {index}")
        start_delta = abs(astart - bstart)
        end_delta = abs(aend - bend)
        boundary_errors.extend((start_delta, end_delta))
        if start_delta > tolerance or end_delta > tolerance:
            queue.append({"word_index": index, "word": aword,
                          "start_disagreement_seconds": start_delta,
                          "end_disagreement_seconds": end_delta})

    return {
        "audio_sha256": first["audio_sha256"],
        "annotators": [first["annotator_id"], second["annotator_id"]],
        "labelled_words": len(a),
        "boundary_median_disagreement_seconds": statistics.median(boundary_errors),
        "boundary_mean_disagreement_seconds": statistics.fmean(boundary_errors),
        "boundary_max_disagreement_seconds": max(boundary_errors),
        "boundaries_within_tolerance_fraction": sum(x <= tolerance for x in boundary_errors) / len(boundary_errors),
        "tolerance_seconds": tolerance,
        "adjudication_required": bool(queue),
        "adjudication_queue": queue,
        "claim_limit": "Agreement audits annotation reliability only; it is not model accuracy or delivery-quality evidence.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--tolerance", type=float, default=0.1)
    args = parser.parse_args()
    result = audit_annotations(json.loads(args.first.read_text()),
                               json.loads(args.second.read_text()), args.tolerance)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
