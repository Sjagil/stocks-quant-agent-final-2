from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nautilus_replay_uses_matching_synthetic_precision():
    text = (
        ROOT / "scripts/workers/nautilus_crosscheck_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "REPLAY_PRICE_PRECISION = 8" in text
    assert 'REPLAY_PRICE_INCREMENT = "0.00000001"' in text
    assert "QuoteTick(" in text
    assert "bid_price=px" in text
    assert "ask_price=px" in text
    assert "price_precision=REPLAY_PRICE_PRECISION" in text
    assert "price_increment=Price.from_str(" in text
    assert "REPLAY_PRICE_INCREMENT" in text
    assert "lot_size=Quantity.from_int(1)" in text


def test_nautilus_replay_does_not_round_to_cents():
    text = (
        ROOT / "scripts/workers/nautilus_crosscheck_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert 'Price.from_str("0.01")' not in text
    assert "TestInstrumentProvider.equity" not in text


def test_deep_parity_audit_searches_nested_strategy_artifacts():
    text = (
        ROOT / "scripts/audit_cross_engine_outputs_v2_17_4.py"
    ).read_text(encoding="utf-8")

    assert "ART.rglob" in text
    assert "MISMATCH_ROWS" in text
    assert "trade_match_ratio" in text


def test_lean_setup_is_isolated_and_no_live_authority():
    text = (
        ROOT / "scripts/setup_lean_runtime_v2_17_4.py"
    ).read_text(encoding="utf-8")

    assert ".venvs/lean-cli" in text
    assert '"lean"' in text
    assert "LEAN_CANONICAL_DATA_ADAPTER_IMPLEMENTED False" in text
    assert "EXECUTION_AUTHORITY NONE" in text
