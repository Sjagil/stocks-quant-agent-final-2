from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from stocks.orchestration.start_preflight_v2_26 import (
    build_start_preflight_v226,
    expected_latest_closed_nyse_1h_bar_v226,
)


def _broker(now: datetime):
    return {
        "captured_at": now.isoformat(),
        "snapshot_components_complete": True,
        "double_snapshot_stable": True,
        "broker_write_calls": 0,
        "economic_account_state": {
            "reporting_value_eur": 10_000.0,
            "execution_sizing_capacity_eur": 5_000.0,
            "spendable_eur": 5_000.0,
            "execution_status": "EXECUTION_ACCOUNT_READY",
        },
        "snapshot": {
            "positions": {"positions": []},
            "all_api_open_orders": {"open_orders": []},
        },
    }


def _audit():
    return {
        "ready": True,
        "strict_dynamic_deployment_gate": True,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }


def test_expected_bar_is_session_aware_after_market_close() -> None:
    # 2026-08-19 23:00 UTC is after the NYSE close. The last 1h bar starts 19:30 UTC.
    now = datetime(2026, 8, 19, 23, 0, tzinfo=UTC)
    assert expected_latest_closed_nyse_1h_bar_v226(now) == pd.Timestamp(
        "2026-08-19T19:30:00Z"
    )


def test_preflight_accepts_fresh_closed_session_state() -> None:
    now = datetime(2026, 8, 19, 23, 0, tzinfo=UTC)
    expected = expected_latest_closed_nyse_1h_bar_v226(now)
    signals = pd.DataFrame([
        {"symbol": "AAA", "signal_bar_time": expected.isoformat()}
    ])
    shariah = pd.DataFrame([
        {
            "symbol": "AAA",
            "decision_time": (now - timedelta(hours=1)).isoformat(),
            "trade_eligible": True,
        }
    ])
    result = build_start_preflight_v226(
        decision_time=now,
        signals=signals,
        signal_audit=_audit(),
        current_shariah_events=shariah,
        broker_snapshot=_broker(now),
    )
    assert result["start_ready"] is True
    assert result["blockers"] == []


def test_preflight_rejects_old_market_state() -> None:
    now = datetime(2026, 8, 19, 23, 0, tzinfo=UTC)
    signals = pd.DataFrame([
        {"symbol": "AAA", "signal_bar_time": "2026-08-14T19:30:00Z"}
    ])
    shariah = pd.DataFrame([
        {"symbol": "AAA", "decision_time": now.isoformat(), "trade_eligible": True}
    ])
    result = build_start_preflight_v226(
        decision_time=now,
        signals=signals,
        signal_audit=_audit(),
        current_shariah_events=shariah,
        broker_snapshot=_broker(now),
    )
    assert result["start_ready"] is False
    assert "DYNAMIC_MARKET_DATA_STALE" in result["blockers"]


def test_preflight_requires_verified_dynamic_candidate() -> None:
    now = datetime(2026, 8, 19, 23, 0, tzinfo=UTC)
    expected = expected_latest_closed_nyse_1h_bar_v226(now)
    signals = pd.DataFrame([
        {"symbol": "AAA", "signal_bar_time": expected.isoformat()}
    ])
    shariah = pd.DataFrame([
        {"symbol": "AAA", "decision_time": now.isoformat(), "trade_eligible": False}
    ])
    result = build_start_preflight_v226(
        decision_time=now,
        signals=signals,
        signal_audit=_audit(),
        current_shariah_events=shariah,
        broker_snapshot=_broker(now),
    )
    assert "NO_SHARIAH_VERIFIED_DYNAMIC_CANDIDATES" in result["blockers"]
