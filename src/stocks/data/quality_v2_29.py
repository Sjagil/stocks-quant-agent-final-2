from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DataQualityPolicy:
    freshness_half_life_seconds: float = 3600.0
    minimum_coverage: float = 0.95
    maximum_duplicate_ratio: float = 0.0
    maximum_ohlc_violation_ratio: float = 0.0
    maximum_negative_volume_ratio: float = 0.0
    maximum_gap_ratio: float = 0.02
    maximum_outlier_ratio: float = 0.02

    def __post_init__(self) -> None:
        if self.freshness_half_life_seconds <= 0:
            raise ValueError("freshness_half_life_seconds must be positive")
        for field in (
            "minimum_coverage",
            "maximum_duplicate_ratio",
            "maximum_ohlc_violation_ratio",
            "maximum_negative_volume_ratio",
            "maximum_gap_ratio",
            "maximum_outlier_ratio",
        ):
            value = float(getattr(self, field))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field} must be in [0,1]")


def freshness_score(*, lag_seconds: float, half_life_seconds: float) -> float:
    if lag_seconds < 0:
        return 1.0
    if half_life_seconds <= 0:
        raise ValueError("half_life_seconds must be positive")
    return float(math.exp(-math.log(2.0) * float(lag_seconds) / float(half_life_seconds)))


def coverage_ratio(*, observed_rows: int, expected_rows: int | None) -> float:
    if observed_rows < 0:
        raise ValueError("observed_rows cannot be negative")
    if expected_rows is None:
        return 1.0
    if expected_rows <= 0:
        raise ValueError("expected_rows must be positive")
    return float(np.clip(observed_rows / expected_rows, 0.0, 1.0))


def _index(frame: pd.DataFrame) -> pd.DatetimeIndex:
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError("OHLCV frame must use a DatetimeIndex")
    index = pd.DatetimeIndex(frame.index)
    if index.tz is None:
        raise ValueError("OHLCV index must be timezone-aware")
    return index


def _required_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing OHLCV columns: {sorted(missing)}")
    out = frame.copy()
    for column in required:
        out[column] = pd.to_numeric(out[column], errors="coerce").astype(float)
    return out


def _robust_return_outlier_ratio(close: pd.Series, threshold: float = 8.0) -> float:
    returns = np.log(close / close.shift(1)).replace([np.inf, -np.inf], np.nan).dropna()
    if len(returns) < 5:
        return 0.0
    median = float(returns.median())
    mad = float((returns - median).abs().median())
    if mad <= 1e-15:
        return 0.0
    z = (returns - median).abs() / (1.4826 * mad)
    return float((z > threshold).mean())


def ohlcv_quality_report(
    frame: pd.DataFrame,
    *,
    expected_rows: int | None = None,
    expected_latest: pd.Timestamp | datetime | None = None,
    expected_interval: pd.Timedelta | None = None,
    session_timezone: str | None = None,
    policy: DataQualityPolicy | None = None,
) -> dict[str, Any]:
    active = policy or DataQualityPolicy()
    work = _required_ohlcv(frame)
    index = _index(work)
    rows = len(work)
    if rows == 0:
        return {
            "rows": 0,
            "quality_score": 0.0,
            "status": "FAILED",
            "blockers": ["ZERO_ROWS"],
        }

    duplicate_ratio = float(index.duplicated().mean())
    missing_value_ratio = float(work[["open", "high", "low", "close", "volume"]].isna().mean().mean())
    valid = work.dropna(subset=["open", "high", "low", "close"])
    lower_bound = valid[["open", "close"]].min(axis=1)
    upper_bound = valid[["open", "close"]].max(axis=1)
    violations = (
        (valid["low"] > lower_bound)
        | (valid["high"] < upper_bound)
        | (valid["high"] < valid["low"])
        | (valid[["open", "high", "low", "close"]] <= 0).any(axis=1)
    )
    ohlc_violation_ratio = float(violations.mean()) if len(valid) else 1.0
    negative_volume_ratio = float((work["volume"].dropna() < 0).mean()) if work["volume"].notna().any() else 1.0
    outlier_ratio = _robust_return_outlier_ratio(work["close"])

    coverage = coverage_ratio(observed_rows=rows, expected_rows=expected_rows)

    gap_ratio = 0.0
    if expected_interval is not None and rows >= 2:
        if expected_interval <= pd.Timedelta(0):
            raise ValueError("expected_interval must be positive")
        ordered = index.sort_values()
        diffs = pd.Series(ordered, index=ordered).diff()
        if session_timezone:
            local_dates = pd.Series(
                ordered.tz_convert(session_timezone).date,
                index=ordered,
            )
            same_session = local_dates.eq(local_dates.shift(1))
            diffs = diffs[same_session]
        diffs = diffs.dropna()
        gap_ratio = float((diffs > expected_interval * 1.5).mean()) if len(diffs) else 0.0

    latest = index.max()
    freshness_lag_seconds = 0.0
    if expected_latest is not None:
        expected = pd.Timestamp(expected_latest)
        if expected.tzinfo is None:
            raise ValueError("expected_latest must be timezone-aware")
        freshness_lag_seconds = max(0.0, float((expected - latest).total_seconds()))
    freshness = freshness_score(
        lag_seconds=freshness_lag_seconds,
        half_life_seconds=active.freshness_half_life_seconds,
    )

    completeness = max(0.0, 1.0 - missing_value_ratio)
    integrity = max(0.0, 1.0 - max(ohlc_violation_ratio, negative_volume_ratio, duplicate_ratio))
    continuity = max(0.0, 1.0 - gap_ratio)
    outlier_score = max(0.0, 1.0 - outlier_ratio)
    score = (
        0.25 * freshness
        + 0.25 * coverage
        + 0.15 * completeness
        + 0.15 * integrity
        + 0.10 * continuity
        + 0.10 * outlier_score
    )

    blockers: list[str] = []
    if coverage < active.minimum_coverage:
        blockers.append("COVERAGE_BELOW_MINIMUM")
    if duplicate_ratio > active.maximum_duplicate_ratio:
        blockers.append("DUPLICATE_TIMESTAMPS")
    if ohlc_violation_ratio > active.maximum_ohlc_violation_ratio:
        blockers.append("OHLC_INTEGRITY")
    if negative_volume_ratio > active.maximum_negative_volume_ratio:
        blockers.append("NEGATIVE_VOLUME")
    if gap_ratio > active.maximum_gap_ratio:
        blockers.append("EXCESSIVE_GAPS")
    if outlier_ratio > active.maximum_outlier_ratio:
        blockers.append("EXCESSIVE_RETURN_OUTLIERS")

    return {
        "rows": rows,
        "first": index.min().isoformat(),
        "latest": latest.isoformat(),
        "coverage": coverage,
        "freshness_lag_seconds": freshness_lag_seconds,
        "freshness_score": freshness,
        "missing_value_ratio": missing_value_ratio,
        "duplicate_ratio": duplicate_ratio,
        "ohlc_violation_ratio": ohlc_violation_ratio,
        "negative_volume_ratio": negative_volume_ratio,
        "gap_ratio": gap_ratio,
        "return_outlier_ratio": outlier_ratio,
        "quality_score": float(np.clip(score, 0.0, 1.0)),
        "status": "READY" if not blockers else "BLOCKED",
        "blockers": blockers,
        "execution_authority": "NONE",
    }
