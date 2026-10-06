import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from clearroute.analyze import AnalysisConfig, analyze_frames, analyze_video
from clearroute.aws_publish import publish_review_event
from clearroute.decision import record_decision
from clearroute.fixtures import ROUTE, reference, scenario, write_fixture_set
from clearroute.review import write_review
from clearroute.server import make_handler


class ClearRouteTests(unittest.TestCase):
    def setUp(self):
        self.config = AnalysisConfig(route=ROUTE)

    def result(self, name):
        return analyze_frames(reference(), scenario(name), self.config)

    def test_clear_route(self):
        self.assertEqual(self.result("clear")["status"], "clear")

    def test_persistent_box_requires_review(self):
        result = self.result("persistent_box")
        self.assertEqual(result["status"], "review_required")
        self.assertIsNotNone(result["evidence_timestamp_seconds"])

    def test_stable_white_box_requires_review(self):
        self.assertEqual(self.result("white_box")["status"], "review_required")

    def test_colored_box_with_glare_requires_review(self):
        self.assertEqual(self.result("box_with_glare")["status"], "review_required")

    def test_transient_passage_does_not_alert(self):
        self.assertEqual(self.result("transient_passage")["status"], "clear")

    def test_intermittent_obstruction_does_not_meet_persistence_gate(self):
        result = self.result("intermittent_obstruction")
        self.assertEqual(result["status"], "clear")
        self.assertLess(result["longest_obstruction_frames"], self.config.persistence_frames)

    def test_outside_route_is_ignored(self):
        self.assertEqual(self.result("outside_route")["status"], "clear")

    def test_poor_light_is_uncertain(self):
        result = self.result("poor_light")
        self.assertEqual((result["status"], result["reason"]), ("uncertain", "poor_light"))

    def test_global_occlusion_is_uncertain(self):
        result = self.result("global_occlusion")
        self.assertEqual(result["status"], "uncertain")

    def test_gradual_dimming_becomes_uncertain_not_review_required(self):
        result = self.result("gradual_dimming")
        self.assertEqual(result["status"], "uncertain")

    def test_camera_shift_is_uncertain(self):
        result = self.result("camera_shift")
        self.assertEqual((result["status"], result["reason"]), ("uncertain", "camera_shift"))

    def test_slow_camera_drift_becomes_uncertain(self):
        result = self.result("slow_camera_drift")
        self.assertEqual((result["status"], result["reason"]), ("uncertain", "camera_shift"))

    def test_camera_vibration_is_uncertain(self):
        self.assertEqual(self.result("camera_vibration")["status"], "uncertain")

    def test_persistent_reflection_is_conservatively_uncertain(self):
        result = self.result("persistent_reflection")
        self.assertEqual((result["status"], result["reason"]), ("uncertain", "possible_reflection"))

    def test_empty_stream_is_uncertain(self):
        self.assertEqual(analyze_frames(reference(), [], self.config)["status"], "uncertain")

    def test_synthetic_shadow_is_not_an_obstruction(self):
        self.assertEqual(self.result("shadow")["status"], "clear")

    def test_video_cli_path_exports_timestamp_and_evidence_image(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture_set(root)
            output = root / "result.json"
            result = analyze_video(root / "reference.png", root / "persistent_box.avi", output, self.config)
            self.assertEqual(result["status"], "review_required")
            self.assertTrue(output.exists())
            self.assertTrue(output.with_suffix(".evidence.png").exists())

    def test_encoded_video_preserves_reflection_white_object_distinction(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture_set(root)
            reflection = analyze_video(root / "reference.png", root / "persistent_reflection.avi", root / "reflection.json", self.config)
            white_box = analyze_video(root / "reference.png", root / "white_box.avi", root / "white-box.json", self.config)
            glare = analyze_video(root / "reference.png", root / "box_with_glare.avi", root / "glare.json", self.config)
            self.assertEqual(reflection["status"], "uncertain")
            self.assertEqual(white_box["status"], "review_required")
            self.assertEqual(glare["status"], "review_required")

    def test_offline_review_page_embeds_evidence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture_set(root)
            result_path = root / "result.json"
            analyze_video(root / "reference.png", root / "persistent_box.avi", result_path, self.config)
            review_path = write_review(result_path, root / "review.html")
            page = review_path.read_text(encoding="utf-8")
            self.assertIn("data:image/png;base64,", page)
            self.assertIn("human review", page.lower())

    def test_reviewer_decision_record_has_no_identity_field(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            result_path = root / "result.json"
            result_path.write_text('{"status":"review_required","reason":"persistent_route_obstruction"}', encoding="utf-8")
            record_path = root / "decision.json"
            record = record_decision(result_path, record_path, "dismissed", "Synthetic reflection")
            self.assertEqual(record["review_decision"], "dismissed")
            self.assertNotIn("reviewer", record)
            self.assertTrue(record_path.exists())

    def test_reviewer_decision_rejects_unknown_value(self):
        with TemporaryDirectory() as directory:
            result_path = Path(directory) / "result.json"
            result_path.write_text('{"status":"clear"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                record_decision(result_path, Path(directory) / "decision.json", "auto_close")

    def test_aws_contract_encrypts_evidence_and_creates_pending_state(self):
        class FakeS3:
            def __init__(self): self.calls = []
            def put_object(self, **kwargs): self.calls.append(kwargs)
        class FakeDynamo:
            def __init__(self): self.calls = []
            def put_item(self, **kwargs): self.calls.append(kwargs)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            result = root / "result.json"
            result.write_text('{"status":"review_required","reason":"persistent_route_obstruction"}', encoding="utf-8")
            evidence = root / "evidence.png"; evidence.write_bytes(b"synthetic-png-placeholder")
            s3, dynamo = FakeS3(), FakeDynamo()
            receipt = publish_review_event(result, evidence, event_id="synthetic-001", bucket="private-evidence", table="review-events", s3=s3, dynamodb=dynamo)
            self.assertEqual(receipt["state"], "pending_review")
            self.assertEqual(len(s3.calls), 2)
            self.assertTrue(all(call["ServerSideEncryption"] == "AES256" for call in s3.calls))
            self.assertTrue(all("ACL" not in call for call in s3.calls))
            self.assertEqual(dynamo.calls[0]["ConditionExpression"], "attribute_not_exists(event_id)")

    def test_aws_contract_rejects_non_review_events(self):
        class NoCalls:
            def put_object(self, **kwargs): raise AssertionError("must not upload")
            def put_item(self, **kwargs): raise AssertionError("must not write")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "evidence.png"; evidence.write_bytes(b"x")
            for status in ("clear", "uncertain"):
                result = root / f"{status}.json"
                result.write_text(json.dumps({"status": status}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    publish_review_event(result, evidence, event_id=f"{status}-1", bucket="b", table="t", s3=NoCalls(), dynamodb=NoCalls())

    def test_cloudformation_storage_controls_are_declared(self):
        template = json.loads(Path("infra/clearroute.json").read_text(encoding="utf-8"))
        resources = template["Resources"]
        bucket = resources["EvidenceBucket"]["Properties"]
        self.assertTrue(all(bucket["PublicAccessBlockConfiguration"].values()))
        encryption = bucket["BucketEncryption"]["ServerSideEncryptionConfiguration"][0]
        self.assertEqual(encryption["ServerSideEncryptionByDefault"]["SSEAlgorithm"], "AES256")
        self.assertEqual(bucket["LifecycleConfiguration"]["Rules"][0]["Status"], "Enabled")
        table = resources["ReviewEvents"]["Properties"]
        self.assertTrue(table["PointInTimeRecoverySpecification"]["PointInTimeRecoveryEnabled"])
        self.assertTrue(table["SSESpecification"]["SSEEnabled"])
        self.assertTrue(table["TimeToLiveSpecification"]["Enabled"])

    def test_cloudformation_publisher_policy_is_write_only_and_scoped(self):
        template = json.loads(Path("infra/clearroute.json").read_text(encoding="utf-8"))
        statements = template["Resources"]["PublisherRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"]
        actions = {action for statement in statements for action in statement["Action"]}
        self.assertEqual(actions, {"s3:PutObject", "dynamodb:PutItem"})
        self.assertEqual(statements[0]["Resource"]["Fn::Sub"], "${EvidenceBucket.Arn}/events/*")

    def test_review_endpoint_requires_token_and_records_decision(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); result = root / "result.json"; decision = root / "decision.json"
            result.write_text('{"status":"review_required","reason":"persistent_route_obstruction"}', encoding="utf-8")
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(result, decision, "test-token"))
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with self.assertRaises(urllib.error.HTTPError) as missing: urllib.request.urlopen(base + "/review")
                self.assertEqual(missing.exception.code, 401)
                wrong = urllib.request.Request(base + "/review", headers={"Authorization": "Bearer wrong"})
                with self.assertRaises(urllib.error.HTTPError) as denied: urllib.request.urlopen(wrong)
                self.assertEqual(denied.exception.code, 401)
                request = urllib.request.Request(base + "/review", headers={"Authorization": "Bearer test-token"})
                with urllib.request.urlopen(request) as response: self.assertIn(b"ClearRoute human review", response.read())
                body = json.dumps({"decision": "dismissed", "note": "Synthetic test"}).encode()
                request = urllib.request.Request(base + "/decision", data=body, method="POST", headers={"Authorization": "Bearer test-token", "Content-Type": "application/json"})
                with urllib.request.urlopen(request) as response: self.assertEqual(response.status, 201)
                self.assertEqual(json.loads(decision.read_text())["review_decision"], "dismissed")
            finally:
                server.shutdown(); server.server_close(); thread.join()

    def test_review_endpoint_rejects_unknown_route_and_decision(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); result = root / "result.json"
            result.write_text('{"status":"review_required"}', encoding="utf-8")
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(result, root / "decision.json", "token"))
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                request = urllib.request.Request(base + "/other", headers={"Authorization": "Bearer token"})
                with self.assertRaises(urllib.error.HTTPError) as missing: urllib.request.urlopen(request)
                self.assertEqual(missing.exception.code, 404)
                body = json.dumps({"decision": "auto_close"}).encode()
                request = urllib.request.Request(base + "/decision", data=body, method="POST", headers={"Authorization": "Bearer token", "Content-Type": "application/json"})
                with self.assertRaises(urllib.error.HTTPError) as invalid: urllib.request.urlopen(request)
                self.assertEqual(invalid.exception.code, 400)
            finally:
                server.shutdown(); server.server_close(); thread.join()


if __name__ == "__main__":
    unittest.main()
