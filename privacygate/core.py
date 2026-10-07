"""Small fictional school-record service used to test authorization regressions."""
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class Actor:
    actor_id: str
    role: str

@dataclass(frozen=True)
class StudentRecord:
    student_id: str
    guardian_id: str
    teacher_id: str
    attendance: int
    mark: int

class AccessDenied(Exception):
    pass

class RecordService:
    def __init__(self, records: list[StudentRecord], defect: str | None = None):
        if defect not in {None, "missing_student_scope", "missing_guardian_scope", "missing_teacher_scope"}:
            raise ValueError("unknown seeded defect")
        self.records = {record.student_id: record for record in records}
        self.defect = defect

    def read(self, actor: Actor, student_id: str) -> dict:
        record = self.records.get(student_id)
        if record is None:
            raise KeyError(student_id)
        allowed = actor.role == "principal"
        if actor.role == "student":
            allowed = self.defect == "missing_student_scope" or actor.actor_id == record.student_id
        elif actor.role == "guardian":
            allowed = self.defect == "missing_guardian_scope" or actor.actor_id == record.guardian_id
        elif actor.role == "teacher":
            allowed = self.defect == "missing_teacher_scope" or actor.actor_id == record.teacher_id
        if not allowed:
            raise AccessDenied
        return asdict(record)

def fictional_records() -> list[StudentRecord]:
    return [
        StudentRecord("student-a", "guardian-a", "teacher-red", 92, 81),
        StudentRecord("student-b", "guardian-b", "teacher-blue", 88, 76),
    ]
