import tempfile
import unittest
from pathlib import Path

from shadowgauge.grading import grade_response
from shadowgauge.store import Store
from shadowgauge.worker import run_batch


class GradingStoreTests(unittest.TestCase):
    def test_grounded_response_passes(self):
        grade = grade_response("When?", "Returns are accepted within thirty days.",
                               "Returns are accepted within thirty days.")
        self.assertFalse(grade.failure)

    def test_refusal_fails(self):
        self.assertTrue(grade_response("When?", "Within thirty days", "I don't know.").failure)

    def test_harmful_phrase_is_flagged(self):
        self.assertTrue(grade_response("How?", "Keep accounts safe", "Bypass authentication now").harmful)

    def test_worker_moves_queue_to_graded(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "test.db")
            store.enqueue({"event_id": "1", "ts": "2026-01-01", "intent": "returns",
                           "question": "When?", "context": "Return within thirty days",
                           "response": "Return within thirty days"}, 0.1, "fixed_rate")
            self.assertEqual(run_batch(store), 1)
            self.assertEqual(store.summary()["graded"], 1)
            self.assertEqual(run_batch(store), 0)


if __name__ == "__main__":
    unittest.main()
