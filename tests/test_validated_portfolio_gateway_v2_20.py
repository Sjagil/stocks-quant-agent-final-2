from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from stocks.contracts import IntentAction, TradeIntent
from stocks.orchestration.validated_portfolio_gateway_v2_20 import (
    DecisionGatewayPolicy,
    build_validated_portfolio_intents,
    build_validated_portfolio_intents_from_project,
)
from stocks.portfolio.deterministic_allocator_v2_20 import (
    AllocationPolicy,
    AlphaProposal,
    AssetKind,
    project_long_only,
)

REGISTRY_HASH = "a" * 64
SOURCE_FINGERPRINT = "b" * 64
DECISION_TIME = datetime(2026, 8, 18, 14, 0, tzinfo=UTC)


def _audit(**overrides) -> dict:
    return {
        "schema": "validated_forward_signal_state_v2_19",
        "ready": True,
        "strict_validated_deployment_gate": True,
        "deployment_registry_sha256": REGISTRY_HASH,
        "source_fingerprint": SOURCE_FINGERPRINT,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
        **overrides,
    }


def _signal(
    symbol: str,
    score: float,
    *,
    hypothesis_id: str | None = None,
    strategy: str = "rsi_threshold_exit",
    signal_time: datetime | None = None,
    ready: bool = True,
) -> dict:
    return {
        "symbol": symbol,
        "hypothesis_id": hypothesis_id or f"{symbol.lower()}-hypothesis",
        "strategy": strategy,
        "new_entry_ready": ready,
        "local_evidence_positive": True,
        "applicability_score": score,
        "signal_bar_time": (
            signal_time or DECISION_TIME - timedelta(minutes=30)
        ).isoformat(),
        "deployment_registry_sha256": REGISTRY_HASH,
        "execution_contract": "NEXT_OPEN_REPLAY",
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }


def _signals() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _signal("AAPL", 95),
            _signal("SPY", 85),
            _signal("MSFT", 75),
            _signal("NVDA", 65),
        ]
    )


def _eligibility() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAPL", "trade_eligible": True, "asset_type": "STOCK"},
            {"symbol": "SPY", "trade_eligible": True, "asset_type": "ETF"},
            {"symbol": "MSFT", "trade_eligible": True, "asset_type": "STOCK"},
            {"symbol": "NVDA", "trade_eligible": True, "asset_type": "STOCK"},
        ]
    )


def test_builds_strict_long_only_trade_intents():
    bundle = build_validated_portfolio_intents(
        _signals(),
        _audit(),
        _eligibility(),
        decision_time=DECISION_TIME,
        equity_eur=10_000.0,
    )

    assert len(bundle.intents) == 3
    assert len(bundle.decision_id) == 64
    assert bundle.projection.total_weight == pytest.approx(0.60)
    assert bundle.projection.cash_weight == pytest.approx(0.40)
    assert bundle.projection.rejected["NVDA"] == ("MAX_OPEN_POSITIONS",)
    assert all(intent.action is IntentAction.INCREASE for intent in bundle.intents)
    assert all(intent.execution_authority == "NONE" for intent in bundle.intents)
    assert all(
        intent.intent_id and len(intent.intent_id) == 64 for intent in bundle.intents
    )
    assert all(intent.target_weight >= 0.0 for intent in bundle.intents)
    assert all(
        intent.target_notional_eur == pytest.approx(intent.target_weight * 10_000.0)
        for intent in bundle.intents
    )
    assert bundle.audit["broker_calls"] == 0
    assert bundle.audit["order_calls"] == 0
    assert bundle.audit["execution_authority"] == "NONE"


def test_input_order_does_not_change_decision_or_intent_ids():
    first = build_validated_portfolio_intents(
        _signals(),
        _audit(),
        _eligibility(),
        decision_time=DECISION_TIME,
        equity_eur=10_000.0,
    )
    second = build_validated_portfolio_intents(
        _signals().sample(frac=1.0, random_state=42).reset_index(drop=True),
        _audit(),
        _eligibility().iloc[::-1].reset_index(drop=True),
        decision_time=DECISION_TIME,
        equity_eur=10_000.0,
    )

    assert second.decision_id == first.decision_id
    assert [intent.intent_id for intent in second.intents] == [
        intent.intent_id for intent in first.intents
    ]


