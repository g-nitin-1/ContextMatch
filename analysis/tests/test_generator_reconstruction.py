import unittest

from analysis.generator_reconstruction import (
    conditional_mode_accuracy,
    correlation_ratio,
)


class GeneratorReconstructionMetricTests(unittest.TestCase):
    def test_conditional_mode_accuracy(self) -> None:
        source = ["a", "a", "b", "b", "b"]
        target = ["x", "x", "x", "y", "y"]
        self.assertAlmostEqual(conditional_mode_accuracy(source, target), 0.8)

    def test_correlation_ratio_detects_group_separation(self) -> None:
        categories = ["a", "a", "b", "b"]
        separated = [0.0, 0.0, 10.0, 10.0]
        constant = [3.0, 3.0, 3.0, 3.0]
        self.assertAlmostEqual(correlation_ratio(categories, separated), 1.0)
        self.assertEqual(correlation_ratio(categories, constant), 0.0)


if __name__ == "__main__":
    unittest.main()
