"""Background grading worker."""

from .grading import grade_response
from .store import Store


def run_batch(store: Store, limit: int = 100) -> int:
    rows = store.pending(limit)
    for row in rows:
        grade = grade_response(row["question"], row["context"], row["response"])
        store.save_grade(row["event_id"], grade.groundedness, grade.unanswered,
                         grade.harmful, grade.failure)
    return len(rows)
