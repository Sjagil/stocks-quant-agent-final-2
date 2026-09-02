from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ForwardLabelSpec:
    horizons: tuple[int, ...] = (4, 8, 16, 24, 40)
    price_column: str = "close"

    def __post_init__(self) -> None:
        cleaned = tuple(sorted({int(value) for value in self.horizons}))
        if not cleaned or cleaned[0] < 1:
            raise ValueError("horizons must contain positive integers")
        object.__setattr__(self, "horizons", cleaned)


def build_forward_return_labels(
    frame: pd.DataFrame,
    *,
    spec: ForwardLabelSpec | None = None,
) -> pd.DataFrame:
    active = spec or ForwardLabelSpec()
    if active.price_column not in frame.columns:
        raise ValueError(f"missing price column: {active.price_column}")
    price = pd.to_numeric(frame[active.price_column], errors="coerce").astype(float)
    if (price.dropna() <= 0).any():
        raise ValueError("prices must be strictly positive")
    out = pd.DataFrame(index=frame.index)
    for horizon in active.horizons:
        out[f"fwd_return_{horizon}"] = price.shift(-horizon) / price - 1.0
        out[f"label_available_after_{horizon}_bars"] = float(horizon)
    return out


def forward_distribution_summary(
    labels: pd.Series | Iterable[float],
    *,
    quantiles: tuple[float, ...] = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95),
) -> dict[str, float | int]:
    series = pd.to_numeric(
        labels.copy() if isinstance(labels, pd.Series) else pd.Series(labels, dtype=float),
        errors="coerce",
    ).dropna()
    if series.empty:
        raise ValueError("labels are empty")
    if any(not 0.0 < q < 1.0 for q in quantiles):
        raise ValueError("quantiles must be in (0, 1)")
    result: dict[str, float | int] = {
        "observations": int(len(series)),
        "mean": float(series.mean()),
        "std": float(series.std(ddof=1)) if len(series) > 1 else 0.0,
        "probability_positive": float((series > 0).mean()),
    }
    for q in quantiles:
        result[f"q{int(round(q * 100)):02d}"] = float(series.quantile(q))
    return result


def robust_expected_return(
    *,
    mean_return: float,
    estimation_uncertainty: float,
    uncertainty_penalty: float = 1.0,
) -> float:
    if estimation_uncertainty < 0 or uncertainty_penalty < 0:
        raise ValueError("uncertainty inputs must be non-negative")
    return float(mean_return - uncertainty_penalty * estimation_uncertainty)


def quantile_opportunity_score(
    *,
    median_return: float,
    lower_quantile_return: float,
    expected_cost: float = 0.0,
    epsilon: float = 1e-9,
) -> float:
    downside = abs(min(float(lower_quantile_return), 0.0))
    return float((float(median_return) - float(expected_cost)) / (downside + float(epsilon)))
