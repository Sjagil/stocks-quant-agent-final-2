from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from stocks.orchestration.start_preflight_v2_26 import build_start_preflight_v226


def _broker(now):
    return {
        "captured_at": now.isoformat(),
        "snapshot_components_complete": True,
        "double_snapshot_stable": True,
        "broker_write_calls": 0,
        "economic_account_state": {"execution_status": "EXECUTION_ACCOUNT_READY"},
        "snapshot": {
            "positions": {"positions": []},
            "all_api_open_orders": {"open_orders": []},
        },
    }


def test_preflight_blocks_if_one_dynamic_symbol_is_stale():
    now = datetime(2026, 8, 20, 21, 0, tzinfo=UTC)
    signals = pd.DataFrame(
        [
            {"symbol": "AAA", "signal_bar_time": "2026-08-20T19:30:00Z"},
            {"symbol": "BBB", "signal_bar_time": "2026-08-19T19:30:00Z"},
        ]
    )
    shariah = pd.DataFrame(
        [{"symbol": "AAA", "decision_time": now.isoformat(), "trade_eligible": True}]
    )
    audit = {
        "ready": True,
        "strict_dynamic_deployment_gate": True,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    result = build_start_preflight_v226(
        decision_time=now,
        signals=signals,
        signal_audit=audit,
        current_shariah_events=shariah,
        broker_snapshot=_broker(now),
    )
    assert result["start_ready"] is False
    assert "DYNAMIC_MARKET_DATA_STALE" in result["blockers"]
    assert result["stale_dynamic_symbols"] == ["BBB"]
