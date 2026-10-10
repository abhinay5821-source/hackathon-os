"""Evaluate the transparent detector with each declared feature group removed."""
import argparse
import json
from pathlib import Path

from repairlab.batch_detect import _rows, detect_manifest
from repairlab.evaluate_detector import evaluate_with_baselines, score_records
from repairlab.features import FEATURES


FEATURE_GROUPS = {
    "energy": ("energy_db",),
    "pitch": ("f0_hz",),
    "spectrum": ("spectral_centroid_hz", "zero_crossing_rate"),
    "timing": ("duration_seconds", "preceding_pause_seconds"),
}


def evaluate_ablations(pair_rows, pair_root, truth_rows, manifest_rows, threshold=2.5,
                       iou_threshold=0.3, seed=17):
    """Score full features and deterministic leave-one-group-out variants."""
    full_predictions = detect_manifest(pair_rows, pair_root, threshold, FEATURES)
    full = evaluate_with_baselines(truth_rows, full_predictions, manifest_rows,
                                   iou_threshold, seed)
    removed = {}
    for name, group in FEATURE_GROUPS.items():
        active = tuple(feature for feature in FEATURES if feature not in group)
        predictions = detect_manifest(pair_rows, pair_root, threshold, active)
        removed[name] = {"removed_features": list(group), "active_features": list(active),
                         "metrics": score_records(truth_rows, predictions, iou_threshold)}
    return {"schema": "repairlab-feature-ablation-v1", "threshold": float(threshold),
            "full": full, "leave_one_group_out": removed,
            "limitations": [
                "Ablations measure detector dependence, not perceptual or clinical importance.",
                "Synthetic-label results do not establish real-speech validity.",
            ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pairs", type=Path)
    parser.add_argument("truth", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--threshold", type=float, default=2.5)
    parser.add_argument("--iou-threshold", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate_ablations(_rows(args.pairs), args.pairs.parent, _rows(args.truth),
                                _rows(args.manifest), args.threshold, args.iou_threshold,
                                args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output),
                      "ablations": len(report["leave_one_group_out"])}))


if __name__ == "__main__":
    main()
