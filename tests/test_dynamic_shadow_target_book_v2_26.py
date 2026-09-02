from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest

import stocks.orchestration.dynamic_shadow_target_book_v2_26 as module


def _broker(now: datetime, *, positions=None):
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
            "positions": {"positions": positions or []},
            "all_api_open_orders": {"open_orders": []},
        },
    }


def _signals(now: datetime, *, ready: bool):
    return pd.DataFrame([
        {
            "symbol": "AAA",
            "hypothesis_id": "h1",
            "strategy": "keltner_volume_breakout",
            "new_entry_ready": ready,
            "signal_bar_time": (now - timedelta(minutes=30)).isoformat(),
        }
    ])


def _bundle(now: datetime, targets):
    return SimpleNamespace(
        decision_id="d" * 64,
        projection=SimpleNamespace(targets=tuple(targets)),
    )


def _target(now: datetime):
    return SimpleNamespace(
        symbol="AAA",
        target_weight=0.10,
        confidence=0.90,
        strategy_ids=("keltner_volume_breakout",),
        hypothesis_ids=("h1",),
        data_cutoff=now - timedelta(minutes=30),
    )


def test_valid_readonly_snapshot_and_fresh_target_create_shadow_order(monkeypatch) -> None:
    now = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(
        module,
        "build_dynamic_validated_portfolio_intents",
        lambda *args, **kwargs: _bundle(now, [_target(now)]),
    )
    monkeypatch.setattr(
        module,
        "_reference_market_state",
        lambda *args, **kwargs: {
            "valid": True,
            "price_eur": 100.0,
            "atr_eur": 1.0,
            "stop_distance_eur": 2.0,
            "bar_time": now - timedelta(minutes=30),
            "canonical_source": "synthetic",
        },
    )
    target_book, orders, audit = module.build_dynamic_shadow_target_book_v226(
        ".",
        decision_time=now,
        broker_snapshot=_broker(now),
        signals=_signals(now, ready=True),
        signal_audit={},
        eligibility=pd.DataFrame([{"symbol": "AAA", "trade_eligible": True}]),
    )
    assert audit["ready"] is True
    assert audit["shadow_ready"] is True
    assert len(target_book) == 1
    assert target_book.loc[0, "target_quantity"] == 10
    assert target_book.loc[0, "shadow_action"] == "BUY"
    assert len(orders) == 1
    assert bool(orders.loc[orders.index[0], "transmit"]) is False
    assert audit["order_calls"] == 0
    assert audit["execution_authority"] == "NONE"


def test_stale_ready_signal_is_hard_blocked(monkeypatch) -> None:
    now = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(
        module,
        "build_dynamic_validated_portfolio_intents",
        lambda *args, **kwargs: _bundle(now, []),
    )
    signals = _signals(now, ready=True)
    signals.loc[0, "signal_bar_time"] = (now - timedelta(hours=8)).isoformat()
    with pytest.raises(ValueError, match="STALE_READY_SIGNAL"):
        module.build_dynamic_shadow_target_book_v226(
            ".",
            decision_time=now,
            broker_snapshot=_broker(now),
            signals=signals,
            signal_audit={},
            eligibility=pd.DataFrame([{"symbol": "AAA", "trade_eligible": True}]),
        )


def test_stale_broker_snapshot_blocks_before_portfolio_gateway(monkeypatch) -> None:
    now = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    called = {"gateway": False}
    def gateway(*args, **kwargs):
        called["gateway"] = True
        return _bundle(now, [])
    monkeypatch.setattr(module, "build_dynamic_validated_portfolio_intents", gateway)
    broker = _broker(now - timedelta(minutes=10))
    _, _, audit = module.build_dynamic_shadow_target_book_v226(
        ".",
        decision_time=now,
        broker_snapshot=broker,
        signals=_signals(now, ready=False),
        signal_audit={},
        eligibility=pd.DataFrame(),
    )
    assert audit["ready"] is False
    assert "BROKER_SNAPSHOT_STALE" in audit["blockers"]
    assert called["gateway"] is False


def test_existing_position_without_explicit_eur_value_fails_closed(monkeypatch) -> None:
    now = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    called = {"gateway": False}
    def gateway(*args, **kwargs):
        called["gateway"] = True
        return _bundle(now, [])
    monkeypatch.setattr(module, "build_dynamic_validated_portfolio_intents", gateway)
    broker = _broker(
        now,
        positions=[{"symbol": "AAA", "position_quantity": 2, "average_cost": 100.0}],
    )
    _, _, audit = module.build_dynamic_shadow_target_book_v226(
        ".",
        decision_time=now,
        broker_snapshot=broker,
        signals=_signals(now, ready=False),
        signal_audit={},
        eligibility=pd.DataFrame(),
    )
    assert audit["ready"] is False
    assert "POSITION_EUR_VALUATION_MISSING:AAA" in audit["blockers"]
    assert called["gateway"] is False


def test_readonly_constraints_reject_broker_write_activity() -> None:
    now = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    broker = _broker(now)
    broker["broker_write_calls"] = 1
    result = module.validate_broker_snapshot_v226(
        broker,
        decision_time=now,
        maximum_age_seconds=120,
    )
    assert result["valid"] is False
    assert "BROKER_WRITE_ACTIVITY_PRESENT" in result["blockers"]
