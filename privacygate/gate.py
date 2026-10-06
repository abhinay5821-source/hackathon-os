"""CI gate for the fictional PrivacyGate access-control fixture."""
import argparse
import json
from pathlib import Path

from .audit import audit
from .core import RecordService, fictional_records


def run_gate(defect: str | None = None, output: Path | None = None) -> int:
    report = audit(RecordService(fictional_records(), defect))
    rendered = json.dumps(report, indent=2) + "\n"
    if output is not None:
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["passed"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail CI when fictional-record scope isolation regresses")
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    parser.add_argument(
        "--seed-defect",
        choices=["missing_student_scope", "missing_guardian_scope", "missing_teacher_scope"],
        help="deliberately introduce a known defect for local demonstrations",
    )
    args = parser.parse_args()
    raise SystemExit(run_gate(args.seed_defect, args.output))


if __name__ == "__main__":
    main()
