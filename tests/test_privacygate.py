import unittest
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory
from http.server import ThreadingHTTPServer
from privacygate.audit import audit
from privacygate.core import AccessDenied, Actor, RecordService, fictional_records
from privacygate.server import make_handler
from privacygate.gate import run_gate

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

    def test_ci_gate_writes_report_and_fails_on_seeded_leak(self):
        with TemporaryDirectory() as directory:
            secure_path = Path(directory) / "secure.json"
            defect_path = Path(directory) / "defect.json"
            self.assertEqual(run_gate(output=secure_path), 0)
            self.assertTrue(json.loads(secure_path.read_text())["passed"])
            self.assertEqual(run_gate("missing_student_scope", defect_path), 1)
            defect_report = json.loads(defect_path.read_text())
            self.assertFalse(defect_report["passed"])
            self.assertEqual(defect_report["findings"][0]["probe"], "student-other")

    def test_http_api_allows_own_record_and_denies_other_student(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(RecordService(fictional_records())))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            own = urllib.request.Request(base + "/records/student-a", headers={"X-Actor-Id": "student-a", "X-Actor-Role": "student"})
            with urllib.request.urlopen(own) as response:
                payload = json.loads(response.read())
                self.assertEqual(payload["record"]["student_id"], "student-a")
                self.assertEqual(payload["fixture"], "fictional-only")
            other = urllib.request.Request(base + "/records/student-b", headers={"X-Actor-Id": "student-a", "X-Actor-Role": "student"})
            with self.assertRaises(urllib.error.HTTPError) as denied:
                urllib.request.urlopen(other)
            self.assertEqual(denied.exception.code, 403)
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_http_api_rejects_missing_actor_and_unknown_record(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(RecordService(fictional_records())))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with self.assertRaises(urllib.error.HTTPError) as missing:
                urllib.request.urlopen(base + "/records/student-a")
            self.assertEqual(missing.exception.code, 401)
            unknown = urllib.request.Request(base + "/records/student-x", headers={"X-Actor-Id": "principal-1", "X-Actor-Role": "principal"})
            with self.assertRaises(urllib.error.HTTPError) as absent:
                urllib.request.urlopen(unknown)
            self.assertEqual(absent.exception.code, 404)
        finally:
            server.shutdown(); server.server_close(); thread.join()

if __name__ == "__main__":
    unittest.main()
