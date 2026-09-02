from __future__ import annotations
import numpy as np
import pandas as pd
from stocks.quant.covariance import shrink_covariance


def clean_strategy_returns(returns: pd.DataFrame, *, min_observations: int = 20) -> pd.DataFrame:
    if not isinstance(returns, pd.DataFrame) or returns.empty:
        raise ValueError("strategy returns must be a non-empty DataFrame")
    frame = returns.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    keep = [c for c in frame.columns if int(frame[c].notna().sum()) >= int(min_observations)]
    frame = frame.loc[:, keep].dropna(how="any")
    if frame.shape[1] < 1 or len(frame) < min_observations:
        raise ValueError("insufficient complete strategy return history")
    return frame.astype(float)


def strategy_covariance(
    returns: pd.DataFrame, *, method: str = "ledoit_wolf", periods_per_year: float | None = None,
    min_observations: int = 20,
) -> pd.DataFrame:
    frame = clean_strategy_returns(returns, min_observations=min_observations)
    return shrink_covariance(frame, method=method, periods_per_year=periods_per_year)


def correlation_from_covariance(covariance: pd.DataFrame) -> pd.DataFrame:
    cov = covariance.astype(float)
    if list(cov.index) != list(cov.columns):
        raise ValueError("covariance index and columns must match")
    scale = np.sqrt(np.clip(np.diag(cov.to_numpy(float)), 0.0, None))
    denom = np.outer(scale, scale)
    corr = np.divide(cov.to_numpy(float), denom, out=np.zeros_like(denom), where=denom > 1e-18)
    np.fill_diagonal(corr, 1.0)
    corr = np.clip(corr, -1.0, 1.0)
    return pd.DataFrame(corr, index=cov.index, columns=cov.columns)


def effective_independent_strategies(correlation: pd.DataFrame) -> float:
    values = np.linalg.eigvalsh(correlation.astype(float).to_numpy())
    values = np.clip(values, 0.0, None)
    s = float(values.sum())
    d = float(np.square(values).sum())
    return 0.0 if d <= 1e-18 else float(s * s / d)


def correlation_clusters(correlation: pd.DataFrame, *, threshold: float = 0.80) -> tuple[tuple[str, ...], ...]:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0,1]")
    corr = correlation.abs()
    names = list(corr.columns)
    visited: set[str] = set(); groups=[]
    for start in names:
        if start in visited: continue
        stack=[start]; group=set()
        while stack:
            node=stack.pop()
            if node in group: continue
            group.add(node); visited.add(node)
            stack.extend(other for other in names if other not in group and other != node and float(corr.loc[node, other]) >= threshold)
        groups.append(tuple(sorted(group)))
    return tuple(sorted(groups, key=lambda x: (x[0], len(x))))

__all__=["clean_strategy_returns","strategy_covariance","correlation_from_covariance","effective_independent_strategies","correlation_clusters"]