def test_equity_and_current_weights_are_part_of_idempotency_key():
    baseline = build_validated_portfolio_intents(
        _signals(),
        _audit(),
        _eligibility(),
        decision_time=DECISION_TIME,
        equity_eur=10_000.0,
    )
    changed_equity = build_validated_portfolio_intents(
        _signals(),
        _audit(),
        _eligibility(),
        decision_time=DECISION_TIME,
        equity_eur=11_000.0,
    )
    changed_position = build_validated_portfolio_intents(
        _signals(),
        _audit(),
        _eligibility(),
        decision_time=DECISION_TIME,
        equity_eur=10_000.0,
        current_weights={"AAPL": 0.5},
    )

    assert changed_equity.decision_id != baseline.decision_id
    assert changed_position.decision_id != baseline.decision_id
    aapl = next(
        intent for intent in changed_position.intents if intent.symbol == "AAPL"
    )
    assert aapl.action is IntentAction.DECREASE


@pytest.mark.parametrize(
    ("signal_time", "reason"),
    [
        (DECISION_TIME + timedelta(minutes=1), "POINT_IN_TIME_VIOLATION"),
        (DECISION_TIME - timedelta(hours=3), "STALE_SIGNAL"),
    ],
)
def test_noncausal_or_stale_signal_is_rejected(signal_time: datetime, reason: str):
    signals = pd.DataFrame([_signal("AAPL", 95, signal_time=signal_time)])
    eligibility = _eligibility().loc[lambda frame: frame["symbol"] == "AAPL"]

    bundle = build_validated_portfolio_intents(
        signals,
        _audit(),
        eligibility,
        decision_time=DECISION_TIME,
        equity_eur=10_000.0,
    )

    assert bundle.intents == ()
    assert reason in bundle.projection.rejected["AAPL"]
    assert bundle.audit["point_in_time_validated"] is True


def test_unverified_or_missing_shariah_status_is_rejected():
    signals = pd.DataFrame(
        [
            _signal("AAPL", 95),
            _signal("UNKNOWN", 90),
        ]
    )
    eligibility = pd.DataFrame(
        [{"symbol": "AAPL", "trade_eligible": False, "asset_type": "STOCK"}]
    )

    bundle = build_validated_portfolio_intents(
        signals,
        _audit(),
        eligibility,
        decision_time=DECISION_TIME,
        equity_eur=10_000.0,
    )

    assert bundle.intents == ()
    assert bundle.projection.rejected["AAPL"] == ("SHARIAH_NOT_VERIFIED",)
    assert bundle.projection.rejected["UNKNOWN"] == ("SHARIAH_ELIGIBILITY_MISSING",)


@pytest.mark.parametrize(
    ("audit_update", "match"),
    [
        ({"execution_authority": "LIVE"}, "grants execution authority"),
        ({"broker_calls": 1}, "has broker calls"),
        ({"automatic_live_promotion": True}, "live promotion"),
        ({"strict_validated_deployment_gate": False}, "strict validated"),
    ],
)
def test_unsafe_signal_audit_fails_closed(audit_update: dict, match: str):
    with pytest.raises(ValueError, match=match):
        build_validated_portfolio_intents(
            _signals(),
            _audit(**audit_update),
            _eligibility(),
            decision_time=DECISION_TIME,
            equity_eur=10_000.0,
        )


def test_registry_tampering_fails_closed():
    signals = _signals()
    signals.loc[0, "deployment_registry_sha256"] = "c" * 64

    with pytest.raises(ValueError, match="registry hash"):
        build_validated_portfolio_intents(
            signals,
            _audit(),
            _eligibility(),
            decision_time=DECISION_TIME,
            equity_eur=10_000.0,
        )


@pytest.mark.parametrize(
    ("column", "value", "match"),
    [
        ("execution_authority", "LIVE", "grants execution authority"),
        ("broker_calls", 1, "non-zero broker_calls"),
        ("order_calls", 1, "non-zero order_calls"),
    ],
)
def test_unsafe_signal_row_fails_closed(column: str, value, match: str):
    signals = _signals()
    signals.loc[0, column] = value

    with pytest.raises(ValueError, match=match):
        build_validated_portfolio_intents(
            signals,
            _audit(),
            _eligibility(),
            decision_time=DECISION_TIME,
            equity_eur=10_000.0,
        )


