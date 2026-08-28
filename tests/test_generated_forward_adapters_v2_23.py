from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from stocks.orchestration.generated_forward_adapter_audit_v2_23 import (
    build_generated_forward_adapter_audit,
)
from stocks.orchestration.generated_strategy_forward_signals_v2_23 import (
    GENERATED_NEXT_OPEN_STRATEGIES,
)
from stocks.orchestration.strategy_forward_signals import (
    SUPPORTED_NEXT_OPEN_STRATEGIES,
    evaluate_latest_entry_condition,
)
from stocks.research.strategy_generation_v2_22 import blueprint_registry


def _frame(rows: int = 320) -> pd.DataFrame:
    index = np.arange(rows, dtype=float)
    close = 100.0 + 0.12 * index + 1.8 * np.sin(index / 6.0)
    open_ = close - 0.15 * np.cos(index / 4.0)
    high = np.maximum(open_, close) + 0.75
    low = np.minimum(open_, close) - 0.75
    volume = 1_000_000.0 + 120_000.0 * (1.0 + np.sin(index / 9.0))
    return pd.DataFrame(
        {
            "date": pd.date_range(
                "2024-01-02 14:30:00",
                periods=rows,
                freq="h",
                tz="UTC",
            ),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def test_all_v222_blueprints_have_generated_forward_adapters() -> None:
    catalog = {blueprint.name for blueprint in blueprint_registry()}
    assert len(catalog) == 9
    assert catalog == set(GENERATED_NEXT_OPEN_STRATEGIES)
    assert catalog.issubset(SUPPORTED_NEXT_OPEN_STRATEGIES)


def test_every_generated_adapter_executes_without_missing_adapter() -> None:
    frame = _frame()
    for blueprint in blueprint_registry():
        result = evaluate_latest_entry_condition(
            strategy=blueprint.name,
            frame=frame,
            params=dict(blueprint.default_params),
        )
        assert isinstance(result["ready"], bool)
        assert "ADAPTER_NOT_IMPLEMENTED" not in str(result["reason"])
        assert result["adapter_version"] == "v2.23"


def test_current_generated_finalist_strategies_are_supported() -> None:
    expected = {
        "keltner_volume_breakout",
        "chaikin_flow_breakout",
        "range_contraction_expansion",
    }
    assert expected.issubset(GENERATED_NEXT_OPEN_STRATEGIES)


def test_unknown_strategy_stays_fail_closed() -> None:
    result = evaluate_latest_entry_condition(
        strategy="future_unknown_strategy",
        frame=_frame(),
        params={},
    )
    assert result["ready"] is False
    assert result["reason"] == "STRATEGY_FORWARD_ADAPTER_NOT_IMPLEMENTED"


def _write_roster(root: Path, strategy: str, hypothesis_id: str) -> None:
    path = root / "artifacts/research_runtime/final_strategy_roster"
    path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "hypothesis_id": hypothesis_id,
                "strategy": strategy,
                "source_engine": "strategy_generation_v2_22",
                "roster_status": "BROADLY_VALIDATED_FINALIST",
            }
        ]
    ).to_csv(path / "roster.csv", index=False)


def test_static_audit_accepts_supported_generated_finalist(tmp_path: Path) -> None:
    _write_roster(tmp_path, "keltner_volume_breakout", "generated-1")
    audit = build_generated_forward_adapter_audit(tmp_path)
    assert audit["coverage_complete"] is True
    assert audit["broad_generated_finalists"] == 1
    assert audit["missing_finalist_adapters"] == []
    assert audit["execution_authority"] == "NONE"


def test_static_audit_rejects_future_unadapted_generated_finalist(
    tmp_path: Path,
) -> None:
    _write_roster(tmp_path, "future_generated_strategy", "generated-2")
    audit = build_generated_forward_adapter_audit(tmp_path)
    assert audit["coverage_complete"] is False
    assert audit["missing_finalist_adapters"] == ["future_generated_strategy"]
