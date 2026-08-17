from __future__ import annotations

import pandas as pd

from stocks.research.cross_engine_validation_v2_17 import (
    aggregate_engine_status,
    canonical_packet_hash,
    compare_ledgers,
)


def _ledger() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_id": "h:A:000001",
                "hypothesis_id": "h",
                "strategy": "s",
                "base_symbol": "A",
                "replay_symbol": "A__PB0",
                "entry_time": pd.Timestamp(
                    "2026-01-02 15:30", tz="UTC"
                ),
                "exit_time": pd.Timestamp(
                    "2026-01-05 15:30", tz="UTC"
                ),
                "entry_price": 100.0,
                "exit_price": 105.0,
                "quantity": 1,
                "gross_return": 0.05,
                "base_net_return": 0.0494,
                "stress_net_return": 0.048,
                "execution_contract": "NEXT_OPEN_REPLAY",
            }
        ]
    )


def test_packet_hash_is_deterministic():
    left = canonical_packet_hash(_ledger())
    right = canonical_packet_hash(_ledger())
    assert left == right


def test_exact_ledger_passes():
    expected = _ledger()
    observed = _ledger()
    _, audit = compare_ledgers(
        expected,
        observed,
        max_fill_price_relative_error=1e-8,
        max_trade_return_difference_bps=0.05,
    )
    assert audit["parity"] is True


def test_timestamp_mismatch_fails():
    expected = _ledger()
    observed = _ledger()
    observed.loc[0, "exit_time"] = pd.Timestamp(
        "2026-01-05 16:30", tz="UTC"
    )
    _, audit = compare_ledgers(
        expected,
        observed,
        max_fill_price_relative_error=1e-8,
        max_trade_return_difference_bps=0.05,
    )
    assert audit["parity"] is False


def test_price_mismatch_fails():
    expected = _ledger()
    observed = _ledger()
    observed.loc[0, "exit_price"] = 104.0
    observed.loc[0, "gross_return"] = 0.04
    _, audit = compare_ledgers(
        expected,
        observed,
        max_fill_price_relative_error=1e-8,
        max_trade_return_difference_bps=0.05,
    )
    assert audit["parity"] is False


def test_trade_count_mismatch_fails():
    expected = pd.concat([_ledger(), _ledger()], ignore_index=True)
    observed = _ledger()
    _, audit = compare_ledgers(
        expected,
        observed,
        max_fill_price_relative_error=1e-8,
        max_trade_return_difference_bps=0.05,
    )
    assert audit["parity"] is False


def test_all_four_full_engines_required():
    rows = [
        {
            "engine": name,
            "mode": "FULL_ENGINE_REPLAY",
            "parity": True,
            "symbols": 10,
            "trades": 500,
        }
        for name in ("native", "pybroker", "nautilus", "lean")
    ]
    result = aggregate_engine_status(
        rows,
        required_engines=("native", "pybroker", "nautilus", "lean"),
        minimum_symbols=5,
        minimum_total_trades=100,
    )
    assert result["status"] == "CROSS_ENGINE_VALIDATED"


def test_source_only_lean_blocks_validation():
    rows = [
        {
            "engine": "native",
            "mode": "FULL_ENGINE_REPLAY",
            "parity": True,
            "symbols": 10,
            "trades": 500,
        },
        {
            "engine": "pybroker",
            "mode": "FULL_ENGINE_REPLAY",
            "parity": True,
        },
        {
            "engine": "nautilus",
            "mode": "FULL_ENGINE_REPLAY",
            "parity": True,
        },
        {
            "engine": "lean",
            "mode": "BLOCKED_FULL_ENGINE_REPLAY",
            "parity": False,
        },
    ]
    result = aggregate_engine_status(
        rows,
        required_engines=("native", "pybroker", "nautilus", "lean"),
        minimum_symbols=5,
        minimum_total_trades=100,
    )
    assert result["status"] == "CROSS_ENGINE_NOT_VALIDATED"
    assert "LEAN_FULL_REPLAY_REQUIRED" in result["blockers"]


def test_fractional_observation_fails_parity():
    expected = _ledger()
    observed = _ledger()
    observed["quantity"] = observed["quantity"].astype(float)
    observed.loc[0, "quantity"] = 0.5
    _, audit = compare_ledgers(
        expected,
        observed,
        max_fill_price_relative_error=1e-8,
        max_trade_return_difference_bps=0.05,
    )
    assert audit["parity"] is False


def test_missing_survivor_artifact_fails_closed_without_traceback():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    text = (
        root
        / "scripts/run_cross_engine_strategy_validation_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "except FileNotFoundError as exc" in text
    assert '"CROSS_ENGINE_PREFLIGHT"' in text
    assert 'print("EXECUTION_AUTHORITY", "NONE")' in text
    assert "return 2" in text
