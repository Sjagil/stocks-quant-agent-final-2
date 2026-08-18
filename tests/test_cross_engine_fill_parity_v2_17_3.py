from __future__ import annotations

from pathlib import Path

from stocks.integrations.stocks_donor_contract_v2_17_1 import (
    classify_donor_worktree_status,
)

ROOT = Path(__file__).resolve().parents[1]


def test_expected_local_macos_lock_is_not_contract_dirty():
    audit = classify_donor_worktree_status(
        "?? requirements.macos.lock.txt\n"
    )
    assert audit["raw_clean"] is False
    assert audit["clean_for_contract"] is True
    assert audit["unexpected_status_lines"] == []


def test_other_untracked_file_remains_contract_dirty():
    audit = classify_donor_worktree_status(
        "?? surprise.txt\n"
    )
    assert audit["clean_for_contract"] is False
    assert audit["unexpected_status_lines"] == ["?? surprise.txt"]


def test_tracked_donor_change_remains_contract_dirty():
    audit = classify_donor_worktree_status(
        " M src/stocks/portfolio/orchestrator.py\n"
    )
    assert audit["clean_for_contract"] is False


def test_pybroker_uses_actual_order_fill_ledger():
    text = (
        ROOT / "scripts/workers/pybroker_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "_normalize_order_fill_ledger" in text
    assert "result.orders.copy()" in text
    assert '"normalization_source": "ORDER_FILL_REPORT"' in text


def test_nautilus_has_version_safe_backtest_config_import():
    text = (
        ROOT / "scripts/workers/nautilus_crosscheck_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "nautilus_trader.backtest.config" in text
    assert "nautilus_trader.model.instruments import Equity" in text
    assert "Equity(" in text
    assert "QuoteTick(" in text
    assert (
        "SYNTHETIC_ZERO_SPREAD_QUOTE_TICK_AT_CANONICAL_OPEN"
        in text
    )
