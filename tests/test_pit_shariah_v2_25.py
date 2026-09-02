from __future__ import annotations

import pandas as pd

from stocks.research.pit_shariah_eligibility_v2_25 import (
    PASS_ATTESTATION_STATUS,
    VERIFIED_STATUS,
    attach_pit_shariah_to_training_frame_v225,
    build_attestation_queue_v225,
    build_historical_pit_shariah_ledger_v225,
    current_verification_to_pit_events_v225,
)


def _events():
    financial = pd.DataFrame([
        {
            "symbol": "AAA",
            "available_at": "2024-02-02T00:00:00Z",
            "report_date": "2023-12-31",
            "filing_date": "2024-02-01",
            "short_debt": 5.0,
            "long_debt": 10.0,
            "cash": 10.0,
            "receivables": 10.0,
        }
    ])
    market = pd.DataFrame([
        {"symbol": "AAA", "available_at": "2024-02-02T00:00:00Z", "market_cap": 100.0}
    ])
    business = pd.DataFrame([
        {"symbol": "AAA", "available_at": "2024-01-01T00:00:00Z", "business_status": "PASS"}
    ])
    attestation = pd.DataFrame([
        {
            "symbol": "AAA",
            "available_at": "2024-02-05T00:00:00Z",
            "status": "VERIFIED",
            "valid_until": "2024-06-01T00:00:00Z",
            "methodology": "TEST",
            "source": "https://example.invalid/evidence",
        }
    ])
    return financial, market, business, attestation


def test_historical_pit_ledger_never_backfills_future_evidence() -> None:
    financial, market, business, attestation = _events()
    decisions = pd.DataFrame([
        {"symbol": "AAA", "decision_time": "2024-02-01T12:00:00Z"},
        {"symbol": "AAA", "decision_time": "2024-02-03T12:00:00Z"},
        {"symbol": "AAA", "decision_time": "2024-02-06T12:00:00Z"},
    ])
    bundle = build_historical_pit_shariah_ledger_v225(
        decisions,
        financial_events=financial,
        market_cap_events=market,
        business_events=business,
        attestation_events=attestation,
    )
    assert bundle.audit["valid"] is True
    assert bundle.audit["future_evidence_rows"] == 0
    assert bundle.ledger.loc[0, "status"] == "SHARIAH_DATA_INCOMPLETE_PIT"
    assert bundle.ledger.loc[1, "status"] == PASS_ATTESTATION_STATUS
    assert bundle.ledger.loc[2, "status"] == VERIFIED_STATUS
    assert bool(bundle.ledger.loc[2, "trade_eligible"]) is True


def test_ratio_failure_remains_ineligible_even_with_attestation() -> None:
    financial, market, business, attestation = _events()
    financial.loc[0, "long_debt"] = 40.0
    decisions = pd.DataFrame([
        {"symbol": "AAA", "decision_time": "2024-02-06T12:00:00Z"}
    ])
    bundle = build_historical_pit_shariah_ledger_v225(
        decisions,
        financial_events=financial,
        market_cap_events=market,
        business_events=business,
        attestation_events=attestation,
    )
    row = bundle.ledger.iloc[0]
    assert row["status"] == "SHARIAH_INELIGIBLE_FINANCIAL_RATIOS"
    assert bool(row["trade_eligible"]) is False
    assert "DEBT_RATIO" in row["reason_codes"]


def test_training_join_uses_latest_known_shariah_state() -> None:
    financial, market, business, attestation = _events()
    decisions = pd.DataFrame([
        {"symbol": "AAA", "decision_time": "2024-02-03T12:00:00Z"},
        {"symbol": "AAA", "decision_time": "2024-02-06T12:00:00Z"},
    ])
    bundle = build_historical_pit_shariah_ledger_v225(
        decisions,
        financial_events=financial,
        market_cap_events=market,
        business_events=business,
        attestation_events=attestation,
    )
    training = pd.DataFrame([
        {"symbol": "AAA", "decision_time": "2024-02-04T00:00:00Z", "feature": 1.0},
        {"symbol": "AAA", "decision_time": "2024-02-07T00:00:00Z", "feature": 2.0},
    ])
    joined = attach_pit_shariah_to_training_frame_v225(training, bundle.ledger)
    assert joined.loc[0, "shariah_status"] == PASS_ATTESTATION_STATUS
    assert joined.loc[1, "shariah_status"] == VERIFIED_STATUS
    assert bool(joined.loc[1, "shariah_trade_eligible"]) is True
    assert (
        pd.to_datetime(joined["shariah_available_at"], utc=True)
        <= pd.to_datetime(joined["decision_time"], utc=True)
    ).all()


def test_current_verification_records_knowability_without_backfill() -> None:
    verification = pd.DataFrame([
        {
            "symbol": "AAA",
            "status": PASS_ATTESTATION_STATUS,
            "trade_eligible": False,
            "filing_date": "2024-02-01",
            "reason_codes": "VERIFIED_ATTESTATION_REQUIRED",
        }
    ])
    events = current_verification_to_pit_events_v225(
        verification,
        decision_time="2024-02-10T12:00:00Z",
    )
    assert events.loc[0, "available_at"] == pd.Timestamp("2024-02-02T00:00:00Z")
    assert bool(events.loc[0, "historical_backfill_allowed"]) is False
    assert events.loc[0, "execution_authority"] == "NONE"


def test_attestation_queue_is_manual_only() -> None:
    verification = pd.DataFrame([
        {"symbol": "AAA", "status": PASS_ATTESTATION_STATUS, "filing_date": "2024-02-01"},
        {"symbol": "BBB", "status": VERIFIED_STATUS, "filing_date": "2024-02-01"},
    ])
    queue = build_attestation_queue_v225(verification)
    assert queue["symbol"].tolist() == ["AAA"]
    assert queue["review_required"].tolist() == [True]
    assert queue["automatic_attestation"].tolist() == [False]
