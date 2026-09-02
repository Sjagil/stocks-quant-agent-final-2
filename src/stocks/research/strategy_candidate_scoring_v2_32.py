from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Mapping

import numpy as np

from .strategy_dna_v2_32 import StrategyDNA


@dataclass(frozen=True)
class StrategyPriorityScore:
    dna_id: str
    score: float
    feature_quality: float
    horizon_fit: float
    stability: float
    complexity_multiplier: float
    drift_multiplier: float
    research_only: bool = True
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _quality(row: Mapping[str, object]) -> tuple[float, float, float, float | None]:
    mean_ic = abs(float(row.get("mean_rank_ic", 0.0) or 0.0))
    icir = abs(float(row.get("rank_icir", 0.0) or 0.0))
    stability = float(row.get("stability_score", 0.0) or 0.0)
    half_life = row.get("decay_half_life")
    hl = float(half_life) if half_life is not None and np.isfinite(float(half_life)) else None
    quality = 0.40 * min(1.0, mean_ic / 0.05) + 0.30 * min(1.0, icir / 0.50) + 0.30 * np.clip(stability, 0.0, 1.0)
    return float(quality), mean_ic, stability, hl


def score_strategy_candidate(dna: StrategyDNA, governance: Mapping[str, Mapping[str, object]]) -> StrategyPriorityScore:
    qualities: list[float] = []
    stabilities: list[float] = []
    half_lives: list[float] = []
    psi_values: list[float] = []
    for feature_id in dna.all_feature_ids:
        row = governance.get(feature_id, {})
        q, _, stability, hl = _quality(row)
        qualities.append(q)
        stabilities.append(stability)
        if hl is not None and hl > 0:
            half_lives.append(hl)
        psi = row.get("psi")
        if psi is not None and np.isfinite(float(psi)):
            psi_values.append(max(0.0, float(psi)))
    feature_quality = float(np.mean(qualities)) if qualities else 0.0
    stability = float(np.mean(stabilities)) if stabilities else 0.0
    target = float(dna.horizon.target_bars)
    if half_lives:
        median_hl = float(np.median(half_lives))
        horizon_fit = float(math.exp(-abs(math.log(max(median_hl, 1e-9) / target))))
    else:
        horizon_fit = 0.50
    complexity_multiplier = float(math.exp(-0.08 * max(0, dna.complexity - 3)))
    mean_psi = float(np.mean(psi_values)) if psi_values else 0.0
    drift_multiplier = float(math.exp(-2.0 * mean_psi))
    score = feature_quality * (0.65 + 0.35 * horizon_fit) * (0.70 + 0.30 * stability) * complexity_multiplier * drift_multiplier
    return StrategyPriorityScore(
        dna_id=dna.dna_id,
        score=float(np.clip(score, 0.0, 1.0)),
        feature_quality=feature_quality,
        horizon_fit=horizon_fit,
        stability=stability,
        complexity_multiplier=complexity_multiplier,
        drift_multiplier=drift_multiplier,
    )


__all__ = ["StrategyPriorityScore", "score_strategy_candidate"]
