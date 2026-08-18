from __future__ import annotations

import json
import os
import runpy
import time
from pathlib import Path

import pandas as pd
import pytest
import yaml

from stocks.orchestration.forward_signal_engine_v2_19 import (
    build_validated_forward_signal_state,
)
from stocks.orchestration.strategy_forward_signals import (
    build_forward_trigger_map,
)
from stocks.orchestration.validated_strategy_deployment_v2_19 import (
    AUDIT_SCHEMA,
    MANIFEST_SCHEMA,
    REGISTRY_SCHEMA,
    build_validated_strategy_deployment,
    exclusive_run_lock,
    verify_validated_strategy_deployment,
    write_validated_strategy_deployment,
)
from stocks.research.cross_engine_handoff_v2_18 import (
    write_cross_engine_handoff,
)

HYPOTHESES = (
    (
        "rsi-id",
        "rsi_threshold_exit",
        {"rsi_period": 2, "entry_threshold": 10, "exit_threshold": 70},
        "a",
        "b",
        358,
    ),
    (
        "obv-id",
        "obv_breakout",
        {"lookback": 20, "obv_ema": 12, "rvol_period": 20, "rvol_min": 1.5},
        "c",
        "d",
        685,
    ),
)
ENGINES = ("native", "pybroker", "nautilus", "lean")


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _fixture(root: Path) -> None:
    validation_root = (
        root / "artifacts/research_runtime/cross_engine_strategy_validation_v2_17"
    )
    validation_root.mkdir(parents=True)
    strategies = [
        {"hypothesis_id": item[0], "strategy": item[1]} for item in HYPOTHESES
    ]
    _write_yaml(
        root / "config/cross_engine_strategy_validation_v2_17.yaml",
        {
            "schema": "cross_engine_strategy_validation_v2_17",
            "scope": {
                "strategies": strategies,
                "primary_timeframe": "1h",
                "supported_execution_contracts": ["NEXT_OPEN_REPLAY"],
            },
            "canonical_contract": {
                "entry_fill": "NEXT_1H_OPEN",
                "whole_shares_only": True,
                "fractional_shares_allowed": False,
                "cross_engine_reselection": False,
                "parameters_frozen": True,
            },
            "engines": {"required": list(ENGINES)},
            "promotion": {
                "minimum_symbols": 5,
                "minimum_total_trades": 100,
                "automatic_live_promotion": False,
                "execution_authority": "NONE",
            },
            "authority": {
                "broker_order_submission": False,
                "external_engine_order_submission": False,
                "execution_authority": "NONE",
            },
        },
    )
    _write_yaml(
        root / "config/cross_engine_handoff_v2_18.yaml",
        {
            "schema": "cross_engine_validated_handoff_v2_18",
            "source": {
                "validation_config": (
                    "config/cross_engine_strategy_validation_v2_17.yaml"
                ),
                "validation_config_schema": ("cross_engine_strategy_validation_v2_17"),
                "validation_root": (
                    "artifacts/research_runtime/cross_engine_strategy_validation_v2_17"
                ),
                "validation_audit_schema": (
                    "cross_engine_strategy_validation_audit_v2_17"
                ),
                "packet_audit_schema": ("canonical_cross_engine_replay_packet_v2_17"),
            },
            "handoff": {
                "required_validation_status": "CROSS_ENGINE_VALIDATED",
                "required_engine_mode": "FULL_ENGINE_REPLAY",
                "required_engine_parity": True,
                "require_exact_configured_scope": True,
                "require_immutable_evidence": True,
                "require_parameters_frozen": True,
                "require_whole_shares_only": True,
                "fractional_shares_allowed": False,
                "automatic_live_promotion": False,
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": "NONE",
            },
        },
    )

    summary_rows = []
    engine_rows = []
    for hypothesis_id, strategy, _, packet_char, bar_char, trades in HYPOTHESES:
        packet_hash = packet_char * 64
        bar_hash = bar_char * 64
        summary_rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "strategy": strategy,
                "symbols": 5,
                "trades": trades,
                "packet_hash": packet_hash,
                "bar_hash": bar_hash,
                "status": "CROSS_ENGINE_VALIDATED",
                "blockers": "[]",
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": "NONE",
            }
        )
        for engine in ENGINES:
            engine_rows.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "strategy": strategy,
                    "engine": engine,
                    "mode": "FULL_ENGINE_REPLAY",
                    "parity": True,
                    "packet_hash": packet_hash,
                    "bar_hash": bar_hash,
                    "broker_calls": 0,
                    "order_calls": 0,
                    "execution_authority": "NONE",
                }
            )

        strategy_root = validation_root / hypothesis_id
        strategy_root.mkdir()
        (strategy_root / "packet_audit.json").write_text(
            json.dumps(
                {
                    "schema": "canonical_cross_engine_replay_packet_v2_17",
                    "hypothesis_id": hypothesis_id,
                    "strategy": strategy,
                    "packet_hash": packet_hash,
                    "bar_hash": bar_hash,
                    "trades": trades,
                    "symbols": 5,
                    "parameters_frozen": True,
                    "whole_shares_only": True,
                    "execution_authority": "NONE",
                }
            ),
            encoding="utf-8",
        )
        (strategy_root / "canonical_schedule.parquet").write_bytes(b"schedule")
        (strategy_root / "native_ledger.parquet").write_bytes(b"native")
        for engine in ENGINES[1:]:
            (strategy_root / f"{engine}_ledger.parquet").write_bytes(engine.encode())
            (strategy_root / f"{engine}_parity_rows.csv").write_text(
                "row_match\nTrue\n",
                encoding="utf-8",
            )

    pd.DataFrame(summary_rows).to_csv(
        validation_root / "strategy_summary.csv", index=False
    )
    pd.DataFrame(engine_rows).to_csv(
        validation_root / "engine_results.csv", index=False
    )
    (validation_root / "audit.json").write_text(
        json.dumps(
            {
                "schema": "cross_engine_strategy_validation_audit_v2_17",
                "strategies": 2,
                "validated": 2,
                "required_engines": list(ENGINES),
                "parameters_frozen": True,
                "whole_shares_only": True,
                "fractional_shares_allowed": False,
                "automatic_live_promotion": False,
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": "NONE",
            }
        ),
        encoding="utf-8",
    )
    write_cross_engine_handoff(root)

    roster_path = root / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    roster_path.parent.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "hypothesis_id": hypothesis_id,
                "strategy": strategy,
                "roster_status": "BROADLY_VALIDATED_FINALIST",
                "params_json": json.dumps(params),
            }
            for hypothesis_id, strategy, params, *_ in HYPOTHESES
        ]
    ).to_csv(roster_path, index=False)

    _write_yaml(
        root / "config/validated_strategy_deployment_v2_19.yaml",
        {
            "schema": "validated_strategy_research_deployment_v2_19",
            "source": {
                "handoff_root": (
                    "artifacts/research_runtime/cross_engine_handoff_v2_18"
                ),
                "handoff_audit_schema": "cross_engine_handoff_audit_v2_18",
                "handoff_registry_schema": ("cross_engine_strategy_registry_v2_18"),
                "final_roster": (
                    "artifacts/research_runtime/final_strategy_roster/roster.csv"
                ),
            },
            "deployment": {
                "required_handoff_status": "RESEARCH_HANDOFF_READY",
                "required_roster_status": "BROADLY_VALIDATED_FINALIST",
                "required_signal_adapters": [
                    "rsi_threshold_exit",
                    "obv_breakout",
                ],
                "require_exact_handoff_scope": True,
                "require_frozen_parameter_payload": True,
                "primary_timeframe": "1h",
                "execution_contract": "NEXT_OPEN_REPLAY",
                "overlap_policy": "REJECT",
                "automatic_live_promotion": False,
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": "NONE",
            },
            "automation": {
                "mode": "EXTERNAL_TRIGGER",
                "timezone": "UTC",
                "lock_timeout_seconds": 3600,
                "write_only_when_changed": True,
            },
        },
    )


