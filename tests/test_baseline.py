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
        page=(self.root/'out_missing'/'review.html').read_text()
        self.assertIn('human must review',page)
        self.assertNotIn(str(self.root),page)
    def test_unchanged(self): self.assertEqual(self.run_case('unchanged')['status'],'no_discrepancy_observed')
    def test_rearranged_same_items_not_flagged(self):
        result=self.run_case('rearranged')
        self.assertEqual(result['status'],'no_discrepancy_observed')
        self.assertEqual(result['item_signatures']['packing'],result['item_signatures']['returned'])
    def test_known_low_saturation_false_negative(self):
        result=self.run_case('missing_gray')
        self.assertEqual(result['status'],'no_discrepancy_observed')
        self.assertEqual(result['item_signatures']['packing'],result['item_signatures']['returned'])
    def test_occluded_abstains(self): self.assertEqual(self.run_case('occluded')['status'],'uncertain')
    def test_dark_abstains(self): self.assertEqual(self.run_case('poor_light')['status'],'uncertain')
    def test_localized_obstruction_abstains(self):
        result=self.run_case('localized_occlusion')
        self.assertEqual(result['status'],'uncertain')
        self.assertEqual(result['changed_regions'],[])
    def test_illumination_drift_abstains(self):
        self.assertEqual(self.run_case('illumination_drift')['status'],'uncertain')
    def test_camera_shift_abstains(self):
        result=self.run_case('camera_shift')
        self.assertEqual(result['status'],'uncertain')
        self.assertIn('Background changed; fixed-camera alignment unverified',result['uncertainty_reasons'])
    def test_unstable_tail_abstains(self):
        result=self.run_case('unstable')
        self.assertEqual(result['status'],'uncertain')
        self.assertIn('Final view is not stable',result['uncertainty_reasons'])
    def test_missing_video_rejected(self):
        with self.assertRaises(ValueError): analyze(self.root/'none.avi',self.root/'packing.avi',self.root/'out')
    def test_same_video_rejected(self):
        with self.assertRaises(ValueError): analyze(self.root/'packing.avi',self.root/'packing.avi',self.root/'out')

if __name__=='__main__': unittest.main()
