from __future__ import annotations

import numpy as np
import pandas as pd


MAD_SCALE = 1.4826


def robust_zscore(
    values: pd.Series,
    *,
    clip: float | None = None,
) -> pd.Series:
    series = pd.to_numeric(values, errors="coerce").astype(float)
    median = float(series.median(skipna=True))
    mad = float((series - median).abs().median(skipna=True))
    if not np.isfinite(mad) or mad <= 1e-15:
        out = pd.Series(0.0, index=series.index, dtype=float).where(series.notna())
    else:
        out = (series - median) / (MAD_SCALE * mad)
    if clip is not None:
        if clip <= 0:
            raise ValueError("clip must be positive")
        out = out.clip(-float(clip), float(clip))
    return out


def winsorize(
    values: pd.Series,
    *,
    lower: float = 0.01,
    upper: float = 0.99,
) -> pd.Series:
    if not 0.0 <= lower < upper <= 1.0:
        raise ValueError("require 0 <= lower < upper <= 1")
    series = pd.to_numeric(values, errors="coerce").astype(float)
    lo = series.quantile(lower)
    hi = series.quantile(upper)
    return series.clip(lower=lo, upper=hi)


def cross_sectional_robust_zscore(
    frame: pd.DataFrame,
    *,
    date_column: str,
    value_column: str,
    output_column: str | None = None,
    clip: float | None = 3.0,
) -> pd.DataFrame:
    if date_column not in frame.columns or value_column not in frame.columns:
        raise ValueError("date/value column missing")
    out = frame.copy()
    name = output_column or f"{value_column}_robust_z"
    out[name] = out.groupby(date_column, sort=False)[value_column].transform(
        lambda group: robust_zscore(group, clip=clip)
    )
    return out
