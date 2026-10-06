import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from clearroute.analyze import AnalysisConfig, analyze_frames, analyze_video
from clearroute.fixtures import ROUTE, reference, scenario, write_fixture_set


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

    def test_transient_passage_does_not_alert(self):
        self.assertEqual(self.result("transient_passage")["status"], "clear")

    def test_outside_route_is_ignored(self):
        self.assertEqual(self.result("outside_route")["status"], "clear")

    def test_poor_light_is_uncertain(self):
        result = self.result("poor_light")
        self.assertEqual((result["status"], result["reason"]), ("uncertain", "poor_light"))

    def test_global_occlusion_is_uncertain(self):
        result = self.result("global_occlusion")
        self.assertEqual(result["status"], "uncertain")

    def test_camera_shift_is_uncertain(self):
        result = self.result("camera_shift")
        self.assertEqual((result["status"], result["reason"]), ("uncertain", "camera_shift"))

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


if __name__ == "__main__":
    unittest.main()
