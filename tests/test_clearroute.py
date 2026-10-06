import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from clearroute.analyze import AnalysisConfig, analyze_frames, analyze_video
from clearroute.decision import record_decision
from clearroute.fixtures import ROUTE, reference, scenario, write_fixture_set
from clearroute.review import write_review


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


if __name__ == "__main__":
    unittest.main()
