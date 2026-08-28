from __future__ import annotations

import json

import pandas as pd

from stocks.research.generated_strategy_validation_v2_22 import (
    build_generated_strategy_validation_audit,
    write_generated_strategy_validation_audit,
)


def _write_pipeline_artifacts(root) -> None:
    generated = root / "artifacts/research_runtime/strategy_generation_v2_22"
    cross = generated / "cross_engine"
    generalization = (
        root / "artifacts/research_runtime/dynamic_universe_generalization"
    )
    registry = root / "artifacts/research_runtime/research_candidate_registry"
    roster = root / "artifacts/research_runtime/final_strategy_roster"
    for path in (generated, cross, generalization, registry, roster):
        path.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [
            {
                "hypothesis_id": "generated-valid",
                "strategy": "keltner_volume_breakout",
                "family": "volatility_breakout",
            },
            {
                "hypothesis_id": "generated-reject",
                "strategy": "chaikin_flow_breakout",
                "family": "money_flow_confirmation",
            },
        ]
    ).to_csv(generated / "validation_queue.csv", index=False)
    pd.DataFrame(
        [
            {
                "hypothesis_id": "generated-valid",
                "status": "CROSS_ENGINE_VALIDATED",
            },
            {
                "hypothesis_id": "generated-reject",
                "status": "CROSS_ENGINE_NOT_VALIDATED",
            },
        ]
    ).to_csv(cross / "strategy_summary.csv", index=False)
    pd.DataFrame(
        [
            {
                "hypothesis_id": "generated-valid",
                "generalization_status": "DYNAMIC_UNIVERSE_VALIDATED",
            },
            {
                "hypothesis_id": "generated-reject",
                "generalization_status": "WAITING_CROSS_ENGINE",
            },
        ]
    ).to_csv(generalization / "summary.csv", index=False)
    pd.DataFrame(
        [
            {
                "hypothesis_id": "generated-valid",
                "promotion_stage": "FINALIST_CANDIDATE",
            },
            {
                "hypothesis_id": "generated-reject",
                "promotion_stage": "REJECTED_AFTER_CROSSCHECK",
            },
        ]
    ).to_csv(registry / "registry.csv", index=False)
    pd.DataFrame(
        [
            {
                "hypothesis_id": "generated-valid",
                "roster_status": "BROADLY_VALIDATED_FINALIST",
            },
            {
                "hypothesis_id": "generated-reject",
                "roster_status": "RESEARCH_PENDING",
            },
        ]
    ).to_csv(roster / "roster.csv", index=False)


def test_generated_pipeline_audit_requires_complete_evidence(tmp_path) -> None:
    _write_pipeline_artifacts(tmp_path)
    frame, audit = build_generated_strategy_validation_audit(tmp_path)
    assert audit["pipeline_complete"] is True
    assert audit["queued_strategies"] == 2
    assert audit["broadly_validated_finalists"] == 1
    assert audit["cross_engine_rejects"] == 1
    assert frame["evidence_complete"].all()
    assert set(frame["execution_authority"]) == {"NONE"}


def test_generated_pipeline_audit_fails_closed_on_missing_roster(tmp_path) -> None:
    _write_pipeline_artifacts(tmp_path)
    roster = (
        tmp_path
        / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    )
    frame = pd.read_csv(roster)
    frame.loc[frame["hypothesis_id"] == "generated-reject"].to_csv(
        roster,
        index=False,
    )
    status, audit = build_generated_strategy_validation_audit(tmp_path)
    assert audit["pipeline_complete"] is False
    assert audit["incomplete_strategies"] == 1
    missing = status.loc[
        status["hypothesis_id"] == "generated-valid"
    ].iloc[0]
    assert "ROSTER_ROW_MISSING" in missing["errors"]


def test_generated_pipeline_audit_writes_non_authoritative_artifacts(
    tmp_path,
) -> None:
    _write_pipeline_artifacts(tmp_path)
    frame, audit, output = write_generated_strategy_validation_audit(tmp_path)
    assert len(frame) == 2
    assert (output / "strategy_status.csv").is_file()
    payload = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert payload == audit
    assert payload["automatic_live_promotion"] is False
    assert payload["broker_calls"] == 0
    assert payload["order_calls"] == 0
    assert payload["execution_authority"] == "NONE"
