"""Deterministic traffic sampling and population-aware estimators."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import inf
from typing import Iterable


@dataclass(frozen=True)
class SampleDecision:
    included: bool
    probability: float
    reason: str


class AdaptiveSampler:
    """Stable Bernoulli sampler that spends more coverage on new intents.

    Hash-based decisions make replays reproducible. The stored inclusion
    probability is essential: without it, oversampling rare intents biases the
    apparent quality rate.
    """

    def __init__(self, base_rate: float = 0.05, new_intent_rate: float = 0.35,
                 known_intents: Iterable[str] = (), daily_cap: int = 500) -> None:
        if not (0 < base_rate <= 1 and 0 < new_intent_rate <= 1):
            raise ValueError("sampling rates must be in (0, 1]")
        if daily_cap < 1:
            raise ValueError("daily_cap must be positive")
        self.base_rate = base_rate
        self.new_intent_rate = new_intent_rate
        self.known_intents = set(known_intents)
        self.daily_cap = daily_cap
        self.sampled_by_day: dict[str, int] = {}

    def decide(self, event_id: str, intent: str, day: str) -> SampleDecision:
        is_new = intent not in self.known_intents
        probability = self.new_intent_rate if is_new else self.base_rate
        reason = "new_intent" if is_new else "fixed_rate"
        if self.sampled_by_day.get(day, 0) >= self.daily_cap:
            return SampleDecision(False, probability, "daily_cap")
        draw = int(sha256(event_id.encode()).hexdigest()[:15], 16) / float(16**15)
        included = draw < probability
        if included:
            self.sampled_by_day[day] = self.sampled_by_day.get(day, 0) + 1
        return SampleDecision(included, probability, reason)


@dataclass(frozen=True)
class WeightedEstimate:
    raw_rate: float
    weighted_rate: float
    effective_sample_size: float
    sample_size: int
    clipped_weights: int


def estimate_failure_rate(rows: Iterable[tuple[bool, float]], max_weight: float = 20.0) -> WeightedEstimate:
    """Return raw and Hájek inverse-probability weighted failure rates."""
    materialized = list(rows)
    if not materialized:
        return WeightedEstimate(0.0, 0.0, 0.0, 0, 0)
    weighted_failures = total_weight = squared_weight = 0.0
    raw_failures = clipped = 0
    for failed, probability in materialized:
        if not 0 < probability <= 1:
            raise ValueError("inclusion probability must be in (0, 1]")
        raw_weight = 1.0 / probability
        weight = min(raw_weight, max_weight)
        clipped += int(weight < raw_weight)
        raw_failures += int(failed)
        weighted_failures += weight * int(failed)
        total_weight += weight
        squared_weight += weight * weight
    ess = total_weight**2 / squared_weight if squared_weight else 0.0
    return WeightedEstimate(
        raw_failures / len(materialized),
        weighted_failures / total_weight if total_weight else 0.0,
        ess,
        len(materialized),
        clipped,
    )
