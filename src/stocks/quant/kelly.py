from __future__ import annotations

import numpy as np
import pandas as pd


def binary_kelly(*, win_probability: float, payoff_ratio: float) -> float:
    p = float(win_probability)
    b = float(payoff_ratio)
    if not 0.0 <= p <= 1.0 or b <= 0:
        raise ValueError("win_probability must be in [0,1] and payoff_ratio > 0")
    q = 1.0 - p
    return float((b * p - q) / b)


def continuous_kelly(*, expected_excess_return: float, variance: float) -> float:
    if variance <= 0:
        raise ValueError("variance must be positive")
    return float(expected_excess_return / variance)


def fractional_kelly(
    kelly_fraction: float,
    *,
    multiplier: float = 0.25,
    lower: float = 0.0,
    upper: float = 1.0,
) -> float:
    if multiplier < 0 or not lower <= upper:
        raise ValueError("invalid fractional Kelly bounds")
    return float(np.clip(float(kelly_fraction) * multiplier, lower, upper))


def multi_asset_kelly(
    expected_excess_returns: pd.Series,
    covariance: pd.DataFrame,
    *,
    fraction: float = 0.25,
    long_only: bool = True,
    max_total_weight: float = 1.0,
) -> pd.Series:
    if not 0.0 <= fraction <= 1.0 or not 0.0 < max_total_weight <= 1.0:
        raise ValueError("invalid fraction/max_total_weight")
    cov = covariance.astype(float)
    mu = pd.to_numeric(expected_excess_returns, errors="coerce").reindex(cov.columns)
    if mu.isna().any():
        raise ValueError("expected returns missing for covariance columns")
    weights = np.linalg.pinv(cov.to_numpy(dtype=float)) @ mu.to_numpy(dtype=float)
    weights = weights * fraction
    if long_only:
        weights = np.maximum(weights, 0.0)
    total = float(weights.sum())
    if total > max_total_weight and total > 0:
        weights = weights * (max_total_weight / total)
    return pd.Series(weights, index=cov.columns, dtype=float)
