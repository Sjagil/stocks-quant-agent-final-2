from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd

from .drawdown import max_drawdown
from .returns import wealth_index
from .tail_risk import downside_deviation


def _series(values: pd.Series | Iterable[float]) -> pd.Series:
    raw = values.copy() if isinstance(values, pd.Series) else pd.Series(values, dtype=float)
    return pd.to_numeric(raw, errors="coerce").dropna().astype(float)


def sharpe_ratio(
    returns: pd.Series | Iterable[float],
    *,
    risk_free_per_period: float = 0.0,
    periods_per_year: float | None = None,
) -> float:
    series = _series(returns) - float(risk_free_per_period)
    if len(series) < 2:
        return float("nan")
    std = float(series.std(ddof=1))
    if std <= 1e-15:
        return float("nan")
    result = float(series.mean() / std)
    return result if periods_per_year is None else result * math.sqrt(periods_per_year)


def sortino_ratio(
    returns: pd.Series | Iterable[float],
    *,
    target_per_period: float = 0.0,
    periods_per_year: float | None = None,
) -> float:
    series = _series(returns)
    downside = downside_deviation(series, target=target_per_period)
    if downside <= 1e-15:
        return float("nan")
    result = float((series.mean() - target_per_period) / downside)
    return result if periods_per_year is None else result * math.sqrt(periods_per_year)


def calmar_ratio(
    returns: pd.Series | Iterable[float],
    *,
    periods_per_year: float,
) -> float:
    series = _series(returns)
    if series.empty or (series <= -1.0).any():
        return float("nan")
    years = len(series) / float(periods_per_year)
    total_growth = float((1.0 + series).prod())
    cagr = total_growth ** (1.0 / max(years, 1e-12)) - 1.0
    wealth = pd.concat(
        [
            pd.Series([1.0], index=[-1], dtype=float),
            wealth_index(series).reset_index(drop=True),
        ]
    )
    mdd = max_drawdown(wealth)
    return float("nan") if mdd <= 1e-15 else float(cagr / mdd)


def tracking_error(
    portfolio_returns: pd.Series | Iterable[float],
    benchmark_returns: pd.Series | Iterable[float],
    *,
    periods_per_year: float | None = None,
) -> float:
    p = _series(portfolio_returns).reset_index(drop=True)
    b = _series(benchmark_returns).reset_index(drop=True)
    n = min(len(p), len(b))
    if n < 2:
        return float("nan")
    active = p.iloc[:n] - b.iloc[:n]
    value = float(active.std(ddof=1))
    return value if periods_per_year is None else value * math.sqrt(periods_per_year)


def information_ratio(
    portfolio_returns: pd.Series | Iterable[float],
    benchmark_returns: pd.Series | Iterable[float],
    *,
    periods_per_year: float | None = None,
) -> float:
    p = _series(portfolio_returns).reset_index(drop=True)
    b = _series(benchmark_returns).reset_index(drop=True)
    n = min(len(p), len(b))
    if n < 2:
        return float("nan")
    active = p.iloc[:n] - b.iloc[:n]
    std = float(active.std(ddof=1))
    if std <= 1e-15:
        return float("nan")
    value = float(active.mean() / std)
    return value if periods_per_year is None else value * math.sqrt(periods_per_year)


def profit_factor(trade_returns: pd.Series | Iterable[float]) -> float:
    series = _series(trade_returns)
    gross_profit = float(series[series > 0].sum())
    gross_loss = abs(float(series[series < 0].sum()))
    if gross_loss <= 1e-15:
        return float("inf") if gross_profit > 0 else float("nan")
    return gross_profit / gross_loss


def trade_expectancy(trade_returns: pd.Series | Iterable[float]) -> float:
    series = _series(trade_returns)
    return float("nan") if series.empty else float(series.mean())


def payoff_ratio(trade_returns: pd.Series | Iterable[float]) -> float:
    series = _series(trade_returns)
    wins = series[series > 0]
    losses = series[series < 0].abs()
    if wins.empty or losses.empty:
        return float("nan")
    return float(wins.mean() / losses.mean())


def one_way_turnover(
    old_weights: Iterable[float],
    new_weights: Iterable[float],
) -> float:
    old = np.asarray(list(old_weights), dtype=float)
    new = np.asarray(list(new_weights), dtype=float)
    if old.shape != new.shape:
        raise ValueError("weight vectors must have equal shape")
    return float(0.5 * np.abs(new - old).sum())
