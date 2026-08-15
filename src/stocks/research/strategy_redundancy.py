from __future__ import annotations

import itertools

import numpy as np
import pandas as pd


def _daily_realized_returns(trades: pd.DataFrame) -> pd.Series:
    if trades.empty:
        return pd.Series(dtype=float)
    work = trades.copy()
    work["exit_time"] = pd.to_datetime(work["exit_time"], utc=True, errors="coerce")
    work["gross_return"] = pd.to_numeric(work["gross_return"], errors="coerce")
    work = work.dropna(subset=["exit_time", "gross_return"])
    if work.empty:
        return pd.Series(dtype=float)
    work["date"] = work["exit_time"].dt.floor("D")
    return work.groupby("date")["gross_return"].mean().sort_index()


def pairwise_redundancy(trades: pd.DataFrame) -> pd.DataFrame:
    required = {"hypothesis_id", "symbol", "entry_time", "exit_time", "gross_return"}
    if trades.empty:
        return pd.DataFrame(columns=["left", "right", "entry_jaccard", "realized_pnl_correlation", "redundancy_flag"])
    missing = required - set(trades.columns)
    if missing:
        raise ValueError(f"redundancy trades missing columns: {sorted(missing)}")

    groups = {str(key): value.copy() for key, value in trades.groupby("hypothesis_id")}
    rows = []
    for left, right in itertools.combinations(sorted(groups), 2):
        a = groups[left]
        b = groups[right]
        a_entries = set(zip(a["symbol"].astype(str), pd.to_datetime(a["entry_time"], utc=True).dt.floor("D")))
        b_entries = set(zip(b["symbol"].astype(str), pd.to_datetime(b["entry_time"], utc=True).dt.floor("D")))
        union = a_entries | b_entries
        jaccard = len(a_entries & b_entries) / len(union) if union else 0.0

        a_pnl = _daily_realized_returns(a)
        b_pnl = _daily_realized_returns(b)
        aligned = pd.concat([a_pnl.rename("a"), b_pnl.rename("b")], axis=1).dropna()
        correlation = float(aligned["a"].corr(aligned["b"])) if len(aligned) >= 10 else np.nan
        redundant = bool(jaccard >= 0.50 or (np.isfinite(correlation) and correlation >= 0.80))
        rows.append(
            {
                "left": left,
                "right": right,
                "entry_jaccard": float(jaccard),
                "realized_pnl_correlation": correlation,
                "redundancy_flag": redundant,
            }
        )
    return pd.DataFrame(rows)
