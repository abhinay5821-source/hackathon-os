"""Run RepairLab's detector over a declared set of audio/alignment pairs."""
import argparse
import json
import math
from pathlib import Path

from repairlab.analyze import analyze_pair


REQUIRED_PATHS = ("baseline_audio", "participant_audio", "baseline_alignment",
                  "participant_alignment")


def _rows(path):
    output = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            output.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {number} of {path}") from exc
    return output


def _safe_path(root, value, field):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a nonempty relative path")
    supplied = Path(value)
    if supplied.is_absolute():
        raise ValueError(f"{field} must be relative to the pair manifest")
    root = root.resolve()
    resolved = (root / supplied).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"{field} escapes the pair manifest directory")
    if not resolved.is_file():
        raise ValueError(f"{field} does not exist: {value}")
    return resolved


def detect_manifest(rows, root, threshold=2.5):
    """Create prediction records without loading labels or injection parameters."""
    if (isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or
            not math.isfinite(threshold) or threshold <= 0):
        raise ValueError("threshold must be a positive finite number")
    seen, output = set(), []
    for row in rows:
        identifier = row.get("derivative_id") if isinstance(row, dict) else None
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError("Pair manifest needs unique nonempty derivative_id values")
        seen.add(identifier)
        paths = {field: _safe_path(Path(root), row.get(field), field)
                 for field in REQUIRED_PATHS}
        baseline_alignment = json.loads(paths["baseline_alignment"].read_text())
        participant_alignment = json.loads(paths["participant_alignment"].read_text())
        result = analyze_pair(paths["baseline_audio"], paths["participant_audio"],
                              baseline_alignment, participant_alignment, threshold)
        output.append({"schema": "repairlab-detector-prediction-v1",
                       "derivative_id": identifier,
                       "threshold": float(result["comparison"]["threshold"]),
                       "regions": result["comparison"]["regions"]})
    return sorted(output, key=lambda item: item["derivative_id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pairs", type=Path)
    parser.add_argument("--threshold", type=float, default=2.5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    predictions = detect_manifest(_rows(args.pairs), args.pairs.parent, args.threshold)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n"
                                   for row in predictions))
    print(json.dumps({"output": str(args.output), "clips": len(predictions),
                      "flagged_regions": sum(len(row["regions"]) for row in predictions)}))


if __name__ == "__main__":
    main()
