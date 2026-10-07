"""Score timestamped flaw predictions against isolated evaluation truth."""
import argparse
import json
import math
import random
from pathlib import Path


def _jsonl(path):
    rows = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {number} of {path}") from exc
    return rows


def _region(item, type_field):
    if not isinstance(item, dict):
        raise ValueError("Regions must be objects")
    start, end, kind = item.get("start_seconds"), item.get("end_seconds"), item.get(type_field)
    if (isinstance(start, bool) or isinstance(end, bool) or
            not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or
            not math.isfinite(start) or not math.isfinite(end) or not 0 <= start < end):
        raise ValueError("Region boundaries must be finite, ordered nonnegative numbers")
    if not isinstance(kind, str) or not kind:
        raise ValueError(f"Region requires {type_field}")
    return {"start_seconds": float(start), "end_seconds": float(end), "type": kind}


def _index(rows, name):
    output = {}
    for row in rows:
        identifier = row.get("derivative_id") if isinstance(row, dict) else None
        if not isinstance(identifier, str) or not identifier or identifier in output:
            raise ValueError(f"{name} needs unique nonempty derivative_id values")
        output[identifier] = row
    return output


def temporal_iou(left, right):
    intersection = max(0.0, min(left["end_seconds"], right["end_seconds"]) -
                       max(left["start_seconds"], right["start_seconds"]))
    union = (max(left["end_seconds"], right["end_seconds"]) -
             min(left["start_seconds"], right["start_seconds"]))
    return intersection / union if union else 0.0


def score_records(truth_rows, prediction_rows, iou_threshold=0.3):
    """Return deterministic one-to-one temporal and type metrics."""
    if (isinstance(iou_threshold, bool) or not isinstance(iou_threshold, (int, float)) or
            not 0 < iou_threshold <= 1):
        raise ValueError("iou_threshold must be in (0, 1]")
    truth = _index(truth_rows, "truth")
    predictions = _index(prediction_rows, "predictions")
    if set(truth) != set(predictions):
        raise ValueError("Truth and predictions must contain identical derivative IDs")
    totals = {"truth_regions": 0, "predicted_regions": 0, "matched_regions": 0,
              "exact_type_matches": 0}
    overlaps, boundary_errors = [], []
    confusion = {}
    control_clips = control_false_positives = 0
    for identifier in sorted(truth):
        truth_row, prediction_row = truth[identifier], predictions[identifier]
        actual = [_region(item, "flaw_type") for item in truth_row.get("labels", [])]
        observed = [_region(item, "candidate_flaw_type")
                    for item in prediction_row.get("regions", [])]
        totals["truth_regions"] += len(actual)
        totals["predicted_regions"] += len(observed)
        if not actual:
            control_clips += 1
            control_false_positives += bool(observed)
        candidates = sorted(((temporal_iou(a, p), ai, pi)
                             for ai, a in enumerate(actual) for pi, p in enumerate(observed)),
                            reverse=True)
        used_actual, used_observed = set(), set()
        for overlap, ai, pi in candidates:
            if overlap < iou_threshold or ai in used_actual or pi in used_observed:
                continue
            used_actual.add(ai); used_observed.add(pi)
            totals["matched_regions"] += 1
            overlaps.append(overlap)
            error = (abs(actual[ai]["start_seconds"] - observed[pi]["start_seconds"]) +
                     abs(actual[ai]["end_seconds"] - observed[pi]["end_seconds"])) / 2
            boundary_errors.append(error)
            actual_type, predicted_type = actual[ai]["type"], observed[pi]["type"]
            confusion.setdefault(actual_type, {}).setdefault(predicted_type, 0)
            confusion[actual_type][predicted_type] += 1
            totals["exact_type_matches"] += actual_type == predicted_type
        for ai, item in enumerate(actual):
            if ai not in used_actual:
                confusion.setdefault(item["type"], {}).setdefault("__missed__", 0)
                confusion[item["type"]]["__missed__"] += 1
        for pi, item in enumerate(observed):
            if pi not in used_observed:
                confusion.setdefault("__none__", {}).setdefault(item["type"], 0)
                confusion["__none__"][item["type"]] += 1
    matched, predicted, actual = (totals["matched_regions"], totals["predicted_regions"],
                                  totals["truth_regions"])
    precision = matched / predicted if predicted else None
    recall = matched / actual if actual else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    return {"iou_threshold": float(iou_threshold), **totals,
            "region_precision": precision, "region_recall": recall, "region_f1": f1,
            "mean_temporal_iou_on_matches": sum(overlaps) / len(overlaps) if overlaps else None,
            "mean_boundary_error_seconds_on_matches": (sum(boundary_errors) / len(boundary_errors)
                                                       if boundary_errors else None),
            "exact_type_accuracy_on_matches": (totals["exact_type_matches"] / matched
                                                if matched else None),
            "control_clips": control_clips,
            "control_clip_false_positive_rate": (control_false_positives / control_clips
                                                  if control_clips else None),
            "confusion_matrix": {key: dict(sorted(value.items()))
                                 for key, value in sorted(confusion.items())}}


def evaluate_with_baselines(truth_rows, prediction_rows, manifest_rows, iou_threshold=0.3, seed=17):
    manifest = _index(manifest_rows, "manifest")
    truth = _index(truth_rows, "truth")
    if set(manifest) != set(truth):
        raise ValueError("Manifest and truth must contain identical derivative IDs")
    flaw_types = sorted({label["flaw_type"] for row in truth_rows for label in row.get("labels", [])})
    rng = random.Random(seed)
    no_flaw, full_clip, random_regions = [], [], []
    for identifier in sorted(truth):
        duration = manifest[identifier].get("duration_seconds")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError("Manifest durations must be positive")
        no_flaw.append({"derivative_id": identifier, "regions": []})
        full_clip.append({"derivative_id": identifier, "regions": [{"start_seconds": 0.0,
                          "end_seconds": duration, "candidate_flaw_type": "unknown"}]})
        width = duration * 0.25
        start = rng.random() * (duration - width)
        random_regions.append({"derivative_id": identifier, "regions": [{"start_seconds": start,
                               "end_seconds": start + width,
                               "candidate_flaw_type": rng.choice(flaw_types or ["unknown"])}]})
    return {"schema": "repairlab-detector-evaluation-v1", "seed": seed,
            "system": score_records(truth_rows, prediction_rows, iou_threshold),
            "baselines": {"predict_no_flaws": score_records(truth_rows, no_flaw, iou_threshold),
                          "predict_full_clip": score_records(truth_rows, full_clip, iou_threshold),
                          "random_quarter_clip": score_records(truth_rows, random_regions, iou_threshold)},
            "limitations": ["Synthetic generator truth does not establish perceptual validity.",
                            "Greedy IoU matching is deterministic but not globally optimal."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("truth", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--iou-threshold", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate_with_baselines(_jsonl(args.truth), _jsonl(args.predictions),
                                     _jsonl(args.manifest), args.iou_threshold, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output),
                      "matched_regions": report["system"]["matched_regions"]}))


if __name__ == "__main__":
    main()
