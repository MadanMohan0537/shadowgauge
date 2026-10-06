"""Distribution-shift monitoring with conservative alert gates."""

from __future__ import annotations

from dataclasses import dataclass
from math import log


def psi(baseline: list[float], current: list[float], bins: int = 5) -> float:
    """Population Stability Index over fixed [0, 1] score bins."""
    if not baseline or not current:
        return 0.0
    epsilon = 1e-6
    def proportions(values: list[float]) -> list[float]:
        counts = [0] * bins
        for value in values:
            idx = min(bins - 1, max(0, int(value * bins)))
            counts[idx] += 1
        return [max(epsilon, count / len(values)) for count in counts]
    expected, actual = proportions(baseline), proportions(current)
    return sum((a - e) * log(a / e) for e, a in zip(expected, actual))


@dataclass
class DriftGate:
    threshold: float = 0.2
    consecutive_required: int = 2
    cooldown_windows: int = 2
    streak: int = 0
    cooldown_remaining: int = 0

    def evaluate(self, score: float) -> bool:
        if self.cooldown_remaining:
            self.cooldown_remaining -= 1
            return False
        self.streak = self.streak + 1 if score >= self.threshold else 0
        if self.streak >= self.consecutive_required:
            self.streak = 0
            self.cooldown_remaining = self.cooldown_windows
            return True
        return False
