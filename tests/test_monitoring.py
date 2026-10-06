import unittest

from shadowgauge.monitoring import DriftGate, psi


class MonitoringTests(unittest.TestCase):
    def test_psi_is_zero_for_identical_distributions(self):
        self.assertAlmostEqual(psi([0.1, 0.2, 0.8], [0.1, 0.2, 0.8]), 0.0)

    def test_psi_detects_shift(self):
        self.assertGreater(psi([0.9] * 20, [0.1] * 20), 1.0)

    def test_gate_requires_two_windows_and_cools_down(self):
        gate = DriftGate(threshold=0.2, consecutive_required=2, cooldown_windows=1)
        self.assertFalse(gate.evaluate(0.3))
        self.assertTrue(gate.evaluate(0.3))
        self.assertFalse(gate.evaluate(0.5))


if __name__ == "__main__":
    unittest.main()
