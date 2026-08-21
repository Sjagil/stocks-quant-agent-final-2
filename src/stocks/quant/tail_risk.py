from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


def _series(values: pd.Series | Iterable[float]) -> pd.Series:
    raw = values.copy() if isinstance(values, pd.Series) else pd.Series(values, dtype=float)
    return pd.to_numeric(raw, errors="coerce").dropna().astype(float)


def _alpha(alpha: float) -> float:
    value = float(alpha)
    if not 0.5 < value < 1.0:
        raise ValueError("alpha must be in (0.5, 1)")
    return value


def historical_var(
    returns: pd.Series | Iterable[float],
    *,
    alpha: float = 0.95,
) -> float:
    series = _series(returns)
    if series.empty:
        return float("nan")
    cutoff = float(series.quantile(1.0 - _alpha(alpha)))
    return max(0.0, -cutoff)


def expected_shortfall(
    returns: pd.Series | Iterable[float],
    *,
    alpha: float = 0.95,
) -> float:
    series = _series(returns)
    if series.empty:
        return float("nan")
    cutoff = float(series.quantile(1.0 - _alpha(alpha)))
    tail = series[series <= cutoff]
    return max(0.0, -float(tail.mean())) if not tail.empty else max(0.0, -cutoff)


def lower_partial_moment(
    returns: pd.Series | Iterable[float],
    *,
    target: float = 0.0,
    order: int = 2,
) -> float:
    if order < 0:
        raise ValueError("order must be >= 0")
    series = _series(returns)
    if series.empty:
        return float("nan")
    shortfall = np.maximum(float(target) - series.to_numpy(dtype=float), 0.0)
    return float(np.mean(shortfall ** order))


def downside_deviation(
    returns: pd.Series | Iterable[float],
    *,
    target: float = 0.0,
) -> float:
    lpm2 = lower_partial_moment(returns, target=target, order=2)
    return float(np.sqrt(lpm2))


def omega_ratio(
    returns: pd.Series | Iterable[float],
    *,
    target: float = 0.0,
) -> float:
    series = _series(returns)
    if series.empty:
        return float("nan")
    upside = np.maximum(series.to_numpy(dtype=float) - target, 0.0).sum()
    downside = np.maximum(target - series.to_numpy(dtype=float), 0.0).sum()
    if downside <= 0:
        return float("inf") if upside > 0 else float("nan")
    return float(upside / downside)
