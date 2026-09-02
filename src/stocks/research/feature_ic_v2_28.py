from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ICReport:
    mean_ic: float
    std_ic: float
    icir: float
    positive_fraction: float
    periods: int


def _corr(group: pd.DataFrame, feature: str, target: str, method: str) -> float:
    pair = group[[feature, target]].dropna()
    if len(pair) < 3 or pair[feature].nunique() < 2 or pair[target].nunique() < 2:
        return float("nan")
    return float(pair[feature].corr(pair[target], method=method))


def cross_sectional_ic_series(
    frame: pd.DataFrame,
    *,
    date_column: str,
    feature_column: str,
    target_column: str,
    rank: bool = True,
) -> pd.Series:
    required = {date_column, feature_column, target_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    method = "spearman" if rank else "pearson"
    values = frame.groupby(date_column, sort=True).apply(
        lambda group: _corr(group, feature_column, target_column, method),
        include_groups=False,
    )
    values.name = f"{'rank_' if rank else ''}ic"
    return pd.to_numeric(values, errors="coerce")


def summarize_ic(ic_series: pd.Series) -> ICReport:
    series = pd.to_numeric(ic_series, errors="coerce").dropna()
    if series.empty:
        return ICReport(float("nan"), float("nan"), float("nan"), float("nan"), 0)
    mean = float(series.mean())
    std = float(series.std(ddof=1)) if len(series) > 1 else 0.0
    icir = float(mean / std) if std > 1e-15 else float("nan")
    return ICReport(
        mean_ic=mean,
        std_ic=std,
        icir=icir,
        positive_fraction=float((series > 0).mean()),
        periods=int(len(series)),
    )


def feature_decay(
    frame: pd.DataFrame,
    *,
    feature_column: str,
    forward_columns: tuple[str, ...],
    rank: bool = True,
) -> pd.Series:
    if feature_column not in frame.columns:
        raise ValueError("feature column missing")
    method = "spearman" if rank else "pearson"
    result: dict[str, float] = {}
    for target in forward_columns:
        if target not in frame.columns:
            raise ValueError(f"forward column missing: {target}")
        pair = frame[[feature_column, target]].dropna()
        result[target] = (
            float(pair[feature_column].corr(pair[target], method=method))
            if len(pair) >= 3
            else float("nan")
        )
    return pd.Series(result, dtype=float)


def feature_redundancy(
    features: pd.DataFrame,
    *,
    method: str = "spearman",
) -> pd.Series:
    numeric = features.apply(pd.to_numeric, errors="coerce")
    corr = numeric.corr(method=method).abs()
    result: dict[str, float] = {}
    for column in corr.columns:
        others = corr[column].drop(index=column, errors="ignore").dropna()
        result[column] = 0.0 if others.empty else float(others.max())
    return pd.Series(result, dtype=float)