def test_builds_parameter_frozen_research_deployment(tmp_path: Path):
    _fixture(tmp_path)

    registry, manifest, audit = build_validated_strategy_deployment(tmp_path)

    assert len(registry) == 2
    assert set(registry["registry_schema"]) == {REGISTRY_SCHEMA}
    assert set(registry["deployment_status"]) == {"RESEARCH_SIGNAL_ELIGIBLE"}
    assert registry["parameters_sha256"].str.len().eq(64).all()
    assert manifest["schema"] == MANIFEST_SCHEMA
    assert manifest["file_count"] == 5
    assert audit["schema"] == AUDIT_SCHEMA
    assert audit["deployment_ready"] is True
    assert audit["eligible_strategies"] == 2
    assert audit["execution_authority"] == "NONE"


def test_writes_idempotently_and_verifies(tmp_path: Path):
    _fixture(tmp_path)

    *_, output_root, first_changed = write_validated_strategy_deployment(tmp_path)
    *_, second_output, second_changed = write_validated_strategy_deployment(tmp_path)

    assert output_root == second_output
    assert first_changed is True
    assert second_changed is False
    assert verify_validated_strategy_deployment(tmp_path)["valid"] is True


def test_roster_tampering_invalidates_written_deployment(tmp_path: Path):
    _fixture(tmp_path)
    write_validated_strategy_deployment(tmp_path)
    roster_path = (
        tmp_path / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    )
    roster = pd.read_csv(roster_path)
    roster.loc[0, "params_json"] = '{"rsi_period":99}'
    roster.to_csv(roster_path, index=False)

    result = verify_validated_strategy_deployment(tmp_path)

    assert result["valid"] is False
    assert any("source hash mismatch" in error for error in result["errors"])


