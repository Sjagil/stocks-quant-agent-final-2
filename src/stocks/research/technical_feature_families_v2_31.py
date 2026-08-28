from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _numeric(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").astype(float)


def rolling_log_trend(close: pd.Series, *, window: int = 20) -> pd.DataFrame:
    """Causal rolling OLS statistics for log(close) ~ intercept + time."""
    if window < 3:
        raise ValueError("window must be >= 3")
    values = _numeric(close)
    logp = np.log(values.where(values > 0.0))
    x = np.arange(window, dtype=float)
    x_centered = x - x.mean()
    sxx = float(np.dot(x_centered, x_centered))

    def stats(array: np.ndarray) -> tuple[float, float, float]:
        if not np.all(np.isfinite(array)):
            return (np.nan, np.nan, np.nan)
        y = array.astype(float)
        y_centered = y - y.mean()
        slope = float(np.dot(x_centered, y_centered) / sxx)
        fitted = y.mean() + slope * x_centered
        residual = y - fitted
        sst = float(np.dot(y_centered, y_centered))
        sse = float(np.dot(residual, residual))
        r2 = 1.0 - sse / sst if sst > 1e-18 else 0.0
        dof = window - 2
        if dof <= 0:
            tstat = np.nan
        else:
            mse = sse / dof
            se = math.sqrt(max(mse, 0.0) / sxx) if sxx > 0 else np.nan
            tstat = slope / se if se and np.isfinite(se) and se > 1e-18 else np.nan
        return slope, float(np.clip(r2, 0.0, 1.0)), float(tstat)

    slope = pd.Series(np.nan, index=values.index, dtype=float)
    r2 = slope.copy()
    tstat = slope.copy()
    raw = logp.to_numpy(dtype=float)
    for end in range(window - 1, len(raw)):
        s, r, t = stats(raw[end - window + 1 : end + 1])
        slope.iloc[end] = s
        r2.iloc[end] = r
        tstat.iloc[end] = t
    return pd.DataFrame({"slope": slope, "r2": r2, "tstat": tstat})


def kaufman_efficiency_ratio(close: pd.Series, *, window: int = 20) -> pd.Series:
    if window < 2:
        raise ValueError("window must be >= 2")
    values = _numeric(close)
    direction = (values - values.shift(window)).abs()
    path = values.diff().abs().rolling(window, min_periods=window).sum()
    ratio = direction / path.replace(0.0, np.nan)
    return ratio.clip(0.0, 1.0)


def risk_adjusted_momentum(close: pd.Series, *, window: int = 20) -> pd.Series:
    if window < 2:
        raise ValueError("window must be >= 2")
    values = _numeric(close)
    log_ret = np.log(values / values.shift(1))
    momentum = np.log(values / values.shift(window))
    vol = log_ret.rolling(window, min_periods=window).std(ddof=0) * math.sqrt(window)
    return momentum / vol.replace(0.0, np.nan)


def relative_strength(
    close: pd.Series,
    benchmark_close: pd.Series,
    *,
    window: int = 20,
) -> pd.Series:
    asset = _numeric(close)
    benchmark = _numeric(benchmark_close).reindex(asset.index)
    return asset.pct_change(window) - benchmark.pct_change(window)


def volatility_expansion(
    close: pd.Series,
    *,
    short_window: int = 10,
    long_window: int = 40,
) -> pd.Series:
    if short_window < 2 or long_window <= short_window:
        raise ValueError("require 2 <= short_window < long_window")
    values = _numeric(close)
    log_ret = np.log(values / values.shift(1))
    short = log_ret.rolling(short_window, min_periods=short_window).std(ddof=0)
    long = log_ret.rolling(long_window, min_periods=long_window).std(ddof=0)
    return short / long.replace(0.0, np.nan) - 1.0


def build_technical_governance_features(
    frame: pd.DataFrame,
    *,
    benchmark_close: pd.Series | None = None,
    trend_window: int = 20,
) -> pd.DataFrame:
    if "close" not in frame.columns:
        raise ValueError("close column is required")
    close = _numeric(frame["close"])
    trend = rolling_log_trend(close, window=trend_window)
    out = pd.DataFrame(index=frame.index)
    out[f"trend_regression_slope_{trend_window}"] = trend["slope"]
    out[f"trend_regression_r2_{trend_window}"] = trend["r2"]
    out[f"trend_regression_tstat_{trend_window}"] = trend["tstat"]
    out[f"kaufman_efficiency_{trend_window}"] = kaufman_efficiency_ratio(close, window=trend_window)
    out[f"risk_adjusted_momentum_{trend_window}"] = risk_adjusted_momentum(close, window=trend_window)
    out["volatility_expansion_10_40"] = volatility_expansion(close, short_window=10, long_window=40)
    if benchmark_close is not None:
        out[f"relative_strength_{trend_window}"] = relative_strength(close, benchmark_close, window=trend_window)
    return out.replace([np.inf, -np.inf], np.nan)


__all__ = [
    "build_technical_governance_features",
    "kaufman_efficiency_ratio",
    "relative_strength",
    "risk_adjusted_momentum",
    "rolling_log_trend",
    "volatility_expansion",
]
