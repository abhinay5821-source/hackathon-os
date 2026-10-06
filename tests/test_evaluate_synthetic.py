import tempfile
import unittest
from parcelproof.evaluate_synthetic import evaluate


class SyntheticEvaluationTests(unittest.TestCase):
    def test_reports_all_declared_synthetic_cases(self):
        with tempfile.TemporaryDirectory() as workdir:
            report=evaluate(workdir)
        self.assertEqual(report['synthetic_cases'],9)
        self.assertEqual(report['correct'],9)
        self.assertEqual(report['failures'],[])


if __name__=='__main__': unittest.main()
