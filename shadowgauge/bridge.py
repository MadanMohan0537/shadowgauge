"""Frozen-overlap analysis for safe grader version changes."""

from __future__ import annotations

from collections import defaultdict
import math

from .monitoring import psi


def _score(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{label} must be finite and between 0 and 1")
    return value


def analyze_bridge(overlap: dict, *, min_per_intent: int = 3,
                   maximum_mean_shift: float = 0.08,
                   maximum_flip_rate: float = 0.10,
                   pass_threshold: float = 0.5) -> dict:
    """Compare old/new graders on the same immutable, segmented examples."""
    if not isinstance(overlap, dict) or set(overlap) != {
            "schema_version", "old_grader", "new_grader", "rows"}:
        raise ValueError("overlap requires schema_version, grader versions and rows")
    if overlap["schema_version"] != 1:
        raise ValueError("overlap schema_version must be 1")
    for field in ("old_grader", "new_grader"):
        if not isinstance(overlap[field], str) or not overlap[field].strip():
            raise ValueError("grader versions must be nonempty")
    if overlap["old_grader"] == overlap["new_grader"]:
        raise ValueError("old and new grader versions must differ")
    if isinstance(min_per_intent, bool) or not isinstance(min_per_intent, int) or min_per_intent < 1:
        raise ValueError("min_per_intent must be a positive integer")
    for value, label in ((maximum_mean_shift, "maximum_mean_shift"),
                         (maximum_flip_rate, "maximum_flip_rate"),
                         (pass_threshold, "pass_threshold")):
        _score(value, label)
    rows = overlap["rows"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("overlap rows must be a nonempty list")
    seen, cleaned = set(), []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"event_id", "intent", "old_score", "new_score"}:
            raise ValueError("each overlap row must contain exact supported fields")
        if not isinstance(row["event_id"], str) or not row["event_id"].strip() or row["event_id"] in seen:
            raise ValueError("overlap event IDs must be nonempty and unique")
        if not isinstance(row["intent"], str) or not row["intent"].strip():
            raise ValueError("overlap intent must be nonempty")
        seen.add(row["event_id"])
        cleaned.append({**row, "old_score": _score(row["old_score"], "old_score"),
                        "new_score": _score(row["new_score"], "new_score")})

    def metrics(items: list[dict]) -> dict:
        deltas = [row["new_score"] - row["old_score"] for row in items]
        flips = [((row["old_score"] >= pass_threshold)
                  != (row["new_score"] >= pass_threshold)) for row in items]
        return {
            "count": len(items),
            "mean_old": sum(row["old_score"] for row in items) / len(items),
            "mean_new": sum(row["new_score"] for row in items) / len(items),
            "mean_shift": sum(deltas) / len(deltas),
            "mean_absolute_shift": sum(abs(delta) for delta in deltas) / len(deltas),
            "classification_flip_rate": sum(flips) / len(flips),
        }

    grouped = defaultdict(list)
    for row in cleaned:
        grouped[row["intent"]].append(row)
    segments = {intent: metrics(items) for intent, items in sorted(grouped.items())}
    coverage_debt = {intent: max(0, min_per_intent - item["count"])
                     for intent, item in segments.items()}
    violations = []
    for intent, item in segments.items():
        if coverage_debt[intent]:
            violations.append({"rule": "segment_coverage", "intent": intent,
                               "debt": coverage_debt[intent]})
        if abs(item["mean_shift"]) > maximum_mean_shift:
            violations.append({"rule": "mean_shift", "intent": intent,
                               "observed": item["mean_shift"]})
        if item["classification_flip_rate"] > maximum_flip_rate:
            violations.append({"rule": "classification_flip", "intent": intent,
                               "observed": item["classification_flip_rate"]})
    overall = metrics(cleaned)
    if abs(overall["mean_shift"]) > maximum_mean_shift:
        violations.append({"rule": "mean_shift", "intent": "all",
                           "observed": overall["mean_shift"]})
    if overall["classification_flip_rate"] > maximum_flip_rate:
        violations.append({"rule": "classification_flip", "intent": "all",
                           "observed": overall["classification_flip_rate"]})
    return {
        "old_grader": overlap["old_grader"], "new_grader": overlap["new_grader"],
        "status": "compatible" if not violations else "quarantine",
        "thresholds": {"minimum_per_intent": min_per_intent,
                       "maximum_mean_shift": maximum_mean_shift,
                       "maximum_flip_rate": maximum_flip_rate,
                       "pass_threshold": pass_threshold},
        "overall": overall, "segments": segments,
        "coverage_debt": coverage_debt, "violations": violations,
        "limitation": "Overlap compatibility is descriptive and may miss unseen intents.",
    }


def classify_product_drift(baseline: list[float], current: list[float],
                           bridge: dict, *, psi_threshold: float = 0.2) -> dict:
    """Keep incompatible measurement changes out of product incidents."""
    score = psi(baseline, current)
    if bridge.get("status") != "compatible":
        return {"decision": "MEASUREMENT_HOLD", "product_incident": False,
                "psi": score, "reason": "grader versions are not comparable"}
    incident = score >= psi_threshold
    return {"decision": "PRODUCT_INCIDENT" if incident else "STABLE",
            "product_incident": incident, "psi": score,
            "reason": "comparable grader bridge; product distribution evaluated"}
