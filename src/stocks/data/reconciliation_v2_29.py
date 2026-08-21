from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _canonical(frame: pd.DataFrame, suffix: str) -> pd.DataFrame:
    required = {"open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing OHLCV columns: {sorted(missing)}")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError("frame must use DatetimeIndex")
    out = frame[list(required)].copy()
    for column in required:
        out[column] = pd.to_numeric(out[column], errors="coerce").astype(float)
    return out.add_suffix(suffix)


def cross_provider_disagreement(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    left_name: str = "left",
    right_name: str = "right",
) -> dict[str, Any]:
    a = _canonical(left, "_a")
    b = _canonical(right, "_b")
    joined = a.join(b, how="inner").dropna()
    if joined.empty:
        return {
            "overlap_rows": 0,
            "status": "NO_OVERLAP",
            "execution_authority": "NONE",
        }

    metrics: dict[str, float] = {}
    for column in ("open", "high", "low", "close"):
        x = joined[f"{column}_a"]
        y = joined[f"{column}_b"]
        denominator = ((x.abs() + y.abs()) / 2.0).replace(0.0, np.nan)
        relative = (x - y).abs() / denominator
        metrics[f"{column}_median_disagreement_bps"] = float(relative.median() * 10_000.0)
        metrics[f"{column}_p95_disagreement_bps"] = float(relative.quantile(0.95) * 10_000.0)

    va = joined["volume_a"]
    vb = joined["volume_b"]
    volume_denominator = pd.concat([va.abs(), vb.abs()], axis=1).max(axis=1).replace(0.0, np.nan)
    volume_relative = (va - vb).abs() / volume_denominator
    metrics["volume_median_relative_disagreement"] = float(volume_relative.median())
    metrics["volume_p95_relative_disagreement"] = float(volume_relative.quantile(0.95))

    return {
        "provider_left": left_name,
        "provider_right": right_name,
        "overlap_rows": int(len(joined)),
        "status": "OK",
        **metrics,
        "execution_authority": "NONE",
    }
