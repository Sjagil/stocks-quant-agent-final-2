from __future__ import annotations

from pathlib import Path

from stocks.integrations.stocks_donor_contract_v2_17_1 import (
    build_stocks_donor_contract,
)


ROOT = Path(__file__).resolve().parents[1]


def test_stocks_donor_contract_is_fail_closed_and_single_writer():
    audit = build_stocks_donor_contract(ROOT)
    assert audit["whole_shares_only"] is True
    assert audit["fractional_shares_allowed"] is False
    assert audit["fixed_euro_order_cap"] is False
    assert audit["automatic_live_promotion"] is False
    assert audit["donor_broker_writes"] == 0
    assert audit["execution_authority"] == "NONE"
    assert (
        audit["canonical_broker_writer"]
        == "stocks.live.service.live_submit_authorized"
    )


def test_active_donor_workers_are_wired():
    audit = build_stocks_donor_contract(ROOT)
    workers = {row["integration"]: row for row in audit["active_workers"]}
    assert workers["stocks_reference"]["active_contract_ready"] is True
    assert workers["stocks_ibkr_reference"]["active_contract_ready"] is True


def test_account_state_is_approved_read_only_source():
    audit = build_stocks_donor_contract(ROOT)
    sources = {row["path"]: row for row in audit["approved_sources"]}
    account = sources["src/stocks/ibkr/reconciliation/account_state.py"]
    assert account["contract_ready"] is True
    assert account["reuse_mode"] == "ISOLATED_READ_ONLY_FUNCTIONAL"


def test_execution_bridge_is_pattern_not_direct_runtime_import():
    audit = build_stocks_donor_contract(ROOT)
    sources = {row["path"]: row for row in audit["approved_sources"]}
    bridge = sources["src/stocks/portfolio/execution_bridge.py"]
    assert bridge["contract_ready"] is True
    assert bridge["reuse_mode"] == "ADAPT_SEMANTICS_NOT_IMPORT"


def test_fixed_euro_canary_source_is_quarantined():
    audit = build_stocks_donor_contract(ROOT)
    quarantine = {row["path"]: row for row in audit["quarantine"]}
    canary = quarantine["src/stocks/capital/canary.py"]
    assert canary["direct_reuse_allowed"] is False
    assert canary["quarantine_enforced"] is True
    assert "hard_notional_cap_eur" in canary["detected_forbidden_markers"]


def test_donor_live_writer_is_never_a_second_writer():
    audit = build_stocks_donor_contract(ROOT)
    quarantine = {row["path"]: row for row in audit["quarantine"]}
    assert quarantine["src/stocks/live/service.py"]["direct_reuse_allowed"] is False
    assert audit["direct_donor_package_import"] is False
    assert audit["donor_live_writer_imported"] is False
