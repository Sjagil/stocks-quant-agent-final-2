from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from stocks.data.current_session_bridge_v2_27 import (
    aggregate_ibkr_30m_to_nyse_1h_v227,
    latest_completed_nyse_session_v227,
    reconcile_overlap_v227,
)


def _row(timestamp, o, h, l, c, v=100):
    return {
        "timestamp": timestamp,
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "volume": v,
    }


def test_30m_aggregates_from_nyse_open_anchor():
    records = [
        _row("2026-08-20T13:30:00Z", 10, 11, 9, 10.5, 100),
        _row("2026-08-20T14:00:00Z", 10.5, 12, 10, 11, 150),
        _row("2026-08-20T14:30:00Z", 11, 13, 10.5, 12, 200),
        _row("2026-08-20T15:00:00Z", 12, 12.5, 11, 11.5, 220),
    ]
    frame, audit = aggregate_ibkr_30m_to_nyse_1h_v227(
        records,
        decision_time=datetime(2026, 8, 20, 16, 0, tzinfo=UTC),
    )
    first = frame.loc[pd.Timestamp("2026-08-20T13:30:00Z")]
    assert first["open"] == 10
    assert first["high"] == 12
    assert first["low"] == 9
    assert first["close"] == 11
    assert first["volume"] == 250
    assert audit["forward_fill"] is False


def test_open_30m_bar_is_not_published():
    records = [
        _row("2026-08-20T13:30:00Z", 10, 11, 9, 10.5),
        _row("2026-08-20T14:00:00Z", 10.5, 12, 10, 11),
        _row("2026-08-20T14:30:00Z", 11, 13, 10.5, 12),
    ]
    frame, _ = aggregate_ibkr_30m_to_nyse_1h_v227(
        records,
        decision_time=datetime(2026, 8, 20, 14, 50, tzinfo=UTC),
    )
    assert list(frame.index) == [pd.Timestamp("2026-08-20T13:30:00Z")]


def test_overlap_reconciliation_passes_small_source_differences():
    index = pd.DatetimeIndex(
        ["2026-08-19T18:30:00Z", "2026-08-19T19:30:00Z"],
        name="timestamp",
    )
    left = pd.DataFrame(
        {
            "open": [100.0, 101.0],
            "high": [101.0, 102.0],
            "low": [99.0, 100.0],
            "close": [100.5, 101.5],
            "volume": [1000, 1200],
        },
        index=index,
    )
    right = left.copy()
    right["close"] *= 1.0005
    assert reconcile_overlap_v227(left, right)["passed"] is True


def test_overlap_reconciliation_blocks_wrong_contract():
    index = pd.DatetimeIndex(["2026-08-19T19:30:00Z"], name="timestamp")
    left = pd.DataFrame(
        {
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.5],
            "volume": [1000],
        },
        index=index,
    )
    right = left.copy()
    right["close"] = 130.0
    audit = reconcile_overlap_v227(left, right)
    assert audit["passed"] is False
    assert audit["reason"] == "SOURCE_OVERLAP_DIVERGENCE"


def test_research_asof_uses_last_completed_nyse_session_after_utc_midnight():
    assert latest_completed_nyse_session_v227(
        datetime(2026, 8, 21, 0, 30, tzinfo=UTC)
    ) == "2026-08-20"


def test_research_asof_advances_after_nyse_close():
    assert latest_completed_nyse_session_v227(
        datetime(2026, 8, 21, 22, 0, tzinfo=UTC)
    ) == "2026-08-21"
