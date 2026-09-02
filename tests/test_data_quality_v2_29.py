from __future__ import annotations

import math

import numpy as np
import pandas as pd

from stocks.data.quality_v2_29 import (
    DataQualityPolicy,
    freshness_score,
    ohlcv_quality_report,
)


def _frame(rows=100):
    idx = pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC")
    close = 100 + np.linspace(0, 5, rows)
    return pd.DataFrame({
        "open": close - 0.2,
        "high": close + 0.5,
        "low": close - 0.5,
        "close": close,
        "volume": np.full(rows, 1000.0),
    }, index=idx)


def test_clean_ohlcv_passes_integrity():
    frame = _frame()
    report = ohlcv_quality_report(
        frame,
        expected_rows=100,
        expected_latest=frame.index[-1],
        expected_interval=pd.Timedelta(hours=1),
    )
    assert report["status"] == "READY"
    assert report["quality_score"] > 0.99
    assert not report["blockers"]


def test_duplicate_and_ohlc_violation_fail_closed():
    frame = _frame(20)
    duplicated = pd.concat([frame, frame.iloc[[-1]]])
    duplicated.iloc[-1, duplicated.columns.get_loc("low")] = duplicated.iloc[-1]["high"] + 1
    report = ohlcv_quality_report(
        duplicated,
        expected_rows=20,
        expected_latest=frame.index[-1],
        expected_interval=pd.Timedelta(hours=1),
    )
    assert report["status"] == "BLOCKED"
    assert "DUPLICATE_TIMESTAMPS" in report["blockers"]
    assert "OHLC_INTEGRITY" in report["blockers"]


def test_freshness_half_life():
    assert math.isclose(freshness_score(lag_seconds=3600, half_life_seconds=3600), 0.5)


def test_session_aware_gap_check_ignores_overnight_rth_gap():
    day1 = pd.date_range("2026-01-05 14:30", periods=7, freq="h", tz="UTC")
    day2 = pd.date_range("2026-01-06 14:30", periods=7, freq="h", tz="UTC")
    idx = day1.append(day2)
    close = 100 + np.linspace(0, 2, len(idx))
    frame = pd.DataFrame({
        "open": close,
        "high": close + 0.2,
        "low": close - 0.2,
        "close": close,
        "volume": np.full(len(idx), 1000.0),
    }, index=idx)
    report = ohlcv_quality_report(
        frame,
        expected_rows=len(frame),
        expected_latest=frame.index[-1],
        expected_interval=pd.Timedelta(hours=1),
        session_timezone="America/New_York",
    )
    assert report["gap_ratio"] == 0.0
    assert "EXCESSIVE_GAPS" not in report["blockers"]
