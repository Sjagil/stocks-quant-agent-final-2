from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stocks.orchestration.dynamic_validated_strategy_deployment_v2_24 import (
    verify_dynamic_validated_strategy_deployment,
    write_dynamic_validated_strategy_deployment,
)


def _write_fixture(root: Path) -> None:
    (root / "config").mkdir(parents=True)
    (root / "artifacts/research_runtime/final_strategy_roster").mkdir(parents=True)
    (root / "artifacts/research_runtime/research_candidate_registry").mkdir(parents=True)
    (root / "artifacts/research_runtime/generated_forward_adapter_audit_v2_23").mkdir(parents=True)
    (root / "config/dynamic_validated_deployment_v2_24.yaml").write_text(
        """schema: dynamic_validated_strategy_deployment_v2_24
source:
  final_roster: artifacts/research_runtime/final_strategy_roster/roster.csv
  final_roster_audit: artifacts/research_runtime/final_strategy_roster/audit.json
  research_candidate_registry: artifacts/research_runtime/research_candidate_registry/registry.csv
  generated_adapter_audit: artifacts/research_runtime/generated_forward_adapter_audit_v2_23/audit.json
deployment:
  required_roster_status: BROADLY_VALIDATED_FINALIST
  required_execution_contract: NEXT_OPEN_REPLAY
  require_research_deployment_ready: true
  require_supported_forward_adapter: true
  accepted_cross_engine_statuses: [CROSS_ENGINE_VALIDATED, 15M_EXECUTION_VALIDATED]
  accepted_generalization_statuses: [DYNAMIC_UNIVERSE_VALIDATED, 15M_DYNAMIC_UNIVERSE_VALIDATED]
  require_frozen_parameter_payload: true
  automatic_live_promotion: false
  broker_calls: 0
  order_calls: 0
  execution_authority: NONE
""",
        encoding="utf-8",
    )
    rows = [
        {
            "hypothesis_id": "a",
            "strategy": "rsi_threshold_exit",
            "family": "mean_reversion",
            "source_engine": "strategy_factory_1h",
            "params_json": json.dumps({"period": 14, "threshold": 30}),
            "execution_contract": "NEXT_OPEN_REPLAY",
            "roster_status": "BROADLY_VALIDATED_FINALIST",
            "research_deployment_ready": True,
            "cross_engine_status": "CROSS_ENGINE_VALIDATED",
            "broad_generalization_status": "DYNAMIC_UNIVERSE_VALIDATED",
            "execution_authority": "NONE",
        },
        {
            "hypothesis_id": "b",
            "strategy": "keltner_volume_breakout",
            "family": "volatility_breakout",
            "source_engine": "strategy_generation_v2_22",
            "params_json": json.dumps({"ema": 20, "atr": 14, "mult": 1.5}),
            "execution_contract": "NEXT_OPEN_REPLAY",
            "roster_status": "BROADLY_VALIDATED_FINALIST",
            "research_deployment_ready": True,
            "cross_engine_status": "CROSS_ENGINE_VALIDATED",
            "broad_generalization_status": "DYNAMIC_UNIVERSE_VALIDATED",
            "execution_authority": "NONE",
        },
        {
            "hypothesis_id": "c",
            "strategy": "market_structure_atr_pullback",
            "family": "breakout_pullback",
            "source_engine": "strategy_factory_1h",
            "params_json": json.dumps({"atr": 14}),
            "execution_contract": "NEXT_OPEN_REPLAY",
            "roster_status": "BROADLY_VALIDATED_FINALIST",
            "research_deployment_ready": True,
            "cross_engine_status": "15M_EXECUTION_VALIDATED",
            "broad_generalization_status": "15M_DYNAMIC_UNIVERSE_VALIDATED",
            "execution_authority": "NONE",
        },
    ]
    pd.DataFrame(rows).to_csv(
        root / "artifacts/research_runtime/final_strategy_roster/roster.csv", index=False
    )
    (root / "artifacts/research_runtime/final_strategy_roster/audit.json").write_text(
        json.dumps({"schema": "final_strategy_roster_v2_8", "execution_authority": "NONE"}),
        encoding="utf-8",
    )
    pd.DataFrame(rows).to_csv(
        root / "artifacts/research_runtime/research_candidate_registry/registry.csv", index=False
    )
    (root / "artifacts/research_runtime/generated_forward_adapter_audit_v2_23/audit.json").write_text(
        json.dumps({"coverage_complete": True, "execution_authority": "NONE"}),
        encoding="utf-8",
    )


def test_dynamic_deployment_selects_supported_finalists_and_records_rejects(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    registry, rejected, audit, _ = write_dynamic_validated_strategy_deployment(tmp_path)
    assert set(registry["strategy"]) == {"rsi_threshold_exit", "keltner_volume_breakout"}
    assert set(rejected["strategy"]) == {"market_structure_atr_pullback"}
    assert "FORWARD_ADAPTER_NOT_SUPPORTED" in rejected.iloc[0]["blockers"]
    assert audit["eligible_strategies"] == 2
    assert audit["excluded_finalists"] == 1
    assert audit["execution_authority"] == "NONE"


def test_dynamic_deployment_verification_is_hash_bound(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    write_dynamic_validated_strategy_deployment(tmp_path)
    verification = verify_dynamic_validated_strategy_deployment(tmp_path)
    assert verification["valid"] is True
    with (tmp_path / "artifacts/research_runtime/final_strategy_roster/roster.csv").open("a", encoding="utf-8") as handle:
        handle.write("\n")
    verification = verify_dynamic_validated_strategy_deployment(tmp_path)
    assert verification["valid"] is False
    assert "MANIFEST_SOURCE_HASH_MISMATCH" in verification["errors"]
