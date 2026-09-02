from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

import stocks.data.current_session_bridge_v2_27 as bridge


def _frame(timestamp: str) -> pd.DataFrame:
    index = pd.DatetimeIndex([timestamp], name="timestamp")
    return pd.DataFrame(
        {
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.5],
            "volume": [1000.0],
        },
        index=index,
    )


def _install_fake_canonical(
    tmp_path: Path,
    monkeypatch,
    timestamp: str,
) -> None:
    target = (
        tmp_path
        / "data/canonical/provider_fabric"
        / "TEST_1h.parquet"
    )
    target.parent.mkdir(parents=True)
    target.touch()
    frame = _frame(timestamp)
    monkeypatch.setattr(
        bridge,
        "read_canonical_parquet",
        lambda *_args, **_kwargs: (frame.copy(), {}),
    )


def test_preopen_fresh_canonical_does_not_need_ibkr(
    tmp_path,
    monkeypatch,
):
    _install_fake_canonical(
        tmp_path,
        monkeypatch,
        "2026-08-20T19:30:00Z",
    )
    state = bridge.canonical_freshness_v227(
        tmp_path,
        "TEST",
        decision_time=datetime(
            2026,
            8,
            21,
            13,
            9,
            tzinfo=UTC,
        ),
    )
    assert state["status"] == "ALREADY_FRESH"
    assert state["operationally_fresh"] is True
    assert state["ibkr_tail_required"] is False


def test_bridge_already_fresh_accepts_zero_ibkr_records(
    tmp_path,
    monkeypatch,
):
    _install_fake_canonical(
        tmp_path,
        monkeypatch,
        "2026-08-20T19:30:00Z",
    )
    result = bridge.bridge_symbol_v227(
        tmp_path,
        "TEST",
        [],
        decision_time=datetime(
            2026,
            8,
            21,
            13,
            9,
            tzinfo=UTC,
        ),
    )
    assert result["status"] == "ALREADY_FRESH"
    assert result["operationally_fresh"] is True
    assert result["appended_rows"] == 0


def test_stale_canonical_still_requires_ibkr_tail(
    tmp_path,
    monkeypatch,
):
    _install_fake_canonical(
        tmp_path,
        monkeypatch,
        "2026-08-20T18:30:00Z",
    )
    state = bridge.canonical_freshness_v227(
        tmp_path,
        "TEST",
        decision_time=datetime(
            2026,
            8,
            21,
            13,
            9,
            tzinfo=UTC,
        ),
    )
    assert state["status"] == "NEEDS_IBKR_TAIL"
    assert state["operationally_fresh"] is False
    assert state["ibkr_tail_required"] is True
