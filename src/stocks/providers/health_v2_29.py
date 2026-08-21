from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class ProviderHealthPolicy:
    ok_weight: float = 1.0
    empty_weight: float = 0.35
    unconfigured_weight: float = 0.0
    error_weight: float = 0.0

    def weight_for(self, state: str) -> float:
        normalized = str(state).upper()
        return {
            "OK": self.ok_weight,
            "EMPTY": self.empty_weight,
            "UNCONFIGURED": self.unconfigured_weight,
            "ERROR": self.error_weight,
        }.get(normalized, 0.0)


def provider_reliability_score(
    states: Mapping[str, int],
    *,
    policy: ProviderHealthPolicy | None = None,
) -> dict[str, float | int | str]:
    active = policy or ProviderHealthPolicy()
    counts = {str(state).upper(): max(0, int(count)) for state, count in states.items()}
    total = sum(counts.values())
    if total <= 0:
        return {
            "attempts": 0,
            "ok_rate": 0.0,
            "error_rate": 0.0,
            "empty_rate": 0.0,
            "reliability_score": 0.0,
            "status": "NO_OBSERVATIONS",
        }
    weighted = sum(active.weight_for(state) * count for state, count in counts.items()) / total
    ok_rate = counts.get("OK", 0) / total
    error_rate = counts.get("ERROR", 0) / total
    empty_rate = counts.get("EMPTY", 0) / total
    score = float(np.clip(weighted, 0.0, 1.0))
    status = "HEALTHY" if score >= 0.90 else "DEGRADED" if score >= 0.60 else "WEAK" if score >= 0.30 else "FAILED"
    return {
        "attempts": total,
        "ok_rate": float(ok_rate),
        "error_rate": float(error_rate),
        "empty_rate": float(empty_rate),
        "reliability_score": score,
        "status": status,
    }


def provider_health_table(summary: Mapping[str, Mapping[str, int]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for provider, states in sorted(summary.items()):
        rows.append({"provider": provider, **provider_reliability_score(states)})
    return sorted(rows, key=lambda row: (-float(row["reliability_score"]), str(row["provider"])))
