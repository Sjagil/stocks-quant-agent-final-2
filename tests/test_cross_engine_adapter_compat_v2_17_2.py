from __future__ import annotations

from pathlib import Path

from stocks.research.cross_engine_validation_v2_17 import (
    aggregate_engine_status,
)

ROOT = Path(__file__).resolve().parents[1]


def test_pybroker_worker_matches_installed_api_contract():
    text = (
        ROOT / "scripts/workers/pybroker_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "        bootstrap=False," not in text
    assert "strategy.backtest(calc_bootstrap=False)" in text
    assert '"bootstrap_metrics": False' in text


def test_nautilus_worker_uses_test_kit_namespace():
    text = (
        ROOT / "scripts/workers/nautilus_crosscheck_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "nautilus_trader.testkit" not in text
    assert "TestInstrumentProvider" not in text
    assert "nautilus_trader.model.instruments import Equity" in text

def test_reporting_distinguishes_absent_from_non_validating_engines():
    rows = [
        {
            "engine": "native",
            "mode": "FULL_ENGINE_REPLAY",
            "parity": True,
            "symbols": 5,
            "trades": 358,
        },
        {
            "engine": "pybroker",
            "mode": "ERROR",
            "parity": False,
            "error": "synthetic",
        },
        {
            "engine": "nautilus",
            "mode": "ERROR",
            "parity": False,
            "error": "synthetic",
        },
        {
            "engine": "lean",
            "mode": "BLOCKED_FULL_ENGINE_REPLAY",
            "parity": False,
            "warnings": ["runtime unavailable"],
        },
    ]

    result = aggregate_engine_status(
        rows,
        required_engines=("native", "pybroker", "nautilus", "lean"),
        minimum_symbols=5,
        minimum_total_trades=100,
    )

    assert result["missing_engines"] == []
    assert set(result["non_validating_engines"]) == {
        "pybroker",
        "nautilus",
        "lean",
    }
    assert result["status"] == "CROSS_ENGINE_NOT_VALIDATED"


def test_adapter_compat_patch_does_not_change_authority_policy():
    rows = [
        {
            "engine": "native",
            "mode": "FULL_ENGINE_REPLAY",
            "parity": True,
            "symbols": 5,
            "trades": 358,
        },
    ]
    result = aggregate_engine_status(
        rows,
        required_engines=("native",),
        minimum_symbols=5,
        minimum_total_trades=100,
    )

    assert result["automatic_live_promotion"] is False
    assert result["broker_calls"] == 0
    assert result["order_calls"] == 0
    assert result["execution_authority"] == "NONE"
