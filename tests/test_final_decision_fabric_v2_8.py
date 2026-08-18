from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from stocks.orchestration.strategy_forward_signals import (
    research_entry_ready,
)
from stocks.research.final_strategy_roster import (
    build_final_strategy_roster,
)
from stocks.research.sec_fundamentals import (
    select_sec_fact,
)
from stocks.research.shariah_financial_verification import (
    evaluate_financials,
)


def test_sec_fact_selection_rejects_future_filing():
    companyfacts = {
        "facts": {
            "us-gaap": {
                "LongTermDebtNoncurrent": {
                    "units": {
                        "USD": [
                            {
                                "end": "2026-03-31",
                                "filed": "2026-05-01",
                                "form": "10-Q",
                                "val": 100.0,
                            },
                            {
                                "end": "2026-06-30",
                                "filed": "2026-08-20",
                                "form": "10-Q",
                                "val": 200.0,
                            },
                        ]
                    }
                }
            }
        }
    }

    fact = select_sec_fact(
        companyfacts,
        concepts=["LongTermDebtNoncurrent"],
        decision_date=date(2026, 8, 14),
    )

    assert fact is not None
    assert fact["value"] == 100.0
    assert fact["end"].isoformat() == "2026-03-31"


def test_financial_screen_without_attestation_is_not_trade_eligible():
    payload = {
        "General": {
            "Name": "Example Technology",
            "Sector": "Technology",
            "Industry": "Software",
        },
        "Highlights": {
            "MarketCapitalization": 1_000.0,
        },
        "Financials": {
            "Balance_Sheet": {
                "quarterly": {
                    "2026-06-30": {
                        "date": "2026-06-30",
                        "filing_date": "2026-08-01",
                        "shortTermDebt": 10.0,
                        "longTermDebt": 100.0,
                        "cashAndShortTermInvestments": 100.0,
                        "netReceivables": 100.0,
                    }
                }
            }
        },
    }

    result = evaluate_financials(
        "TEST",
        payload,
        decision_date=date(2026, 8, 14),
        policy={
            "debt_to_market_cap_max": 0.30,
            "cash_and_interest_securities_to_market_cap_max": 0.30,
            "receivables_to_market_cap_max": 0.49,
            "maximum_attestation_age_days": 120,
        },
        attestation=None,
    )

    assert (
        result.status
        == "FINANCIAL_SCREEN_PASS_ATTESTATION_REQUIRED"
    )
    assert result.trade_eligible is False


def test_active_replay_position_blocks_duplicate_fresh_entry():
    assert (
        research_entry_ready(
            local_evidence_positive=True,
            source_setup_state="ACTIVE_AT_DATA_BOUNDARY",
            trigger_ready=True,
        )
        is False
    )


def test_flat_strategy_can_surface_new_closed_bar_trigger():
    assert (
        research_entry_ready(
            local_evidence_positive=True,
            source_setup_state="DORMANT",
            trigger_ready=True,
        )
        is True
    )


def test_validated_15m_champion_is_promoted(tmp_path: Path):
    registry_root = (
        tmp_path
        / "artifacts/research_runtime/"
        "research_candidate_registry"
    )
    registry_root.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "hypothesis_id": "market-champion",
                "strategy": "market_structure_atr_pullback",
                "family": "breakout_pullback",
                "generalization_status": "ROUTE_TO_15M_GENERALIZATION",
                "promotion_stage": "FINALIST_CANDIDATE",
                "execution_contract": "REAL_15M_CHRONOLOGY",
            }
        ]
    ).to_csv(
        registry_root / "registry.csv",
        index=False,
    )

    execution_root = (
        tmp_path
        / "artifacts/research_runtime/"
        "market_structure_15m_execution"
    )
    execution_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "hypothesis_id": "market-champion",
                "median_stress_expectancy_bps": 50.0,
                "median_resolved_profit_factor": 2.0,
            }
        ]
    ).to_csv(
        execution_root / "summary.csv",
        index=False,
    )

    broad_root = (
        tmp_path
        / "artifacts/research_runtime/"
        "market_structure_15m_generalization"
    )
    broad_root.mkdir(parents=True)
    (
        broad_root / "audit.json"
    ).write_text(
        json.dumps(
            {
                "hypothesis_id": "market-champion",
                "status": "15M_DYNAMIC_UNIVERSE_VALIDATED",
                "eligible_symbols": 16,
                "traded_symbols": 16,
                "oos_trades": 1265,
                "positive_fold_ratio": 1.0,
                "stress_positive_fold_ratio": 1.0,
                "positive_symbol_ratio": 0.90,
                "stress_positive_symbol_ratio": 0.80,
                "median_expectancy_bps": 40.0,
                "median_stress_expectancy_bps": 25.0,
                "max_symbol_trade_share": 0.10,
            }
        ),
        encoding="utf-8",
    )

    config = tmp_path / "config"
    config.mkdir()
    (
        config / "final_decision_fabric_v2_8.json"
    ).write_text(
        json.dumps(
            {
                "market_structure_promotion": {
                    "required_status": "15M_DYNAMIC_UNIVERSE_VALIDATED",
                    "minimum_eligible_symbols": 12,
                    "minimum_traded_symbols": 12,
                    "minimum_oos_trades": 500,
                    "minimum_positive_fold_ratio": 0.75,
                    "minimum_stress_positive_fold_ratio": 0.75,
                    "minimum_positive_symbol_ratio": 0.60,
                    "minimum_stress_positive_symbol_ratio": 0.50,
                    "maximum_symbol_trade_share": 0.35,
                    "require_positive_median_expectancy": True,
                    "require_positive_median_stress_expectancy": True,
                }
            }
        ),
        encoding="utf-8",
    )

    frame, audit = build_final_strategy_roster(tmp_path)

    assert len(frame) == 1
    assert (
        frame.iloc[0]["roster_status"]
        == "BROADLY_VALIDATED_FINALIST"
    )
    assert audit["validated_15m_champions"] == 1
    assert audit["pending_15m_champions"] == 0
