from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class AlphaEvidence:
    feature_id: str
    family: str
    raw_value: float
    normalized_value: float
    governance_status: str
    mean_rank_ic: float
    rank_icir: float
    stability_score: float
    regime_multiplier: float = 1.0
    freshness_multiplier: float = 1.0
    data_quality_multiplier: float = 1.0
    execution_authority: str = "NONE"

    def __post_init__(self) -> None:
        for field in ("regime_multiplier", "freshness_multiplier", "data_quality_multiplier"):
            value = float(getattr(self, field))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field} must be in [0,1]")
        if self.execution_authority != "NONE":
            raise ValueError("alpha evidence cannot grant execution authority")

    @property
    def predictive_weight(self) -> float:
        if self.governance_status != "PROMOTE_RESEARCH":
            return 0.0
        ic_strength = abs(float(self.mean_rank_ic))
        icir_strength = min(2.0, abs(float(self.rank_icir))) / 2.0 if np.isfinite(self.rank_icir) else 0.0
        return float(
            np.clip(
                ic_strength
                * (0.5 + 0.5 * icir_strength)
                * float(self.stability_score)
                * float(self.regime_multiplier)
                * float(self.freshness_multiplier)
                * float(self.data_quality_multiplier),
                0.0,
                1.0,
            )
        )

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["predictive_weight"] = self.predictive_weight
        return payload


def combine_alpha_evidence(
    evidence: list[AlphaEvidence] | tuple[AlphaEvidence, ...],
    *,
    redundancy_penalty: float = 0.0,
) -> dict[str, float | int]:
    if not 0.0 <= redundancy_penalty <= 1.0:
        raise ValueError("redundancy_penalty must be in [0,1]")
    active = [row for row in evidence if row.predictive_weight > 0.0 and np.isfinite(row.normalized_value)]
    if not active:
        return {"alpha_evidence_score": 0.0, "confidence": 0.0, "active_features": 0}
    weights = np.asarray([row.predictive_weight for row in active], dtype=float)
    values = np.asarray([row.normalized_value for row in active], dtype=float)
    score = float(np.average(values, weights=weights)) if weights.sum() > 0 else 0.0
    weighted_var = float(np.average((values - score) ** 2, weights=weights)) if weights.sum() > 0 else 1.0
    agreement = float(np.clip(1.0 / (1.0 + weighted_var), 0.0, 1.0))
    breadth = float(1.0 - np.exp(-len(active) / 4.0))
    confidence = float(np.clip(agreement * breadth * (1.0 - redundancy_penalty), 0.0, 1.0))
    return {
        "alpha_evidence_score": score,
        "confidence": confidence,
        "active_features": len(active),
    }


__all__ = ["AlphaEvidence", "combine_alpha_evidence"]
