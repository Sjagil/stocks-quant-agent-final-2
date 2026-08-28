from __future__ import annotations
import numpy as np
import pandas as pd


def clean_returns(values) -> np.ndarray:
    arr = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    return arr[np.isfinite(arr)]


def skewness(values) -> float:
    x = clean_returns(values)
    if len(x) < 3:
        return float("nan")
    d = x - x.mean(); m2 = np.mean(d*d)
    if m2 <= 1e-18:
        return 0.0
    return float(np.mean(d**3) / m2**1.5)


def kurtosis(values) -> float:
    x = clean_returns(values)
    if len(x) < 4:
        return float("nan")
    d = x - x.mean(); m2 = np.mean(d*d)
    if m2 <= 1e-18:
        return 3.0
    return float(np.mean(d**4) / (m2*m2))


def max_drawdown_from_returns(values) -> float:
    x = clean_returns(values)
    if len(x) == 0 or np.any(x <= -1):
        return float("nan")
    wealth = np.cumprod(1.0 + x)
    peak = np.maximum.accumulate(wealth)
    dd = 1.0 - wealth / np.maximum(peak, 1e-18)
    return float(np.max(dd))


__all__ = ["clean_returns", "kurtosis", "max_drawdown_from_returns", "skewness"]
