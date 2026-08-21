from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd


def _return_series(values: pd.Series | Iterable[float]) -> pd.Series:
    series = values.copy() if isinstance(values, pd.Series) else pd.Series(values, dtype=float)
    return pd.to_numeric(series, errors="coerce").astype(float)


def _ohlc(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"open", "high", "low", "close"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing OHLC columns: {sorted(missing)}")
    out = frame.copy()
    for column in required:
        out[column] = pd.to_numeric(out[column], errors="coerce").astype(float)
    valid = out[list(required)].dropna()
    if ((valid["high"] <= 0) | (valid["low"] <= 0) | (valid["open"] <= 0) | (valid["close"] <= 0)).any():
        raise ValueError("OHLC values must be positive")
    return out


def annualized_volatility(
    returns: pd.Series | Iterable[float],
    *,
    periods_per_year: float,
    ddof: int = 1,
) -> float:
    if not math.isfinite(periods_per_year) or periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    series = _return_series(returns).dropna()
    if len(series) <= ddof:
        return float("nan")
    return float(series.std(ddof=ddof) * math.sqrt(periods_per_year))


def ewma_volatility(
    returns: pd.Series | Iterable[float],
    *,
    decay: float = 0.94,
    periods_per_year: float | None = None,
) -> pd.Series:
    if not 0.0 < decay < 1.0:
        raise ValueError("decay must be in (0, 1)")
    series = _return_series(returns)
    variance = series.pow(2).ewm(alpha=1.0 - decay, adjust=False, min_periods=2).mean()
    vol = np.sqrt(variance)
    if periods_per_year is not None:
        if periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        vol = vol * math.sqrt(periods_per_year)
    return vol


def true_range(frame: pd.DataFrame) -> pd.Series:
    work = _ohlc(frame)
    previous_close = work["close"].shift(1)
    return pd.concat(
        [
            work["high"] - work["low"],
            (work["high"] - previous_close).abs(),
            (work["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    if period < 1:
        raise ValueError("period must be >= 1")
    return true_range(frame).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def _scale(value: float, periods_per_year: float | None) -> float:
    if periods_per_year is None:
        return value
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    return value * math.sqrt(periods_per_year)


def parkinson_volatility(
    frame: pd.DataFrame,
    *,
    periods_per_year: float | None = None,
) -> float:
    work = _ohlc(frame).dropna(subset=["high", "low"])
    if work.empty:
        return float("nan")
    variance = np.log(work["high"] / work["low"]).pow(2).mean() / (4.0 * math.log(2.0))
    return _scale(float(math.sqrt(max(0.0, variance))), periods_per_year)


def garman_klass_volatility(
    frame: pd.DataFrame,
    *,
    periods_per_year: float | None = None,
) -> float:
    work = _ohlc(frame).dropna(subset=["open", "high", "low", "close"])
    if work.empty:
        return float("nan")
    hl = np.log(work["high"] / work["low"])
    co = np.log(work["close"] / work["open"])
    variance = (0.5 * hl.pow(2) - (2.0 * math.log(2.0) - 1.0) * co.pow(2)).mean()
    return _scale(float(math.sqrt(max(0.0, variance))), periods_per_year)


def rogers_satchell_volatility(
    frame: pd.DataFrame,
    *,
    periods_per_year: float | None = None,
) -> float:
    work = _ohlc(frame).dropna(subset=["open", "high", "low", "close"])
    if work.empty:
        return float("nan")
    variance = (
        np.log(work["high"] / work["open"]) * np.log(work["high"] / work["close"])
        + np.log(work["low"] / work["open"]) * np.log(work["low"] / work["close"])
    ).mean()
    return _scale(float(math.sqrt(max(0.0, variance))), periods_per_year)
