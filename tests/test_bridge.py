import copy
import unittest

from shadowgauge.bridge import analyze_bridge, classify_product_drift
from shadowgauge.simulation import generate_bridge_overlap


class GraderBridgeTests(unittest.TestCase):
    def test_grader_only_shift_is_quarantined_not_product_incident(self):
        overlap = generate_bridge_overlap(grader_shift=True)
        bridge = analyze_bridge(overlap)
        decision = classify_product_drift(
            [row["old_score"] for row in overlap["rows"]],
            [row["new_score"] for row in overlap["rows"]], bridge)
        self.assertEqual(bridge["status"], "quarantine")
        self.assertGreater(decision["psi"], .2)
        self.assertEqual(decision["decision"], "MEASUREMENT_HOLD")
        self.assertFalse(decision["product_incident"])

    def test_compatible_bridge_allows_real_product_incident(self):
        overlap = generate_bridge_overlap(grader_shift=False)
        bridge = analyze_bridge(overlap)
        decision = classify_product_drift(
            [row["old_score"] for row in overlap["rows"]], [0.15] * 24, bridge)
        self.assertEqual(bridge["status"], "compatible")
        self.assertEqual(decision["decision"], "PRODUCT_INCIDENT")
        self.assertTrue(decision["product_incident"])

    def test_segment_breakdowns_and_coverage(self):
        bridge = analyze_bridge(generate_bridge_overlap(False), min_per_intent=6)
        self.assertEqual(set(bridge["segments"]), {"account", "billing", "returns", "shipping"})
        self.assertTrue(all(item["count"] == 6 for item in bridge["segments"].values()))
        self.assertTrue(all(debt == 0 for debt in bridge["coverage_debt"].values()))

    def test_thin_segment_quarantines(self):
        overlap = generate_bridge_overlap(False)
        overlap["rows"] = [r for r in overlap["rows"] if r["intent"] != "billing"] + [
            next(r for r in overlap["rows"] if r["intent"] == "billing")]
        bridge = analyze_bridge(overlap, min_per_intent=3)
        self.assertEqual(bridge["status"], "quarantine")
        self.assertIn("segment_coverage", {item["rule"] for item in bridge["violations"]})

    def test_duplicate_and_invalid_scores_rejected(self):
        overlap = generate_bridge_overlap(False)
        overlap["rows"].append(copy.deepcopy(overlap["rows"][0]))
        with self.assertRaises(ValueError):
            analyze_bridge(overlap)
        overlap = generate_bridge_overlap(False)
        overlap["rows"][0]["new_score"] = float("nan")
        with self.assertRaises(ValueError):
            analyze_bridge(overlap)

    def test_unknown_fields_and_same_version_rejected(self):
        overlap = generate_bridge_overlap(False)
        overlap["extra"] = True
        with self.assertRaises(ValueError):
            analyze_bridge(overlap)
        overlap = generate_bridge_overlap(False)
        overlap["new_grader"] = overlap["old_grader"]
        with self.assertRaises(ValueError):
            analyze_bridge(overlap)

    def test_thresholds_are_predeclared_and_validated(self):
        overlap = generate_bridge_overlap(False)
        with self.assertRaises(ValueError):
            analyze_bridge(overlap, maximum_mean_shift=-.1)
        bridge = analyze_bridge(overlap, maximum_mean_shift=.001)
        self.assertEqual(bridge["status"], "quarantine")


if __name__ == "__main__":
    unittest.main()
