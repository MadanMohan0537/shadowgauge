"""Reproducible synthetic traffic used for demos and validation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


INTENTS = ("billing", "shipping", "returns", "account")


def generate_events(count: int = 800, regression_at: int = 520) -> list[dict]:
    start = datetime(2026, 1, 5, tzinfo=timezone.utc)
    events = []
    for index in range(count):
        intent = INTENTS[index % len(INTENTS)]
        context = {
            "billing": "Invoices are available in Settings Billing for twelve months.",
            "shipping": "Standard shipping arrives within five business days.",
            "returns": "Unused items may be returned within thirty days with receipt.",
            "account": "Account recovery requires a verified email address.",
        }[intent]
        natural_failure = index % 37 == 0
        regression = index >= regression_at and intent in {"shipping", "returns"}
        failed = natural_failure or regression
        response = "I don't know." if failed else context
        events.append({
            "event_id": f"evt-{index:05d}",
            "ts": (start + timedelta(minutes=index)).isoformat(),
            "intent": intent,
            "question": f"What is the policy for {intent}?",
            "context": context,
            "response": response,
            "synthetic_failure": int(failed),
        })
    return events
