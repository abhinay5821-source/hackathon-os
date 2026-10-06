import unittest
from privacygate.audit import audit
from privacygate.core import AccessDenied, Actor, RecordService, fictional_records

class PrivacyGateTests(unittest.TestCase):
    def test_secure_fixture_enforces_role_isolation(self):
        service = RecordService(fictional_records())
        self.assertEqual(service.read(Actor("student-a", "student"), "student-a")["student_id"], "student-a")
        with self.assertRaises(AccessDenied):
            service.read(Actor("student-a", "student"), "student-b")
        with self.assertRaises(AccessDenied):
            service.read(Actor("guardian-a", "guardian"), "student-b")
        with self.assertRaises(AccessDenied):
            service.read(Actor("teacher-red", "teacher"), "student-b")

    def test_audit_passes_secure_fixture(self):
        report = audit(RecordService(fictional_records()))
        self.assertTrue(report["passed"])
        self.assertEqual((report["probe_count"], report["finding_count"]), (7, 0))
        self.assertEqual(report["fixture"], "fictional-only")

    def test_audit_catches_each_seeded_scope_defect(self):
        expected = {
            "missing_student_scope": "student-other",
            "missing_guardian_scope": "guardian-other",
            "missing_teacher_scope": "teacher-other",
        }
        for defect, probe in expected.items():
            with self.subTest(defect=defect):
                report = audit(RecordService(fictional_records(), defect))
                self.assertFalse(report["passed"])
                self.assertEqual(report["finding_count"], 1)
                self.assertEqual(report["findings"][0]["probe"], probe)

    def test_unknown_defect_is_rejected(self):
        with self.assertRaises(ValueError):
            RecordService(fictional_records(), "disable_all_auth")

if __name__ == "__main__":
    unittest.main()
