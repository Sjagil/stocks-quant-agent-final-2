from __future__ import annotations

import pytest

from stocks.research.contextual_discovery import (
    ContextualDiscoveryPolicy,
    canonicalize_contextual_candidates,
)

POLICY = ContextualDiscoveryPolicy(25_000_000_000, 65.0, 0.025, 45.0, 4.0, 150)


def _record(symbol: str, classification: str, total: float) -> dict:
    return {
        "symbol": symbol,
        "asset_key": symbol,
        "asset_type": "STOCK",
        "sector": "Technology",
        "industry": "Semiconductors",
        "source_classification": classification,
        "classification": classification,
        "total_score": total,
        "research_score": total,
        "fundamental_score": 60.0,
        "technical_score": 70.0,
        "liquidity_score": 80.0,
        "risk_score": 70.0,
        "macro_score": 62.0,
        "macro_context": {
            "macro_regime": "RISK_ON",
            "macro_confidence": 0.8,
            "macro_data_status": "GO",
            "sector_macro_tailwind": "POSITIVE",
            "region_macro_tailwind": "POSITIVE",
            "currency_regime": "USD_FIRM",
            "commodity_regime": "MIXED",
            "market_breadth": 0.6,
        },
        "market_cap": 10_000_000_000,
        "daily_return": 0.01,
        "rejection_reasons": [],
        "trade_blockers": [],
        "research_blockers": [],
        "trade_eligible": True,
        "research_eligible": True,
        "shariah_gate": "VERIFIED",
        "shariah_verification_required": False,
        "selection_reasons": [],
        "warnings": [],
        "shariah_status": "SHARIAH_ELIGIBLE_PIT",
        "fundamental_coverage": 0.8,
        "fundamental_applicability": "COMPANY_LEVEL",
        "data_timestamps": {
            "price_session": "2026-08-14",
            "price_source_timestamp": "2026-08-14T20:00:00+00:00",
            "fundamental_available_at": "2026-08-13T12:00:00+00:00",
            "shariah_screened_at": "2026-08-01T00:00:00+00:00",
        },
        "sec_context": {
            "status": "GO",
            "as_of": "2026-08-14T20:15:00+00:00",
            "causal_event_count": 3,
            "sec_intelligence_score": 1.0,
            "overlay": {"sec_overlay_points": 4.0, "entry_authorized": False},
            "authority": "RANKING_OVERLAY_ONLY",
            "standalone_entry_allowed": False,
        },
        "execution_authority": "NONE",
    }


