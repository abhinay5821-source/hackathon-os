"""Score a held-out partition only with a verified frozen rubric."""
import argparse
import json
from pathlib import Path

from repairlab.batch_detect import _rows, detect_manifest
from repairlab.evaluate_detector import evaluate_with_baselines
from repairlab.freeze_rubric import verify_rubric_config


def _index(rows, name):
    output = {}
    for row in rows:
        identifier = row.get("derivative_id") if isinstance(row, dict) else None
        if not isinstance(identifier, str) or not identifier or identifier in output:
            raise ValueError(f"{name} needs unique nonempty derivative_id values")
        output[identifier] = row
    return output


def score_held_out(pair_rows, pair_root, truth_rows, manifest_rows, config,
                   iou_threshold=0.3, seed=17):
    verify_rubric_config(config)
    pairs, truth, manifest = (_index(pair_rows, "pairs"), _index(truth_rows, "truth"),
                              _index(manifest_rows, "manifest"))
    if not set(pairs) == set(truth) == set(manifest):
        raise ValueError("Pairs, truth and manifest must contain identical derivative IDs")
    held_ids = sorted(identifier for identifier, row in manifest.items()
                      if row.get("partition") == "held_out")
    if not held_ids:
        raise ValueError("Require a nonempty held_out partition")
    held_pairs = [pairs[identifier] for identifier in held_ids]
    held_truth = [truth[identifier] for identifier in held_ids]
    held_manifest = [manifest[identifier] for identifier in held_ids]
    predictions = detect_manifest(held_pairs, pair_root, config["threshold"])
    report = evaluate_with_baselines(held_truth, predictions, held_manifest,
                                     iou_threshold, seed)
    return {"schema": "repairlab-frozen-held-out-score-v1",
            "partition": "held_out", "rubric_config_sha256": config["config_sha256"],
            "calibration_sha256": config["calibration_sha256"],
            "threshold": config["threshold"], "derivative_ids": held_ids,
            "report": report,
            "limitations": ["Synthetic-label performance does not establish listener or judge validity.",
                            "Results are valid only for the fingerprinted rubric and frozen dataset."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pairs", type=Path)
    parser.add_argument("truth", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("rubric", type=Path)
    parser.add_argument("--iou-threshold", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.rubric.read_text())
    result = score_held_out(_rows(args.pairs), args.pairs.parent, _rows(args.truth),
                            _rows(args.manifest), config, args.iou_threshold, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output),
                      "rubric_config_sha256": result["rubric_config_sha256"],
                      "held_out_records": len(result["derivative_ids"])}))


if __name__ == "__main__":
    main()
