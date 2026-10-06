"""Run an explicit role/access matrix against the fictional service."""
import argparse
import json
from dataclasses import asdict, dataclass
from .core import AccessDenied, Actor, RecordService, fictional_records

@dataclass(frozen=True)
class Probe:
    name: str
    actor: Actor
    target: str
    should_allow: bool

def probes() -> list[Probe]:
    return [
        Probe("student-own", Actor("student-a", "student"), "student-a", True),
        Probe("student-other", Actor("student-a", "student"), "student-b", False),
        Probe("guardian-linked", Actor("guardian-a", "guardian"), "student-a", True),
        Probe("guardian-other", Actor("guardian-a", "guardian"), "student-b", False),
        Probe("teacher-assigned", Actor("teacher-red", "teacher"), "student-a", True),
        Probe("teacher-other", Actor("teacher-red", "teacher"), "student-b", False),
        Probe("principal-any", Actor("principal-1", "principal"), "student-b", True),
    ]

def audit(service: RecordService) -> dict:
    rows, findings = [], []
    for probe in probes():
        try:
            service.read(probe.actor, probe.target)
            observed = "allowed"
        except AccessDenied:
            observed = "denied"
        expected = "allowed" if probe.should_allow else "denied"
        row = {"probe": probe.name, "actor": asdict(probe.actor), "target": probe.target, "expected": expected, "observed": observed}
        rows.append(row)
        if observed != expected:
            findings.append(row)
    return {"fixture": "fictional-only", "probe_count": len(rows), "finding_count": len(findings), "passed": not findings, "findings": findings, "probes": rows}

def main() -> None:
    parser = argparse.ArgumentParser(description="Audit fictional school-record access")
    parser.add_argument("--seed-defect", choices=["missing_student_scope", "missing_guardian_scope", "missing_teacher_scope"])
    args = parser.parse_args()
    print(json.dumps(audit(RecordService(fictional_records(), args.seed_defect)), indent=2))

if __name__ == "__main__":
    main()
