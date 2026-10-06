"""SQLite-backed event queue, grades, windows, and alerts."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS sampled_events (
  event_id TEXT PRIMARY KEY, ts TEXT NOT NULL, intent TEXT NOT NULL,
  question TEXT NOT NULL, context TEXT NOT NULL, response TEXT NOT NULL,
  inclusion_probability REAL NOT NULL, sample_reason TEXT NOT NULL,
  synthetic_failure INTEGER, status TEXT NOT NULL DEFAULT 'pending'
);
CREATE TABLE IF NOT EXISTS grades (
  event_id TEXT PRIMARY KEY REFERENCES sampled_events(event_id),
  groundedness REAL NOT NULL, unanswered INTEGER NOT NULL,
  harmful INTEGER NOT NULL, failure INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
  window_name TEXT NOT NULL, psi REAL NOT NULL, message TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        with self.connect() as db:
            db.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def enqueue(self, event: dict[str, Any], probability: float, reason: str) -> None:
        with self.connect() as db:
            db.execute(
                """INSERT OR IGNORE INTO sampled_events
                (event_id,ts,intent,question,context,response,inclusion_probability,
                 sample_reason,synthetic_failure) VALUES (?,?,?,?,?,?,?,?,?)""",
                (event["event_id"], event["ts"], event["intent"], event["question"],
                 event["context"], event["response"], probability, reason,
                 event.get("synthetic_failure")),
            )

    def pending(self, limit: int = 100) -> list[sqlite3.Row]:
        with self.connect() as db:
            return list(db.execute("SELECT * FROM sampled_events WHERE status='pending' ORDER BY ts LIMIT ?", (limit,)))

    def save_grade(self, event_id: str, groundedness: float, unanswered: bool,
                   harmful: bool, failure: bool) -> None:
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?,?)",
                       (event_id, groundedness, int(unanswered), int(harmful), int(failure)))
            db.execute("UPDATE sampled_events SET status='graded' WHERE event_id=?", (event_id,))

    def graded(self) -> list[sqlite3.Row]:
        with self.connect() as db:
            return list(db.execute("SELECT e.*, g.groundedness, g.failure FROM sampled_events e JOIN grades g USING(event_id) ORDER BY e.ts"))

    def add_alert(self, created_at: str, window: str, psi: float, message: str) -> None:
        with self.connect() as db:
            db.execute("INSERT INTO alerts(created_at,window_name,psi,message) VALUES (?,?,?,?)",
                       (created_at, window, psi, message))

    def summary(self) -> dict[str, Any]:
        with self.connect() as db:
            queued = db.execute("SELECT COUNT(*) FROM sampled_events").fetchone()[0]
            graded = db.execute("SELECT COUNT(*) FROM grades").fetchone()[0]
            failures = db.execute("SELECT COUNT(*) FROM grades WHERE failure=1").fetchone()[0]
            alerts = [dict(r) for r in db.execute("SELECT * FROM alerts ORDER BY id")]
        return {"sampled": queued, "graded": graded, "failures": failures, "alerts": alerts}

    def export_json(self) -> str:
        return json.dumps(self.summary(), indent=2)
