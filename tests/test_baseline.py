import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from parcelproof.baseline import analyze
from parcelproof.fixtures import generate

class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=generate(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def run_case(self,name):
        return analyze(self.root/'packing.avi',self.root/(name+'.avi'),self.root/('out_'+name))
    def test_missing_requires_review_and_evidence(self):
        result=self.run_case('missing')
        self.assertEqual(result['status'],'review_required')
        self.assertEqual(len(result['changed_regions']),1)
        self.assertAlmostEqual(result['packing_seconds'],1.9)
        for file in result['evidence_frames']:
            self.assertIsNotNone(cv2.imread(str(self.root/'out_missing'/file)))
    def test_unchanged(self): self.assertEqual(self.run_case('unchanged')['status'],'no_discrepancy_observed')
    def test_occluded_abstains(self): self.assertEqual(self.run_case('occluded')['status'],'uncertain')
    def test_dark_abstains(self): self.assertEqual(self.run_case('poor_light')['status'],'uncertain')
    def test_missing_video_rejected(self):
        with self.assertRaises(ValueError): analyze(self.root/'none.avi',self.root/'packing.avi',self.root/'out')
    def test_same_video_rejected(self):
        with self.assertRaises(ValueError): analyze(self.root/'packing.avi',self.root/'packing.avi',self.root/'out')

if __name__=='__main__': unittest.main()
