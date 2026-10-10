"""Score predicted word boundaries against independently annotated references.

The evaluator accepts only records explicitly marked ``human_manual``.  That
field is a provenance assertion, not proof that a human created the labels;
review the annotation log before reporting these metrics.
"""
import argparse
import json
import math
import statistics
import re
from pathlib import Path


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _percentile(values, percentile):
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _verify_blind_manifest(reference, manifest):
    if manifest.get("format") != "repairlab-blind-annotation-v1":
        raise ValueError("Unsupported blind annotation manifest format")
    if manifest.get("prediction_included") is not False:
        raise ValueError("Blind annotation manifest must declare prediction_included false")
    if manifest.get("audio_sha256") != reference.get("audio_sha256"):
        raise ValueError("Manifest and reference audio_sha256 do not match")
    manifest_duration = _finite_number(manifest.get("duration_seconds"), "manifest duration_seconds")
    reference_duration = _finite_number(reference.get("duration_seconds"), "reference duration_seconds")
    if not math.isclose(manifest_duration, reference_duration, rel_tol=0, abs_tol=1e-6):
        raise ValueError("Manifest and reference duration_seconds do not match")
    selected = manifest.get("selected_words")
    if not isinstance(selected, list) or not selected:
        raise ValueError("Manifest selected_words must be nonempty")
    planned = [(item.get("word_index"), item.get("word")) for item in selected]
    labelled = [(item.get("word_index"), item.get("word")) for item in reference.get("words", [])]
    if planned != labelled:
        raise ValueError("Reference words do not exactly match the predeclared manifest selection")


def evaluate_alignment(prediction, reference, manifest=None):
    """Return boundary-error metrics for a manually labelled word subset."""
    if reference.get("evidence_type") != "human_manual":
        raise ValueError("Reference evidence_type must be human_manual")
    for field in ("audio_sha256", "annotation_method", "annotated_at"):
        if not isinstance(reference.get(field), str) or not reference[field].strip():
            raise ValueError(f"Reference {field} is required")
    reference_hash = reference["audio_sha256"].lower()
    prediction_hash = prediction.get("audio_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", reference_hash):
        raise ValueError("Reference audio_sha256 must be 64 lowercase hexadecimal characters")
    if not isinstance(prediction_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", prediction_hash):
        raise ValueError("Prediction audio_sha256 must be 64 lowercase hexadecimal characters")
    if prediction_hash != reference_hash:
        raise ValueError("Prediction and reference audio_sha256 do not match")
    if manifest is not None:
        _verify_blind_manifest(reference, manifest)
    predicted = prediction.get("words")
    labelled = reference.get("words")
    if not isinstance(predicted, list) or not predicted or not isinstance(labelled, list) or not labelled:
        raise ValueError("Prediction and reference need nonempty word arrays")
    duration = _finite_number(prediction.get("duration_seconds"), "duration_seconds")
    if duration <= 0:
        raise ValueError("duration_seconds must be positive")
    reference_duration = _finite_number(reference.get("duration_seconds"), "reference duration_seconds")
    if reference_duration <= 0:
        raise ValueError("reference duration_seconds must be positive")
    if not math.isclose(duration, reference_duration, rel_tol=0, abs_tol=1e-6):
        raise ValueError("Prediction and reference duration_seconds do not match")

    starts, ends = [], []
    seen = set()
    for item in labelled:
        index = item.get("word_index")
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(predicted) or index in seen:
            raise ValueError("Reference word_index must be unique and in range")
        seen.add(index)
        expected = predicted[index]
        if item.get("word") != expected.get("word"):
            raise ValueError(f"Word mismatch at index {index}")
        reference_start = _finite_number(item.get("start_seconds"), "reference start_seconds")
        reference_end = _finite_number(item.get("end_seconds"), "reference end_seconds")
        predicted_start = _finite_number(expected.get("start_seconds"), "predicted start_seconds")
        predicted_end = _finite_number(expected.get("end_seconds"), "predicted end_seconds")
        if not (0 <= reference_start < reference_end <= duration):
            raise ValueError(f"Invalid reference boundary at index {index}")
        if not (0 <= predicted_start < predicted_end <= duration):
            raise ValueError(f"Invalid predicted boundary at index {index}")
        starts.append(abs(predicted_start - reference_start))
        ends.append(abs(predicted_end - reference_end))

    boundaries = starts + ends
    return {
        "schema": "repairlab-human-alignment-score-v1",
        "labelled_words": len(labelled),
        "labelled_fraction": len(labelled) / len(predicted),
        "start_mae_seconds": statistics.fmean(starts),
        "end_mae_seconds": statistics.fmean(ends),
        "boundary_median_absolute_error_seconds": statistics.median(boundaries),
        "boundary_p95_absolute_error_seconds": _percentile(boundaries, 0.95),
        "boundary_max_absolute_error_seconds": max(boundaries),
        "boundaries_within_100ms_fraction": sum(error <= 0.1 for error in boundaries) / len(boundaries),
        "claim_limit": "Metrics cover only the independently labelled words in this recording; they do not validate delivery scoring.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prediction", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--manifest", type=Path,
                        help="Prediction-free annotation manifest used to predeclare the scored words")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text()) if args.manifest else None
    result = evaluate_alignment(json.loads(args.prediction.read_text()),
                                json.loads(args.reference.read_text()), manifest)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
