from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pybroker_preserves_unrounded_result_prices():
    text = (
        ROOT / "scripts/workers/pybroker_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "round_fill_price=False" in text
    assert "round_test_result=False" in text


def test_nautilus_uses_quote_tick_sequenced_next_open_market_orders():
    text = (
        ROOT / "scripts/workers/nautilus_crosscheck_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "QuoteTick" in text
    assert "subscribe_quote_ticks" in text
    assert "def on_quote_tick(" in text
    assert 'work["execute_entry"]' in text
    assert 'work["execute_exit"]' in text
    assert text.count(".shift(1)") >= 2
    assert "TimeInForce.GTC" in text
    assert "TimeInForce.AT_THE_OPEN" not in text
    assert "def on_bar(" not in text
    assert "bar_execution=True" not in text
    assert "use_message_queue=True" not in text
    assert (
        "SYNTHETIC_ZERO_SPREAD_QUOTE_TICK_AT_CANONICAL_OPEN"
        in text
    )
    assert '"signals_shifted_rows": 1' in text
    assert '"execution_authority": "NONE"' in text


def test_nautilus_keeps_adjusted_precision_and_whole_shares():
    text = (
        ROOT / "scripts/workers/nautilus_crosscheck_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "REPLAY_PRICE_PRECISION = 8" in text
    assert 'REPLAY_PRICE_INCREMENT = "0.00000001"' in text
    assert "lot_size=Quantity.from_int(1)" in text


def test_deep_audit_tolerates_empty_parity_csv():
    text = (
        ROOT / "scripts/audit_cross_engine_outputs_v2_17_4.py"
    ).read_text(encoding="utf-8")

    assert "pd.errors.EmptyDataError" in text
    assert "path.stat().st_size == 0" in text


def test_completion_runner_is_non_authoritative():
    text = (
        ROOT / "scripts/run_cross_engine_completion_v2_17_5.py"
    ).read_text(encoding="utf-8")

    assert "BROKER_CALLS 0" in text
    assert "ORDER_CALLS 0" in text
    assert "EXECUTION_AUTHORITY NONE" in text
    assert "automatic_live_promotion" in text


def test_completion_runners_discover_every_v217_test():
    expected = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob(
            "test_cross_engine_*v2_17*.py"
        )
    }
    expected.add(
        "tests/test_stocks_donor_integration_v2_17_1.py"
    )

    for relative in (
        "scripts/run_cross_engine_completion_v2_17_5.py",
        "scripts/run_cross_engine_finalization_v2_17_7.py",
    ):
        namespace = runpy.run_path(str(ROOT / relative))
        assert set(namespace["focused_tests"]()) == expected
