"""Persist a minimal local reviewer decision without personal identifiers."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

DECISIONS = {"confirmed_obstruction", "dismissed", "needs_follow_up"}


def record_decision(result_path: Path, output_path: Path, decision: str, note: str = "") -> dict:
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of: {', '.join(sorted(DECISIONS))}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    record = {
        "source_result": result_path.name,
        "analysis_status": result.get("status"),
        "analysis_reason": result.get("reason"),
        "review_decision": decision,
        "note": note,
        "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "warning": "Local prototype record; no reviewer identity or automatic action.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Record a local ClearRoute review decision")
    parser.add_argument("result", type=Path)
    parser.add_argument("decision", choices=sorted(DECISIONS))
    parser.add_argument("--note", default="")
    parser.add_argument("--output", type=Path, default=Path("clearroute-decision.json"))
    args = parser.parse_args()
    record_decision(args.result, args.output, args.decision, args.note)
    print(args.output)


if __name__ == "__main__":
    main()
