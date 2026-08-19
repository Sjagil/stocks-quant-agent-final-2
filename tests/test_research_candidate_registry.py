from __future__ import annotations

import pandas as pd

from stocks.research.research_candidate_registry import (
    build_research_candidate_registry,
)


def test_validation_queue_contract_is_non_authoritative() -> None:
    row = {
        "promotion_stage": "VALIDATION_QUEUE",
        "cross_engine_validated": False,
        "dynamic_universe_generalized": False,
        "execution_authority": "NONE",
    }
    assert row["promotion_stage"] != "FINALIST_CANDIDATE"
    assert row["cross_engine_validated"] is False
    assert row["execution_authority"] == "NONE"


def test_candidate_registry_stage_order_is_explicit() -> None:
    stages = pd.Series(["FINALIST_CANDIDATE", "CHALLENGER", "VALIDATION_QUEUE"])
    assert set(stages) == {"FINALIST_CANDIDATE", "CHALLENGER", "VALIDATION_QUEUE"}


def test_generated_cross_engine_failure_is_not_left_in_queue(
    tmp_path,
    monkeypatch,
) -> None:
    queue_root = tmp_path / "artifacts/research_runtime/strategy_generation_v2_22"
    cross_root = queue_root / "cross_engine"
    cross_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "hypothesis_id": "generated-1",
                "strategy": "dual_horizon_momentum",
                "family": "multi_horizon_momentum",
                "params_json": "{}",
                "source_engine": "strategy_generation_v2_22",
                "status": "DIVERSE_SURVIVOR",
                "execution_contract": "NEXT_OPEN_REPLAY",
                "robustness_score": 88.5,
                "median_test_expectancy_bps": 32.0,
                "median_stress_test_expectancy_bps": 18.0,
                "median_test_profit_factor": 1.4,
                "queue_rank": 2,
            }
        ]
    ).to_csv(queue_root / "validation_queue.csv", index=False)
    pd.DataFrame(
        [
            {
                "hypothesis_id": "generated-1",
                "status": "CROSS_ENGINE_NOT_VALIDATED",
            }
        ]
    ).to_csv(cross_root / "strategy_summary.csv", index=False)

    def empty_validated_registry(project_root):
        return (
            pd.DataFrame(),
            {"live_ready": False},
            project_root / "validated.csv",
        )

    monkeypatch.setattr(
        "stocks.research.validated_strategy_registry.write_validated_strategy_registry",
        empty_validated_registry,
    )
    registry, audit = build_research_candidate_registry(tmp_path)
    row = registry.iloc[0]
    assert row["validation_status"] == "REJECTED"
    assert row["promotion_stage"] == "REJECTED_AFTER_CROSSCHECK"
    assert row["robustness_score"] == 88.5
    assert row["median_stress_test_expectancy_bps"] == 18.0
    assert row["queue_rank"] == 2
    assert audit["rejected_after_crosscheck_count"] == 1
    assert row["execution_authority"] == "NONE"
