import unittest

from shadowgauge.sampling import AdaptiveSampler, estimate_failure_rate


class SamplingTests(unittest.TestCase):
    def test_decision_is_reproducible(self):
        one = AdaptiveSampler(0.2, 0.8, {"known"}).decide("same", "known", "2026-01-01")
        two = AdaptiveSampler(0.2, 0.8, {"known"}).decide("same", "known", "2026-01-01")
        self.assertEqual(one, two)

    def test_new_intent_probability_is_recorded(self):
        result = AdaptiveSampler(0.05, 0.4, {"known"}).decide("x", "new", "2026-01-01")
        self.assertEqual(result.probability, 0.4)
        self.assertEqual(result.reason, "new_intent")

    def test_weighting_corrects_skewed_sample(self):
        # 10 common failures sampled at 10%, 10 rare successes sampled at 100%.
        result = estimate_failure_rate([(True, 0.1)] * 10 + [(False, 1.0)] * 10)
        self.assertEqual(result.raw_rate, 0.5)
        self.assertAlmostEqual(result.weighted_rate, 100 / 110)
        self.assertLess(result.effective_sample_size, result.sample_size)

    def test_empty_estimate(self):
        self.assertEqual(estimate_failure_rate([]).sample_size, 0)

    def test_invalid_probability(self):
        with self.assertRaises(ValueError):
            estimate_failure_rate([(True, 0)])


if __name__ == "__main__":
    unittest.main()
