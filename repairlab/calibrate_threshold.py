"""Select a detector threshold on development data, then lock it for held-out scoring."""
import argparse
import json
import math
from pathlib import Path

from repairlab.batch_detect import _rows, detect_manifest
from repairlab.evaluate_detector import evaluate_with_baselines, score_records


def _index(rows, name):
    output = {}
    for row in rows:
        identifier = row.get("derivative_id") if isinstance(row, dict) else None
        if not isinstance(identifier, str) or not identifier or identifier in output:
            raise ValueError(f"{name} needs unique nonempty derivative_id values")
        output[identifier] = row
    return output


def _thresholds(values):
    if not values:
        raise ValueError("Require at least one candidate threshold")
    output = []
    for value in values:
        if (isinstance(value, bool) or not isinstance(value, (int, float)) or
                not math.isfinite(value) or value <= 0):
            raise ValueError("Thresholds must be positive finite numbers")
        output.append(float(value))
    if len(set(output)) != len(output):
        raise ValueError("Threshold candidates must be unique")
    return sorted(output)


def calibrate(pair_rows, pair_root, truth_rows, manifest_rows, candidates,
              iou_threshold=0.3, seed=17):
    """Tune on development only and report a separately scored held-out partition."""
    pairs, truth, manifest = (_index(pair_rows, "pairs"), _index(truth_rows, "truth"),
                              _index(manifest_rows, "manifest"))
    if not set(pairs) == set(truth) == set(manifest):
        raise ValueError("Pairs, truth and manifest must contain identical derivative IDs")
    partitions = {name: [] for name in ("development", "held_out")}
    for identifier, row in manifest.items():
        partition = row.get("partition")
        if partition in partitions:
            partitions[partition].append(identifier)
    if any(not identifiers for identifiers in partitions.values()):
        raise ValueError("Require nonempty development and held_out partitions")

    def subset(indexed, identifiers):
        return [indexed[identifier] for identifier in sorted(identifiers)]

    development_scores = []
    for threshold in _thresholds(candidates):
        ids = partitions["development"]
        predictions = detect_manifest(subset(pairs, ids), pair_root, threshold)
        metrics = score_records(subset(truth, ids), predictions, iou_threshold)
        development_scores.append({"threshold": threshold, "metrics": metrics})

    def objective(item):
        metrics = item["metrics"]
        f1 = metrics["region_f1"] if metrics["region_f1"] is not None else -1.0
        control_fp = (metrics["control_clip_false_positive_rate"]
                      if metrics["control_clip_false_positive_rate"] is not None else 1.0)
        return f1, -control_fp, item["threshold"]

    chosen = max(development_scores, key=objective)["threshold"]
    held_ids = partitions["held_out"]
    held_predictions = detect_manifest(subset(pairs, held_ids), pair_root, chosen)
    held_report = evaluate_with_baselines(subset(truth, held_ids), held_predictions,
                                          subset(manifest, held_ids), iou_threshold, seed)
    return {"schema": "repairlab-threshold-calibration-v1",
            "selection_partition": "development", "chosen_threshold": chosen,
            "candidate_results": development_scores, "held_out": held_report,
            "selection_rule": "max development F1, then lower control FP, then higher threshold",
            "limitations": ["Synthetic-label calibration does not establish perceptual validity.",
                            "The chosen value is valid only for the frozen pipeline and dataset."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pairs", type=Path)
    parser.add_argument("truth", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--candidates", type=float, nargs="+", default=[1.5, 2.0, 2.5, 3.0])
    parser.add_argument("--iou-threshold", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = calibrate(_rows(args.pairs), args.pairs.parent, _rows(args.truth),
                       _rows(args.manifest), args.candidates, args.iou_threshold, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output),
                      "chosen_threshold": report["chosen_threshold"]}))


if __name__ == "__main__":
    main()
