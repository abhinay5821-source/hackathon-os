import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from clearroute.demo import build_demo


class ClearRouteDemoTests(unittest.TestCase):
    def test_demo_builds_reviewable_synthetic_bundle(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = build_demo(root)
            self.assertEqual(receipt["dataset_kind"], "synthetic")
            self.assertEqual(receipt["status"], "review_required")
            self.assertIn("not real-camera validation", receipt["claim"])
            result = json.loads(Path(receipt["result"]).read_text(encoding="utf-8"))
            self.assertEqual(result["reason"], "persistent_route_obstruction")
            self.assertTrue(Path(receipt["evidence"]).is_file())
            review = Path(receipt["review"]).read_text(encoding="utf-8")
            self.assertIn("data:image/png;base64,", review)
            self.assertIn("human review", review.lower())


if __name__ == "__main__":
    unittest.main()