@pytest.mark.parametrize(
    ("weights", "match"),
    [
        ({"AAPL": -0.01}, "short exposure"),
        ({"AAPL": 0.7, "SPY": 0.4}, "leverage"),
    ],
)
def test_current_portfolio_cannot_contain_short_or_leverage(weights, match: str):
    with pytest.raises(ValueError, match=match):
        build_validated_portfolio_intents(
            _signals(),
            _audit(),
            _eligibility(),
            decision_time=DECISION_TIME,
            equity_eur=10_000.0,
            current_weights=weights,
        )


def test_multiple_strategy_votes_are_aggregated_per_symbol():
    signals = pd.DataFrame(
        [
            _signal("AAPL", 90, hypothesis_id="rsi", strategy="rsi_threshold_exit"),
            _signal("AAPL", 80, hypothesis_id="obv", strategy="obv_breakout"),
        ]
    )
    eligibility = _eligibility().loc[lambda frame: frame["symbol"] == "AAPL"]
    policy = DecisionGatewayPolicy(minimum_strategy_votes=2)

    bundle = build_validated_portfolio_intents(
        signals,
        _audit(),
        eligibility,
        decision_time=DECISION_TIME,
        equity_eur=10_000.0,
        policy=policy,
    )

    assert len(bundle.intents) == 1
    assert bundle.intents[0].metadata["strategy_ids"] == [
        "obv_breakout",
        "rsi_threshold_exit",
    ]
    assert bundle.intents[0].metadata["hypothesis_ids"] == ["obv", "rsi"]


def test_allocator_honors_instrument_and_total_caps():
    cutoff = DECISION_TIME - timedelta(minutes=30)
    proposals = [
        AlphaProposal(
            symbol="AAPL",
            asset_kind=AssetKind.STOCK,
            alpha_score=1.0,
            confidence=1.0,
            data_cutoff=cutoff,
            strategy_ids=("rsi",),
            hypothesis_ids=("a",),
            shariah_eligible=True,
        ),
        AlphaProposal(
            symbol="SPY",
            asset_kind=AssetKind.ETF,
            alpha_score=0.1,
            confidence=1.0,
            data_cutoff=cutoff,
            strategy_ids=("obv",),
            hypothesis_ids=("b",),
            shariah_eligible=True,
        ),
    ]

    result = project_long_only(
        proposals,
        policy=AllocationPolicy(
            max_total_weight=0.60,
            max_stock_weight=0.35,
            max_etf_weight=0.40,
            max_open_positions=2,
            minimum_confidence=0.0,
        ),
    )
    by_symbol = {target.symbol: target for target in result.targets}

    assert result.total_weight == pytest.approx(0.60)
    assert by_symbol["AAPL"].target_weight == pytest.approx(0.35)
    assert by_symbol["SPY"].target_weight == pytest.approx(0.25)


def test_from_project_reads_only_validated_v219_artifacts(tmp_path: Path):
    signal_root = (
        tmp_path / "artifacts/research_runtime/validated_forward_signal_state_v2_19"
    )
    signal_root.mkdir(parents=True)
    _signals().to_csv(signal_root / "signals.csv", index=False)
    (signal_root / "audit.json").write_text(
        json.dumps(_audit()),
        encoding="utf-8",
    )
    eligibility_path = (
        tmp_path
        / "artifacts/research_runtime/shariah_financial_verification/verification.csv"
    )
    eligibility_path.parent.mkdir(parents=True)
    _eligibility().to_csv(eligibility_path, index=False)

    bundle = build_validated_portfolio_intents_from_project(
        tmp_path,
        decision_time=DECISION_TIME,
        equity_eur=10_000.0,
    )

    assert len(bundle.intents) == 3
    assert bundle.audit["deployment_registry_sha256"] == REGISTRY_HASH


def test_trade_intent_rejects_non_hash_id():
    with pytest.raises(ValueError, match="SHA-256"):
        TradeIntent(
            created_at=DECISION_TIME,
            symbol="AAPL",
            action=IntentAction.INCREASE,
            target_weight=0.1,
            target_notional_eur=1000.0,
            confidence=0.8,
            intent_id="not-a-hash",
        )


def test_v220_source_has_no_broker_or_order_submission_imports():
    root = Path(__file__).resolve().parents[1]
    sources = [
        root / "src/stocks/orchestration/validated_portfolio_gateway_v2_20.py",
        root / "src/stocks/portfolio/deterministic_allocator_v2_20.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources)

    assert "ib_insync" not in text
    assert "ibapi" not in text
    assert "placeOrder" not in text
    assert "submit_order" not in text