def _payload(records):
    return {
        "schema": "stocks_reference_contextual_candidates_v2",
        "screening_date": "2026-08-14",
        "decision_time": "2026-08-14T20:15:00+00:00",
        "records": records,
        "execution_authority": "NONE",
        "strategy_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }


def test_neutral_enters_research_watchlist():
    frame, audit = canonicalize_contextual_candidates(
        _payload([_record("AMD", "NEUTRAL", 55.0)]), POLICY
    )
    assert frame.iloc[0]["lane"] == "WATCHLIST"
    assert audit["neutral_source_count"] == 1


def test_sec_overlay_changes_rank_not_classification():
    a = _record("AMD", "WATCHLIST", 65.0)
    b = _record("MSFT", "WATCHLIST", 67.0)
    b["sec_context"]["overlay"]["sec_overlay_points"] = 0.0
    frame, _ = canonicalize_contextual_candidates(_payload([a, b]), POLICY)
    assert list(frame["symbol"]) == ["AMD", "MSFT"]


def test_high_potential_small_cap_routes_to_gem():
    frame, _ = canonicalize_contextual_candidates(
        _payload([_record("ON", "HIGH_POTENTIAL", 78.0)]), POLICY
    )
    assert frame.iloc[0]["lane"] == "GEM"


def test_future_evidence_is_rejected():
    r = _record("AMD", "WATCHLIST", 65.0)
    r["data_timestamps"]["fundamental_available_at"] = "2026-08-15T00:00:00+00:00"
    with pytest.raises(ValueError, match="future information"):
        canonicalize_contextual_candidates(_payload([r]), POLICY)


def test_sec_overlay_bound_is_enforced():
    r = _record("AMD", "WATCHLIST", 65.0)
    r["sec_context"]["overlay"]["sec_overlay_points"] = 4.01
    with pytest.raises(ValueError, match="SEC overlay exceeds"):
        canonicalize_contextual_candidates(_payload([r]), POLICY)


def test_below_research_floor_is_rejected():
    r = _record("AMD", "REJECTED", 20.0)
    r["research_score"] = 44.9
    r["trade_eligible"] = False
    with pytest.raises(ValueError, match="below research-pool"):
        canonicalize_contextual_candidates(_payload([r]), POLICY)


def test_sec_cannot_claim_standalone_entry_authority():
    r = _record("AMD", "WATCHLIST", 65.0)
    r["sec_context"]["standalone_entry_allowed"] = True
    with pytest.raises(ValueError, match="standalone entry authority"):
        canonicalize_contextual_candidates(_payload([r]), POLICY)


def test_macro_fields_are_preserved():
    frame, audit = canonicalize_contextual_candidates(
        _payload([_record("AMD", "WATCHLIST", 65.0)]), POLICY
    )
    assert frame.iloc[0]["macro_regime"] == "RISK_ON"
    assert audit["macro_go_count"] == 1


def test_rejected_source_can_be_recovered_for_research_only():
    r = _record("GEMX", "REJECTED", 30.0)
    r["research_score"] = 71.0
    r["trade_eligible"] = False
    r["trade_blockers"] = ["MISSING_FUNDAMENTAL_DATA"]
    r["shariah_gate"] = "VERIFIED"
    frame, audit = canonicalize_contextual_candidates(_payload([r]), POLICY)
    assert frame.iloc[0]["lane"] == "RESEARCH_ONLY"
    assert audit["rejected_source_recovered_count"] == 1
    assert audit["trade_eligible_count"] == 0


def test_pending_shariah_is_research_only_not_tradeable():
    r = _record("PEND", "REJECTED", 25.0)
    r["research_score"] = 68.0
    r["trade_eligible"] = False
    r["trade_blockers"] = ["SHARIAH_DATA_UNAVAILABLE"]
    r["shariah_gate"] = "PENDING"
    r["shariah_verification_required"] = True
    r["shariah_status"] = "SHARIAH_DATA_UNAVAILABLE"
    frame, audit = canonicalize_contextual_candidates(_payload([r]), POLICY)
    assert frame.iloc[0]["lane"] == "PENDING_SHARIAH"
    assert audit["pending_shariah_count"] == 1
    assert not bool(frame.iloc[0]["trade_eligible"])


def test_research_blocker_leak_is_rejected():
    r = _record("BAD", "REJECTED", 55.0)
    r["trade_eligible"] = False
    r["research_blockers"] = ["STALE_PRICE_DATA"]
    with pytest.raises(ValueError, match="research blockers leaked"):
        canonicalize_contextual_candidates(_payload([r]), POLICY)


def test_pending_shariah_preserves_research_lane():
    from stocks.research.contextual_discovery import (
        ContextualDiscoveryPolicy,
        canonicalize_contextual_candidates,
    )

    policy = ContextualDiscoveryPolicy(
        minimum_research_pool_total_score=45.0,
        gem_market_cap_ceiling_usd=25_000_000_000.0,
        tactical_min_technical_score=65.0,
        tactical_min_absolute_daily_return=2.5,
        maximum_candidates=150,
        maximum_sec_overlay_points=4.0,
    )

    payload = {
        "schema": "stocks_reference_contextual_candidates_v2",
        "screening_date": "2026-08-14",
        "decision_time": "2026-08-15T00:00:00Z",
        "execution_authority": "NONE",
        "strategy_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
        "records": [
            {
                "symbol": "XYZ",
                "asset_type": "STOCK",
                "source_classification": "WATCHLIST",
                "research_lane": "GEM",
                "research_eligible": True,
                "trade_eligible": False,
                "research_blockers": [],
                "trade_blockers": ["SHARIAH_DATA_UNAVAILABLE"],
                "shariah_gate": "PENDING",
                "total_score": 80.0,
                "research_score": 80.0,
                "fundamental_score": 65.0,
                "technical_score": 80.0,
                "liquidity_score": 70.0,
                "risk_score": 60.0,
                "market_cap": 2_000_000_000.0,
                "daily_return": 3.0,
                "data_timestamps": {"price_session": "2026-08-14"},
                "execution_authority": "NONE",
            }
        ],
    }

    frame, audit = canonicalize_contextual_candidates(payload, policy)
    assert frame.iloc[0]["lane"] == "PENDING_SHARIAH"
    assert frame.iloc[0]["research_lane"] == "GEM"
    assert audit["research_gem_count"] == 1
