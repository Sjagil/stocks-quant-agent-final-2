from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd


def _frame(returns: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(returns, pd.DataFrame) or returns.empty:
        raise ValueError("returns must be a non-empty DataFrame")
    out = returns.apply(pd.to_numeric, errors="coerce").astype(float)
    if out.dropna(how="all").empty:
        raise ValueError("returns contain no numeric observations")
    return out


def _weights(weights: pd.Series | Iterable[float], columns: pd.Index) -> np.ndarray:
    if isinstance(weights, pd.Series):
        vector = weights.reindex(columns).fillna(0.0).to_numpy(dtype=float)
    else:
        vector = np.asarray(list(weights), dtype=float)
    if vector.shape != (len(columns),):
        raise ValueError("weights dimension does not match covariance matrix")
    if not np.isfinite(vector).all():
        raise ValueError("weights must be finite")
    return vector


def sample_covariance(
    returns: pd.DataFrame,
    *,
    periods_per_year: float | None = None,
) -> pd.DataFrame:
    frame = _frame(returns)
    cov = frame.cov()
    if periods_per_year is not None:
        if periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        cov = cov * float(periods_per_year)
    return cov


def ewma_covariance(
    returns: pd.DataFrame,
    *,
    decay: float = 0.94,
    periods_per_year: float | None = None,
) -> pd.DataFrame:
    if not 0.0 < decay < 1.0:
        raise ValueError("decay must be in (0, 1)")
    frame = _frame(returns).dropna(how="any")
    if len(frame) < 2:
        raise ValueError("need at least two complete return observations")
    values = frame.to_numpy(dtype=float)
    values = values - values.mean(axis=0, keepdims=True)
    powers = np.arange(len(values) - 1, -1, -1, dtype=float)
    raw = (1.0 - decay) * np.power(decay, powers)
    weights = raw / raw.sum()
    cov = (values * weights[:, None]).T @ values
    if periods_per_year is not None:
        if periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        cov = cov * float(periods_per_year)
    return pd.DataFrame(cov, index=frame.columns, columns=frame.columns)


def shrink_covariance(
    returns: pd.DataFrame,
    *,
    method: str = "ledoit_wolf",
    periods_per_year: float | None = None,
) -> pd.DataFrame:
    frame = _frame(returns).dropna(how="any")
    if len(frame) < 2:
        raise ValueError("need at least two complete return observations")
    normalized = method.strip().lower()
    try:
        from sklearn.covariance import LedoitWolf, OAS
    except Exception as exc:  # pragma: no cover
        raise ImportError("scikit-learn is required for covariance shrinkage") from exc
    estimator = LedoitWolf() if normalized in {"ledoit_wolf", "lw"} else OAS() if normalized == "oas" else None
    if estimator is None:
        raise ValueError("method must be 'ledoit_wolf' or 'oas'")
    estimator.fit(frame.to_numpy(dtype=float))
    cov = np.asarray(estimator.covariance_, dtype=float)
    if periods_per_year is not None:
        if periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        cov = cov * float(periods_per_year)
    return pd.DataFrame(cov, index=frame.columns, columns=frame.columns)


def portfolio_volatility(
    weights: pd.Series | Iterable[float],
    covariance: pd.DataFrame,
) -> float:
    cov = covariance.astype(float)
    vector = _weights(weights, cov.columns)
    variance = float(vector @ cov.to_numpy(dtype=float) @ vector)
    return float(math.sqrt(max(0.0, variance)))


def marginal_risk_contribution(
    weights: pd.Series | Iterable[float],
    covariance: pd.DataFrame,
) -> pd.Series:
    cov = covariance.astype(float)
    vector = _weights(weights, cov.columns)
    sigma = portfolio_volatility(vector, cov)
    if sigma <= 1e-15:
        return pd.Series(0.0, index=cov.columns)
    return pd.Series(cov.to_numpy(dtype=float) @ vector / sigma, index=cov.columns)


def risk_contribution(
    weights: pd.Series | Iterable[float],
    covariance: pd.DataFrame,
) -> pd.Series:
    cov = covariance.astype(float)
    vector = _weights(weights, cov.columns)
    return pd.Series(vector, index=cov.columns) * marginal_risk_contribution(vector, cov)


def diversification_ratio(
    weights: pd.Series | Iterable[float],
    covariance: pd.DataFrame,
) -> float:
    cov = covariance.astype(float)
    vector = _weights(weights, cov.columns)
    sigma_assets = np.sqrt(np.clip(np.diag(cov.to_numpy(dtype=float)), 0.0, None))
    denominator = portfolio_volatility(vector, cov)
    if denominator <= 1e-15:
        return float("nan")
    return float(vector @ sigma_assets / denominator)


def effective_number_of_positions(weights: pd.Series | Iterable[float]) -> float:
    vector = np.asarray(weights.to_numpy(dtype=float) if isinstance(weights, pd.Series) else list(weights), dtype=float)
    if (vector < -1e-12).any():
        raise ValueError("effective number assumes non-negative weights")
    total = vector.sum()
    if total <= 0:
        return 0.0
    normalized = vector / total
    hhi = float(np.square(normalized).sum())
    return 0.0 if hhi <= 0 else 1.0 / hhi


def entropy_effective_number(weights: pd.Series | Iterable[float]) -> float:
    vector = np.asarray(weights.to_numpy(dtype=float) if isinstance(weights, pd.Series) else list(weights), dtype=float)
    if (vector < -1e-12).any():
        raise ValueError("entropy effective number assumes non-negative weights")
    total = vector.sum()
    if total <= 0:
        return 0.0
    normalized = vector / total
    positive = normalized[normalized > 0]
    return float(np.exp(-np.sum(positive * np.log(positive))))
