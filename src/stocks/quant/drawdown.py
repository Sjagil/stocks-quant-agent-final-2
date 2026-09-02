from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


def _wealth(values: pd.Series | Iterable[float]) -> pd.Series:
    series = values.copy() if isinstance(values, pd.Series) else pd.Series(values, dtype=float)
    series = pd.to_numeric(series, errors="coerce").astype(float)
    if (series.dropna() <= 0).any():
        raise ValueError("wealth must be positive")
    return series


def drawdown_series(wealth: pd.Series | Iterable[float]) -> pd.Series:
    series = _wealth(wealth)
    high = series.cummax()
    return 1.0 - series / high


def max_drawdown(wealth: pd.Series | Iterable[float]) -> float:
    dd = drawdown_series(wealth).dropna()
    return 0.0 if dd.empty else float(dd.max())


def ulcer_index(wealth: pd.Series | Iterable[float]) -> float:
    dd = drawdown_series(wealth).dropna()
    return 0.0 if dd.empty else float(np.sqrt(np.mean(np.square(dd))))


def pain_index(wealth: pd.Series | Iterable[float]) -> float:
    dd = drawdown_series(wealth).dropna()
    return 0.0 if dd.empty else float(dd.mean())


def drawdown_velocity(
    wealth: pd.Series | Iterable[float],
    *,
    periods: int = 1,
) -> pd.Series:
    if periods < 1:
        raise ValueError("periods must be >= 1")
    return drawdown_series(wealth).diff(periods) / float(periods)


def recovery_ratio(
    *,
    current_wealth: float,
    previous_peak: float,
    trough: float,
) -> float:
    if previous_peak <= trough:
        raise ValueError("previous_peak must exceed trough")
    return float(np.clip((current_wealth - trough) / (previous_peak - trough), 0.0, 1.0))