def test_output_audit_tampering_is_rejected_by_source_rebuild(tmp_path: Path):
    _fixture(tmp_path)
    *_, output_root, _ = write_validated_strategy_deployment(tmp_path)
    audit_path = output_root / "audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["registry_sha256"] = "f" * 64
    audit_path.write_text(json.dumps(audit), encoding="utf-8")

    result = verify_validated_strategy_deployment(tmp_path)

    assert result["valid"] is False
    assert "registry hash mismatch" in result["errors"]


def test_missing_handoff_strategy_in_roster_fails_closed(tmp_path: Path):
    _fixture(tmp_path)
    roster_path = (
        tmp_path / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    )
    roster = pd.read_csv(roster_path).iloc[:1]
    roster.to_csv(roster_path, index=False)

    with pytest.raises(ValueError, match="final roster row missing"):
        build_validated_strategy_deployment(tmp_path)


def test_non_finalist_roster_status_fails_closed(tmp_path: Path):
    _fixture(tmp_path)
    roster_path = (
        tmp_path / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    )
    roster = pd.read_csv(roster_path)
    roster.loc[0, "roster_status"] = "CHALLENGER"
    roster.to_csv(roster_path, index=False)

    with pytest.raises(ValueError, match="roster status is not eligible"):
        build_validated_strategy_deployment(tmp_path)


def test_empty_parameter_payload_fails_closed(tmp_path: Path):
    _fixture(tmp_path)
    roster_path = (
        tmp_path / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    )
    roster = pd.read_csv(roster_path)
    roster.loc[0, "params_json"] = "{}"
    roster.to_csv(roster_path, index=False)

    with pytest.raises(ValueError, match="non-empty object"):
        build_validated_strategy_deployment(tmp_path)


def test_signal_trigger_map_rejects_non_deployed_strategy(tmp_path: Path):
    matrix = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "hypothesis_id": "not-deployed",
                "strategy": "rsi_threshold_exit",
            }
        ]
    )
    deployment = pd.DataFrame(
        [
            {
                "hypothesis_id": "rsi-id",
                "strategy": "rsi_threshold_exit",
                "params_json": '{"rsi_period":2,"entry_threshold":10}',
                "deployment_status": "RESEARCH_SIGNAL_ELIGIBLE",
            }
        ]
    )

    triggers = build_forward_trigger_map(
        tmp_path,
        matrix,
        strategy_registry=deployment,
        required_status_column="deployment_status",
        required_status="RESEARCH_SIGNAL_ELIGIBLE",
    )

    assert triggers[("AAPL", "not-deployed")]["ready"] is False
    assert triggers[("AAPL", "not-deployed")]["reason"] == (
        "STRATEGY_NOT_DEPLOYED_FOR_RESEARCH_SIGNALS"
    )


def test_forward_signal_gate_blocks_missing_candidate_matrix(tmp_path: Path):
    _fixture(tmp_path)
    write_validated_strategy_deployment(tmp_path)

    frame, audit = build_validated_forward_signal_state(tmp_path)

    assert frame.empty
    assert audit["ready"] is False
    assert audit["reason"] == "CANDIDATE_STRATEGY_MATRIX_MISSING"
    assert audit["execution_authority"] == "NONE"


def test_exclusive_lock_rejects_overlap_and_recovers_stale_lock(
    tmp_path: Path,
):
    lock_path = tmp_path / "automation.lock"
    with (
        exclusive_run_lock(lock_path, timeout_seconds=3600),
        pytest.raises(RuntimeError, match="AUTOMATION_RUN_ALREADY_ACTIVE"),
        exclusive_run_lock(lock_path, timeout_seconds=3600),
    ):
        pass
    assert not lock_path.exists()

    lock_path.write_text("stale", encoding="utf-8")
    old = time.time() - 7200
    os.utime(lock_path, (old, old))
    with exclusive_run_lock(lock_path, timeout_seconds=3600):
        assert lock_path.is_file()
    assert not lock_path.exists()


def test_v219_finalizer_discovers_all_v219_tests():
    root = Path(__file__).resolve().parents[1]
    expected = {
        str(path.relative_to(root)) for path in (root / "tests").glob("test_*v2_19*.py")
    }
    script = root / "scripts/run_research_automation_finalization_v2_19.py"
    namespace = runpy.run_path(str(script))

    assert set(namespace["focused_tests"]()) == expected
