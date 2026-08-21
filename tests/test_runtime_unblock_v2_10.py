from __future__ import annotations
import pandas as pd
from stocks.orchestration.runtime_unblock_v2_10 import (
    attestation_template, build_attestation_queue, choose_open_port
)

def test_choose_configured_open_port_first():
    assert choose_open_port(7497, {7497: True, 7496: True}) == 7497

def test_choose_alternate_open_port():
    assert choose_open_port(7497, {7497: False, 7496: True}) == 7496

def test_no_open_port_returns_none():
    assert choose_open_port(7497, {7497: False, 7496: False}) is None

def test_attestation_queue_only_contains_passes():
    source = pd.DataFrame([
        {"symbol":"AAA","status":"FINANCIAL_SCREEN_PASS_ATTESTATION_REQUIRED","debt_to_market_cap":0.1},
        {"symbol":"BBB","status":"SHARIAH_INELIGIBLE_FINANCIAL_RATIOS","debt_to_market_cap":0.8},
        {"symbol":"CCC","status":"SHARIAH_DATA_INCOMPLETE"},
    ])
    queue = build_attestation_queue(source)
    assert list(queue["symbol"]) == ["AAA"]
    assert queue.iloc[0]["review_status"] == "PENDING_EXTERNAL_SHARIAH_ATTESTATION"

def test_template_never_marks_compliant_automatically():
    queue = pd.DataFrame([{
        "symbol":"AAA","status":"FINANCIAL_SCREEN_PASS_ATTESTATION_REQUIRED",
        "debt_to_market_cap":0.1,"cash_to_market_cap":0.1,"receivables_to_market_cap":0.1
    }])
    payload = attestation_template(queue, as_of="2026-08-14")
    assert payload["automatic_attestation"] is False
    assert payload["attestations"][0]["status"] == "PENDING_REVIEW"
