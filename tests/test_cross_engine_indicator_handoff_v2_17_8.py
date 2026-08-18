from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from stocks.research.canonical_trade_handoff_v2_17_8 import (
    configured_validation_coverage,
    load_canonical_trade_artifacts,
    materialize_survivor_trades,
)


ROOT = Path(__file__).resolve().parents[1]


def _trades(hypothesis_id: str, strategy: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "hypothesis_id": hypothesis_id,
                "strategy": strategy,
                "family": "volume_breakout",
                "symbol": "SPY",
                "entry_time": pd.Timestamp("2026-01-02 15:30", tz="UTC"),
                "exit_time": pd.Timestamp("2026-01-05 15:30", tz="UTC"),
                "gross_return": 0.05,
                "score": 1.0,
                "duration_bars": 10,
                "forced": False,
            }
        ]
    )


def test_indicator_survivors_materialize_canonical_trades():
    survivors = pd.DataFrame([{"hypothesis_id": "obv"}])
    result = materialize_survivor_trades(
        {"obv": _trades("obv", "obv_breakout")},
        survivors,
    )

    assert result["hypothesis_id"].tolist() == ["obv"]
    assert result["strategy"].tolist() == ["obv_breakout"]
    assert str(result["entry_time"].dt.tz) == "UTC"


def test_indicator_survivor_without_trades_fails_closed():
    survivors = pd.DataFrame([{"hypothesis_id": "obv"}])
    with pytest.raises(ValueError, match="without canonical trades"):
        materialize_survivor_trades({}, survivors)


def test_factory_and_indicator_trade_artifacts_are_combined(tmp_path):
    factory = tmp_path / "factory.parquet"
    indicator = tmp_path / "indicator.parquet"
    _trades("rsi", "rsi_threshold_exit").to_parquet(factory, index=False)
    _trades("obv", "obv_breakout").to_parquet(indicator, index=False)

    result = load_canonical_trade_artifacts(
        primary_candidates=(tmp_path / "missing.parquet", factory),
        supplemental=(indicator,),
    )

    assert set(result["hypothesis_id"]) == {"rsi", "obv"}
    assert result["canonical_trade_source"].nunique() == 2


def test_duplicate_hypothesis_sources_fail_closed(tmp_path):
    factory = tmp_path / "factory.parquet"
    indicator = tmp_path / "indicator.parquet"
    _trades("same", "obv_breakout").to_parquet(factory, index=False)
    _trades("same", "obv_breakout").to_parquet(indicator, index=False)

    with pytest.raises(ValueError, match="multiple artifacts"):
        load_canonical_trade_artifacts(
            primary_candidates=(factory,),
            supplemental=(indicator,),
        )


def test_finalization_requires_every_configured_strategy():
    strategies = [
        {"hypothesis_id": "rsi"},
        {"hypothesis_id": "obv"},
    ]
    summary = pd.DataFrame(
        [
            {
                "hypothesis_id": "rsi",
                "status": "CROSS_ENGINE_VALIDATED",
            }
        ]
    )

    coverage = configured_validation_coverage(summary, strategies)

    assert coverage["validated"] is False
    assert coverage["validated_count"] == 1
    assert coverage["missing_hypothesis_ids"] == ["obv"]


def test_finalization_passes_only_with_complete_coverage():
    strategies = [
        {"hypothesis_id": "rsi"},
        {"hypothesis_id": "obv"},
    ]
    summary = pd.DataFrame(
        [
            {
                "hypothesis_id": hypothesis_id,
                "status": "CROSS_ENGINE_VALIDATED",
            }
            for hypothesis_id in ("rsi", "obv")
        ]
    )

    coverage = configured_validation_coverage(summary, strategies)

    assert coverage["validated"] is True
    assert coverage["validated_count"] == 2
    assert coverage["missing_hypothesis_ids"] == []


def test_scripts_wire_indicator_trade_handoff_and_strict_coverage():
    indicator = (
        ROOT / "scripts/run_indicator_strategy_discovery.py"
    ).read_text(encoding="utf-8")
    replay = (
        ROOT / "scripts/run_cross_engine_strategy_validation_v2_17.py"
    ).read_text(encoding="utf-8")
    finalizer = (
        ROOT / "scripts/run_cross_engine_finalization_v2_17_7.py"
    ).read_text(encoding="utf-8")

    assert 'output / "survivor_trades.parquet"' in indicator
    assert "materialize_survivor_trades(" in indicator
    assert "indicator_discovery_1h/" in replay
    assert "load_canonical_trade_artifacts(" in replay
    assert "configured_validation_coverage(" in finalizer
    assert ').any()' not in finalizer
