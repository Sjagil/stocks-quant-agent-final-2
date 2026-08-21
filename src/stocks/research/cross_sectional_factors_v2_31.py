from __future__ import annotations

import numpy as np
import pandas as pd

from stocks.quant.normalization import robust_zscore


def cross_sectional_percentile_rank(
    frame: pd.DataFrame,
    *,
    date_column: str,
    value_column: str,
    output_column: str | None = None,
) -> pd.DataFrame:
    required = {date_column, value_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    out = frame.copy()
    name = output_column or f"{value_column}_pct_rank"
    out[name] = out.groupby(date_column, sort=False)[value_column].rank(method="average", pct=True)
    return out


def sector_neutral_robust_zscore(
    frame: pd.DataFrame,
    *,
    date_column: str,
    sector_column: str,
    value_column: str,
    output_column: str | None = None,
    clip: float = 3.0,
) -> pd.DataFrame:
    required = {date_column, sector_column, value_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    out = frame.copy()
    name = output_column or f"{value_column}_sector_neutral_z"
    out[name] = out.groupby([date_column, sector_column], sort=False)[value_column].transform(
        lambda values: robust_zscore(values, clip=clip) if values.notna().any() else pd.Series(np.nan, index=values.index, dtype=float)
    )
    return out


def cross_sectional_momentum_panel(
    prices: pd.DataFrame,
    *,
    symbol_column: str = "symbol",
    date_column: str = "timestamp",
    close_column: str = "close",
    sector_column: str | None = "sector",
    window: int = 20,
) -> pd.DataFrame:
    required = {symbol_column, date_column, close_column}
    missing = required.difference(prices.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    if window < 1:
        raise ValueError("window must be positive")
    out = prices.copy().sort_values([symbol_column, date_column])
    out[close_column] = pd.to_numeric(out[close_column], errors="coerce")
    out[f"momentum_{window}"] = out.groupby(symbol_column, sort=False)[close_column].pct_change(window)
    out = cross_sectional_percentile_rank(
        out,
        date_column=date_column,
        value_column=f"momentum_{window}",
        output_column=f"cross_sectional_momentum_rank_{window}",
    )
    out[f"cross_sectional_momentum_z_{window}"] = out.groupby(date_column, sort=False)[
        f"momentum_{window}"
    ].transform(lambda values: robust_zscore(values, clip=3.0) if values.notna().any() else pd.Series(np.nan, index=values.index, dtype=float))
    if sector_column and sector_column in out.columns:
        out = sector_neutral_robust_zscore(
            out,
            date_column=date_column,
            sector_column=sector_column,
            value_column=f"momentum_{window}",
            output_column=f"sector_neutral_momentum_z_{window}",
        )
    return out


def cross_sectional_dispersion_by_date(
    frame: pd.DataFrame,
    *,
    date_column: str,
    return_column: str,
) -> pd.Series:
    values = frame[[date_column, return_column]].copy()
    values[return_column] = pd.to_numeric(values[return_column], errors="coerce")
    result = values.groupby(date_column, sort=True)[return_column].std(ddof=0)
    result.name = "cross_sectional_dispersion"
    return result


__all__ = [
    "cross_sectional_dispersion_by_date",
    "cross_sectional_momentum_panel",
    "cross_sectional_percentile_rank",
    "sector_neutral_robust_zscore",
]
