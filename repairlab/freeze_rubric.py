"""Freeze a calibrated RepairLab rubric before held-out execution."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from repairlab.features import RUBRIC_GROUPS, RUBRIC_WEIGHTS


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _fingerprint(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def freeze_rubric(calibration, weights=None, severity_cap_multiple=2.0):
    if not isinstance(calibration, dict) or calibration.get("schema") != "repairlab-threshold-calibration-v1":
        raise ValueError("Require a RepairLab threshold calibration report")
    if calibration.get("selection_partition") != "development":
        raise ValueError("Rubric threshold must be selected on development data")
    threshold = calibration.get("chosen_threshold")
    if (isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or
            not math.isfinite(threshold) or threshold <= 0):
        raise ValueError("Calibration chosen_threshold must be positive and finite")
    if (isinstance(severity_cap_multiple, bool) or
            not isinstance(severity_cap_multiple, (int, float)) or
            not math.isfinite(severity_cap_multiple) or severity_cap_multiple <= 0):
        raise ValueError("severity_cap_multiple must be positive and finite")
    weights = dict(RUBRIC_WEIGHTS if weights is None else weights)
    if set(weights) != set(RUBRIC_GROUPS):
        raise ValueError("Weights must declare every rubric component exactly once")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or
           not math.isfinite(value) or value <= 0 for value in weights.values()):
        raise ValueError("Weights must be positive finite numbers")
    total = sum(weights.values())
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError("Weights must sum to 1")
    calibration_digest = _fingerprint(calibration)
    payload = {"schema": "repairlab-frozen-rubric-v1", "threshold": float(threshold),
               "weights": {name: float(weights[name]) for name in sorted(weights)},
               "severity_cap_multiple": float(severity_cap_multiple),
               "feature_groups": {name: list(RUBRIC_GROUPS[name]) for name in sorted(RUBRIC_GROUPS)},
               "selection_partition": "development",
               "calibration_sha256": calibration_digest,
               "status": "frozen_for_held_out_execution",
               "formula": "p=min(max(|delta|-threshold,0)/(severity_cap*threshold),1); component=100*(1-mean(p)); overall=weighted mean"}
    payload["config_sha256"] = _fingerprint(payload)
    return payload


def verify_rubric_config(config):
    if not isinstance(config, dict) or config.get("schema") != "repairlab-frozen-rubric-v1":
        raise ValueError("Require a frozen rubric config")
    expected = config.get("config_sha256")
    unsigned = {key: value for key, value in config.items() if key != "config_sha256"}
    if not isinstance(expected, str) or expected != _fingerprint(unsigned):
        raise ValueError("Frozen rubric fingerprint mismatch")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("calibration", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.calibration.read_text())
    config = freeze_rubric(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "config_sha256": config["config_sha256"]}))


if __name__ == "__main__":
    main()
