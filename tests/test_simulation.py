import json
import tempfile
import unittest
from pathlib import Path

from shadowgauge.cli import simulate


class SimulationTests(unittest.TestCase):
    def test_replay_produces_report_and_alert(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "demo.db"
            report_path = Path(directory) / "report.json"
            report = simulate(str(db), str(report_path), 800)
            self.assertGreater(report["sampled"], 0)
            self.assertEqual(report["sampled"], report["graded"])
            self.assertTrue(report["alert_fired"])
            self.assertEqual(json.loads(report_path.read_text())["graded"], report["graded"])


if __name__ == "__main__":
    unittest.main()
