from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ReturnMetrics:
    total_return: float
    max_drawdown: float
    sharpe: float
    profit_factor: float | None
    observations: int
    periods_per_year: float

    def to_dict(self) -> dict:
        return asdict(self)


def annualization_factor(index: pd.Index | None) -> float:
    if index is None:
        return 252.0

    try:
        timestamps = pd.DatetimeIndex(index)
    except Exception:
        return 252.0

    timestamps = timestamps.dropna().sort_values().unique()

    if len(timestamps) < 2:
        return 252.0

    elapsed_seconds = (
        timestamps[-1] - timestamps[0]
    ).total_seconds()

    if elapsed_seconds <= 0:
        return 252.0

    years = elapsed_seconds / (
        365.2425 * 24.0 * 60.0 * 60.0
    )

    years = max(
        years,
        1.0 / 365.2425,
    )

    empirical = (
        len(timestamps) - 1
    ) / years

    return float(
        max(empirical, 1.0)
    )


def summarize_returns(
    returns: pd.Series,
) -> ReturnMetrics:
    values = pd.Series(
        returns,
        copy=True,
        dtype=float,
    )

    values = (
        values
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    periods_per_year = annualization_factor(
        values.index
    )

    if values.empty:
        return ReturnMetrics(
            total_return=0.0,
            max_drawdown=0.0,
            sharpe=0.0,
            profit_factor=None,
            observations=0,
            periods_per_year=periods_per_year,
        )

    equity = (
        1.0 + values
    ).cumprod()

    peak = equity.cummax()

    drawdown = (
        1.0 -
        equity /
        peak.replace(0.0, np.nan)
    )

    total_return = float(
        equity.iloc[-1] - 1.0
    )

    max_drawdown = float(
        drawdown
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .max()
    )

    std = float(
        values.std(ddof=1)
    ) if len(values) > 1 else 0.0

    sharpe = (
        float(
            values.mean()
            / std
            * np.sqrt(periods_per_year)
        )
        if std > 0
        else 0.0
    )

    gains = float(
        values[values > 0].sum()
    )

    losses = float(
        -values[values < 0].sum()
    )

    profit_factor = (
        gains / losses
        if losses > 0
        else None
    )

    return ReturnMetrics(
        total_return=total_return,
        max_drawdown=max_drawdown,
        sharpe=sharpe,
        profit_factor=profit_factor,
        observations=len(values),
        periods_per_year=periods_per_year,
    )
