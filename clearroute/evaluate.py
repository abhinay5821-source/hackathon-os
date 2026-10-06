"""Score labeled ClearRoute results without overstating synthetic evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

VALID_EXPECTED = {"obstruction", "clear"}
VALID_PREDICTED = {"review_required", "clear", "uncertain"}

def evaluate_manifest(manifest: dict, base: Path | None = None) -> dict:
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("manifest must contain at least one case")
    dataset_kind = manifest.get("dataset_kind")
    if dataset_kind not in {"synthetic", "real_camera"}:
        raise ValueError("dataset_kind must be synthetic or real_camera")
    base = base or Path(".")
    sessions: set[str] = set()
    tp = fp = tn = fn = uncertain = 0
    rows = []
    for case in cases:
        expected, session = case.get("expected"), case.get("session_id")
        if expected not in VALID_EXPECTED:
            raise ValueError(f"invalid expected label: {expected}")
        if not isinstance(session, str) or not session.strip():
            raise ValueError("every case needs a non-empty session_id")
        predicted = json.loads((base / case["result"]).read_text(encoding="utf-8")).get("status")
        if predicted not in VALID_PREDICTED:
            raise ValueError(f"invalid result status: {predicted}")
        sessions.add(session)
        if predicted == "uncertain": uncertain += 1
        elif expected == "obstruction" and predicted == "review_required": tp += 1
        elif expected == "obstruction": fn += 1
        elif predicted == "review_required": fp += 1
        else: tn += 1
        rows.append({"case_id": case.get("case_id"), "expected": expected, "predicted": predicted})
    total, obstruction_total, clear_total = len(cases), tp + fn, tn + fp
    return {
        "dataset_kind": dataset_kind, "case_count": total, "session_count": len(sessions),
        "counts": {"true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn, "uncertain": uncertain},
        "obstruction_recall": round(tp / obstruction_total, 4) if obstruction_total else None,
        "false_alert_rate": round(fp / clear_total, 4) if clear_total else None,
        "uncertain_rate": round(uncertain / total, 4),
        "determinate_coverage": round((total - uncertain) / total, 4),
        "cases": rows,
        "claim": "held-out real-camera evaluation" if dataset_kind == "real_camera" and manifest.get("held_out") is True else f"{dataset_kind} evaluation; not real-world validation",
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Score labeled ClearRoute result JSON files")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, default=Path("evaluation-report.json"))
    args = parser.parse_args()
    report = evaluate_manifest(json.loads(args.manifest.read_text(encoding="utf-8")), args.manifest.parent)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
