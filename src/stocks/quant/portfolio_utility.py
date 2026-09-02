from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class UtilityPenalties:
    variance: float = 1.0
    expected_shortfall: float = 1.0
    drawdown: float = 1.0
    turnover: float = 0.0
    impact: float = 0.0
    concentration: float = 0.0

    def __post_init__(self) -> None:
        if any(float(value) < 0 for value in self.__dict__.values()):
            raise ValueError("utility penalties must be non-negative")


def concentration_hhi(weights: pd.Series | Iterable[float]) -> float:
    vector = np.asarray(
        weights.to_numpy(dtype=float) if isinstance(weights, pd.Series) else list(weights),
        dtype=float,
    )
    if (vector < -1e-12).any():
        raise ValueError("concentration HHI assumes long-only weights")
    return float(np.square(vector).sum())


def portfolio_utility(
    *,
    weights: pd.Series,
    expected_net_returns: pd.Series,
    covariance: pd.DataFrame,
    expected_shortfall: float = 0.0,
    drawdown_risk: float = 0.0,
    turnover: float = 0.0,
    impact: float = 0.0,
    penalties: UtilityPenalties | None = None,
) -> float:
    p = penalties or UtilityPenalties()
    columns = covariance.columns
    w = pd.to_numeric(weights, errors="coerce").reindex(columns).fillna(0.0).to_numpy(dtype=float)
    mu = pd.to_numeric(expected_net_returns, errors="coerce").reindex(columns)
    if mu.isna().any():
        raise ValueError("expected net returns incomplete")
    cov = covariance.reindex(index=columns, columns=columns).to_numpy(dtype=float)
    expected = float(w @ mu.to_numpy(dtype=float))
    variance = float(w @ cov @ w)
    return float(
        expected
        - p.variance * variance
        - p.expected_shortfall * max(0.0, float(expected_shortfall))
        - p.drawdown * max(0.0, float(drawdown_risk))
        - p.turnover * max(0.0, float(turnover))
        - p.impact * max(0.0, float(impact))
        - p.concentration * concentration_hhi(w)
    )
