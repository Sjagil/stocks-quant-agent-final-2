from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd


def _prices(values: pd.Series | Iterable[float]) -> pd.Series:
    series = values.copy() if isinstance(values, pd.Series) else pd.Series(values, dtype=float)
    series = pd.to_numeric(series, errors="coerce").astype(float)
    if (series.dropna() <= 0).any():
        raise ValueError("prices must be strictly positive")
    return series


def _returns(values: pd.Series | Iterable[float]) -> pd.Series:
    series = values.copy() if isinstance(values, pd.Series) else pd.Series(values, dtype=float)
    return pd.to_numeric(series, errors="coerce").astype(float)


def simple_returns(prices: pd.Series | Iterable[float], periods: int = 1) -> pd.Series:
    if periods < 1:
        raise ValueError("periods must be >= 1")
    return _prices(prices).pct_change(periods=periods, fill_method=None)


def log_returns(prices: pd.Series | Iterable[float], periods: int = 1) -> pd.Series:
    if periods < 1:
        raise ValueError("periods must be >= 1")
    series = _prices(prices)
    return np.log(series / series.shift(periods))


def forward_simple_returns(
    prices: pd.Series | Iterable[float],
    horizons: Iterable[int],
) -> pd.DataFrame:
    series = _prices(prices)
    out = pd.DataFrame(index=series.index)
    seen: set[int] = set()
    for raw in horizons:
        horizon = int(raw)
        if horizon < 1:
            raise ValueError("forward horizons must be >= 1")
        if horizon in seen:
            continue
        seen.add(horizon)
        out[f"fwd_return_{horizon}"] = series.shift(-horizon) / series - 1.0
    return out


def wealth_index(
    returns: pd.Series | Iterable[float],
    *,
    initial_wealth: float = 1.0,
) -> pd.Series:
    if not math.isfinite(initial_wealth) or initial_wealth <= 0:
        raise ValueError("initial_wealth must be positive and finite")
    series = _returns(returns)
    if (series.dropna() <= -1.0).any():
        raise ValueError("simple returns cannot be <= -100%")
    return float(initial_wealth) * (1.0 + series.fillna(0.0)).cumprod()


def cumulative_return(returns: pd.Series | Iterable[float]) -> float:
    series = _returns(returns).dropna()
    if series.empty:
        return 0.0
    if (series <= -1.0).any():
        raise ValueError("simple returns cannot be <= -100%")
    return float((1.0 + series).prod() - 1.0)


def cagr_from_wealth(
    wealth: pd.Series | Iterable[float],
    *,
    years: float,
) -> float:
    if not math.isfinite(years) or years <= 0:
        raise ValueError("years must be positive and finite")
    series = pd.to_numeric(
        wealth.copy() if isinstance(wealth, pd.Series) else pd.Series(wealth, dtype=float),
        errors="coerce",
    ).dropna()
    if len(series) < 2 or float(series.iloc[0]) <= 0 or float(series.iloc[-1]) <= 0:
        raise ValueError("wealth needs at least two positive observations")
    return float((float(series.iloc[-1]) / float(series.iloc[0])) ** (1.0 / years) - 1.0)
