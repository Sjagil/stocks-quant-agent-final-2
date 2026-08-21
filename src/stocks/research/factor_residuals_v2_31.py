from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RollingFactorConfig:
    window: int = 60
    min_observations: int = 40
    add_intercept: bool = True

    def __post_init__(self) -> None:
        if self.window < 5:
            raise ValueError("window must be >= 5")
        if not 3 <= self.min_observations <= self.window:
            raise ValueError("min_observations must be in [3, window]")


def _fit(y: np.ndarray, x: np.ndarray, *, add_intercept: bool) -> tuple[np.ndarray, float, float]:
    matrix = np.column_stack([np.ones(len(x)), x]) if add_intercept else x
    coef, *_ = np.linalg.lstsq(matrix, y, rcond=None)
    fitted = matrix @ coef
    residual = y - fitted
    dof = max(1, len(y) - matrix.shape[1])
    idio = float(np.sqrt(np.dot(residual, residual) / dof))
    current_residual = float(y[-1] - fitted[-1])
    return coef, current_residual, idio


def rolling_factor_projection(
    asset_returns: pd.Series,
    factor_returns: pd.DataFrame,
    *,
    config: RollingFactorConfig | None = None,
) -> pd.DataFrame:
    cfg = config or RollingFactorConfig()
    y = pd.to_numeric(asset_returns, errors="coerce").astype(float)
    x = factor_returns.apply(pd.to_numeric, errors="coerce").astype(float).reindex(y.index)
    out = pd.DataFrame(index=y.index)
    factor_names = tuple(str(c) for c in x.columns)
    for factor in factor_names:
        out[f"beta_{factor}"] = np.nan
    out["factor_alpha"] = np.nan
    out["factor_residual"] = np.nan
    out["idiosyncratic_vol"] = np.nan

    for end in range(len(y)):
        start = max(0, end - cfg.window + 1)
        window = pd.concat([y.iloc[start : end + 1].rename("asset"), x.iloc[start : end + 1]], axis=1).dropna()
        if len(window) < cfg.min_observations or not factor_names:
            continue
        coef, current_residual, idio = _fit(
            window["asset"].to_numpy(dtype=float),
            window[list(factor_names)].to_numpy(dtype=float),
            add_intercept=cfg.add_intercept,
        )
        offset = 1 if cfg.add_intercept else 0
        out.iloc[end, out.columns.get_loc("factor_alpha")] = float(coef[0]) if cfg.add_intercept else 0.0
        for idx, factor in enumerate(factor_names):
            out.iloc[end, out.columns.get_loc(f"beta_{factor}")] = float(coef[idx + offset])
        out.iloc[end, out.columns.get_loc("factor_residual")] = current_residual
        out.iloc[end, out.columns.get_loc("idiosyncratic_vol")] = idio
    return out


def residual_momentum(residual_returns: pd.Series, *, window: int = 20) -> pd.Series:
    if window < 1:
        raise ValueError("window must be positive")
    values = pd.to_numeric(residual_returns, errors="coerce").astype(float)
    return (1.0 + values).rolling(window, min_periods=window).apply(np.prod, raw=True) - 1.0


__all__ = ["RollingFactorConfig", "residual_momentum", "rolling_factor_projection"]
