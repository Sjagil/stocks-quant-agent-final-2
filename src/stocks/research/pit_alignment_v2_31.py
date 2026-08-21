from __future__ import annotations

import pandas as pd


def merge_asof_point_in_time(
    decisions: pd.DataFrame,
    facts: pd.DataFrame,
    *,
    symbol_column: str = "symbol",
    decision_time_column: str = "timestamp",
    available_at_column: str = "available_at",
    max_age: pd.Timedelta | None = None,
    suffix: str = "_fact",
) -> pd.DataFrame:
    """Backward as-of join that forbids facts unavailable at decision time."""
    required_left = {symbol_column, decision_time_column}
    required_right = {symbol_column, available_at_column}
    if missing := required_left.difference(decisions.columns):
        raise ValueError(f"decision columns missing: {sorted(missing)}")
    if missing := required_right.difference(facts.columns):
        raise ValueError(f"fact columns missing: {sorted(missing)}")
    left = decisions.copy()
    right = facts.copy()
    left[decision_time_column] = pd.to_datetime(left[decision_time_column], utc=True, errors="coerce")
    right[available_at_column] = pd.to_datetime(right[available_at_column], utc=True, errors="coerce")
    if left[decision_time_column].isna().any() or right[available_at_column].isna().any():
        raise ValueError("decision/fact timestamps must be valid and timezone-aware/UTC-convertible")
    left = left.sort_values([decision_time_column, symbol_column]).reset_index(drop=False).rename(columns={"index": "__original_index"})
    right = right.sort_values([available_at_column, symbol_column])
    merged = pd.merge_asof(
        left,
        right,
        left_on=decision_time_column,
        right_on=available_at_column,
        by=symbol_column,
        direction="backward",
        tolerance=max_age,
        suffixes=("", suffix),
        allow_exact_matches=True,
    )
    available = merged[available_at_column].notna()
    if (merged.loc[available, available_at_column] > merged.loc[available, decision_time_column]).any():
        raise AssertionError("point-in-time join leaked future facts")
    return merged.sort_values("__original_index").drop(columns=["__original_index"]).reset_index(drop=True)


__all__ = ["merge_asof_point_in_time"]
