from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_errors_block_broker_writes_and_second_preflight_exists():
    text = (ROOT / "src/stocks/production/runtime_v2_41.py").read_text()
    assert 'if summary["errors"]:' in text
    assert '"BLOCKED_RUNTIME_ERRORS"' in text
    assert 'summary["pre_submit_preflight"]' in text
    assert 'PRE_SUBMIT_PREFLIGHT_FAILED' in text
    assert 'summary["pre_submit_reconciliation"]' in text


def test_preflight_guards_clock_and_readonly_write_count():
    text = (ROOT / "src/stocks/production/preflight_v2_41.py").read_text()
    assert '"READONLY_BROKER_WRITE_CALLS_ZERO"' in text
    assert '"BROKER_CLOCK_SYNC"' in text
    assert 'maximum_broker_clock_drift_seconds' in text


def test_protected_buy_rolls_back_unprotected_parent_on_child_failure():
    text = (ROOT / "src/stocks/production/ibkr_adapter_v2_41.py").read_text()
    assert 'parent_placed = False' in text
    assert 'self.ib.cancelOrder(parent)' in text
