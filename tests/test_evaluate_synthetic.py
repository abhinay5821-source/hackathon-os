import tempfile
import unittest
from parcelproof.evaluate_synthetic import evaluate


class SyntheticEvaluationTests(unittest.TestCase):
    def test_reports_rearrangement_false_alarm(self):
        with tempfile.TemporaryDirectory() as workdir:
            report=evaluate(workdir)
        self.assertEqual(report['synthetic_cases'],9)
        self.assertEqual(report['correct'],8)
        self.assertEqual(report['failures'][0]['case'],'rearranged')
        self.assertEqual(report['failures'][0]['actual'],'review_required')


if __name__=='__main__': unittest.main()
