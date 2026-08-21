from __future__ import annotations

import numpy as np
import pandas as pd


def factor_beta(asset_returns: pd.Series, factor_returns: pd.Series) -> float:
    frame = pd.concat(
        [
            pd.to_numeric(asset_returns, errors="coerce").rename("asset"),
            pd.to_numeric(factor_returns, errors="coerce").rename("factor"),
        ],
        axis=1,
    ).dropna()
    if len(frame) < 2:
        return float("nan")
    variance = float(frame["factor"].var(ddof=1))
    if variance <= 1e-15:
        return float("nan")
    return float(frame["asset"].cov(frame["factor"]) / variance)


def rolling_beta(
    asset_returns: pd.Series,
    factor_returns: pd.Series,
    *,
    window: int = 60,
) -> pd.Series:
    if window < 2:
        raise ValueError("window must be >= 2")
    asset = pd.to_numeric(asset_returns, errors="coerce").astype(float)
    factor = pd.to_numeric(factor_returns, errors="coerce").astype(float)
    covariance = asset.rolling(window, min_periods=window).cov(factor)
    variance = factor.rolling(window, min_periods=window).var(ddof=1)
    return covariance / variance.replace(0.0, np.nan)


def residual_returns(
    asset_returns: pd.Series,
    factors: pd.DataFrame,
) -> pd.Series:
    y = pd.to_numeric(asset_returns, errors="coerce").rename("asset")
    x = factors.apply(pd.to_numeric, errors="coerce")
    joined = pd.concat([y, x], axis=1).dropna()
    if len(joined) <= x.shape[1] + 1:
        return pd.Series(np.nan, index=asset_returns.index, name="residual")
    matrix = np.column_stack([np.ones(len(joined)), joined[x.columns].to_numpy(dtype=float)])
    coefficients, *_ = np.linalg.lstsq(matrix, joined["asset"].to_numpy(dtype=float), rcond=None)
    fitted = matrix @ coefficients
    residual = joined["asset"].to_numpy(dtype=float) - fitted
    out = pd.Series(np.nan, index=asset_returns.index, dtype=float, name="residual")
    out.loc[joined.index] = residual
    return out


def residual_momentum(
    residuals: pd.Series,
    *,
    window: int = 20,
) -> pd.Series:
    if window < 1:
        raise ValueError("window must be >= 1")
    values = pd.to_numeric(residuals, errors="coerce").astype(float)
    return (1.0 + values).rolling(window, min_periods=window).apply(np.prod, raw=True) - 1.0


def cross_sectional_dispersion(returns: pd.DataFrame) -> pd.Series:
    frame = returns.apply(pd.to_numeric, errors="coerce").astype(float)
    return frame.std(axis=1, ddof=0)


def average_pairwise_correlation(returns: pd.DataFrame) -> float:
    corr = returns.apply(pd.to_numeric, errors="coerce").corr()
    if len(corr) < 2:
        return float("nan")
    values = corr.to_numpy(dtype=float)
    mask = np.triu(np.ones_like(values, dtype=bool), k=1)
    pairs = values[mask]
    pairs = pairs[np.isfinite(pairs)]
    return float(np.mean(pairs)) if len(pairs) else float("nan")
