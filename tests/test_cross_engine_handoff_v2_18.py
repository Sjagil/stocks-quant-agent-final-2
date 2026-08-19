from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from stocks.research.cross_engine_handoff_v2_18 import (
    AUDIT_SCHEMA,
    MANIFEST_SCHEMA,
    REGISTRY_SCHEMA,
    build_cross_engine_handoff,
    verify_cross_engine_handoff,
    write_cross_engine_handoff,
)

HYPOTHESES = (
    ("rsi-id", "rsi_threshold_exit", "a", "b", 358),
    ("obv-id", "obv_breakout", "c", "d", 685),
)
ENGINES = ("native", "pybroker", "nautilus", "lean")


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _fixture(root: Path) -> Path:
    validation_root = (
        root / "artifacts/research_runtime/cross_engine_strategy_validation_v2_17"
    )
    validation_root.mkdir(parents=True)

    validation_config = {
        "schema": "cross_engine_strategy_validation_v2_17",
        "scope": {
            "strategies": [
                {"hypothesis_id": item[0], "strategy": item[1]} for item in HYPOTHESES
            ],
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
    }
    validation_config_path = root / "config/cross_engine_strategy_validation_v2_17.yaml"
    _write_yaml(validation_config_path, validation_config)

    handoff_config_path = root / "config/cross_engine_handoff_v2_18.yaml"
    _write_yaml(
        handoff_config_path,
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
    for hypothesis_id, strategy, packet_char, bar_char, trades in HYPOTHESES:
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
        (strategy_root / "canonical_schedule.parquet").write_bytes(
            b"canonical-schedule"
        )
        (strategy_root / "native_ledger.parquet").write_bytes(b"native-ledger")
        for engine in ENGINES[1:]:
            (strategy_root / f"{engine}_ledger.parquet").write_bytes(
                f"{engine}-ledger".encode()
            )
            (strategy_root / f"{engine}_parity_rows.csv").write_text(
                "row_match\nTrue\n",
                encoding="utf-8",
            )

    pd.DataFrame(summary_rows).to_csv(
        validation_root / "strategy_summary.csv",
        index=False,
    )
    pd.DataFrame(engine_rows).to_csv(
        validation_root / "engine_results.csv",
        index=False,
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
    return handoff_config_path


def test_builds_complete_immutable_two_strategy_handoff(tmp_path: Path):
    _fixture(tmp_path)

    registry, manifest, audit = build_cross_engine_handoff(tmp_path)

    assert list(registry["hypothesis_id"]) == ["obv-id", "rsi-id"]
    assert set(registry["registry_schema"]) == {REGISTRY_SCHEMA}
    assert set(registry["handoff_status"]) == {"RESEARCH_HANDOFF_READY"}
    assert set(registry["required_engines"]) == {"native|pybroker|nautilus|lean"}
    assert manifest["schema"] == MANIFEST_SCHEMA
    assert manifest["file_count"] == 23
    assert len(manifest["manifest_sha256"]) == 64
    assert audit["schema"] == AUDIT_SCHEMA
    assert audit["handoff_ready"] is True
    assert audit["registered_strategies"] == 2
    assert audit["automatic_live_promotion"] is False
    assert audit["execution_authority"] == "NONE"


def test_written_handoff_verifies_and_detects_artifact_tampering(
    tmp_path: Path,
):
    _fixture(tmp_path)
    _, _, _, output_root = write_cross_engine_handoff(tmp_path)

    assert verify_cross_engine_handoff(tmp_path)["valid"] is True

    evidence = (
        tmp_path / "artifacts/research_runtime/"
        "cross_engine_strategy_validation_v2_17/"
        "obv-id/lean_ledger.parquet"
    )
    evidence.write_bytes(b"tampered")
    result = verify_cross_engine_handoff(
        tmp_path,
        output_root=output_root,
    )

    assert result["valid"] is False
    assert any("evidence" in error for error in result["errors"])


def test_missing_required_engine_fails_closed(tmp_path: Path):
    _fixture(tmp_path)
    path = (
        tmp_path / "artifacts/research_runtime/"
        "cross_engine_strategy_validation_v2_17/engine_results.csv"
    )
    frame = pd.read_csv(path)
    frame = frame.loc[
        ~((frame["hypothesis_id"] == "obv-id") & (frame["engine"] == "lean"))
    ]
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="engine coverage mismatch"):
        build_cross_engine_handoff(tmp_path)


def test_mixed_packet_hash_fails_closed(tmp_path: Path):
    _fixture(tmp_path)
    path = (
        tmp_path / "artifacts/research_runtime/"
        "cross_engine_strategy_validation_v2_17/engine_results.csv"
    )
    frame = pd.read_csv(path)
    frame.loc[
        (frame["hypothesis_id"] == "rsi-id") & (frame["engine"] == "nautilus"),
        "packet_hash",
    ] = "f" * 64
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="packet hash mismatch"):
        build_cross_engine_handoff(tmp_path)


def test_summary_blocker_fails_closed(tmp_path: Path):
    _fixture(tmp_path)
    path = (
        tmp_path / "artifacts/research_runtime/"
        "cross_engine_strategy_validation_v2_17/strategy_summary.csv"
    )
    frame = pd.read_csv(path)
    frame.loc[frame["hypothesis_id"] == "rsi-id", "blockers"] = "['LEAN_PARITY_FAILED']"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="validation blockers present"):
        build_cross_engine_handoff(tmp_path)


def test_any_execution_authority_fails_closed(tmp_path: Path):
    _fixture(tmp_path)
    path = (
        tmp_path / "artifacts/research_runtime/"
        "cross_engine_strategy_validation_v2_17/engine_results.csv"
    )
    frame = pd.read_csv(path)
    frame.loc[
        (frame["hypothesis_id"] == "obv-id") & (frame["engine"] == "pybroker"),
        "execution_authority",
    ] = "CANARY"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="execution authority granted"):
        build_cross_engine_handoff(tmp_path)


def test_scope_must_exactly_match_validation_config(tmp_path: Path):
    _fixture(tmp_path)
    path = (
        tmp_path / "artifacts/research_runtime/"
        "cross_engine_strategy_validation_v2_17/strategy_summary.csv"
    )
    frame = pd.read_csv(path)
    frame = pd.concat(
        [frame, frame.iloc[[0]].assign(hypothesis_id="unexpected-id")],
        ignore_index=True,
    )
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="scope mismatch"):
        build_cross_engine_handoff(tmp_path)


def test_unsafe_handoff_policy_is_rejected(tmp_path: Path):
    config_path = _fixture(tmp_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["handoff"]["automatic_live_promotion"] = True
    _write_yaml(config_path, config)

    with pytest.raises(ValueError, match="unsafe handoff"):
        build_cross_engine_handoff(tmp_path)


def test_verifier_reports_malformed_counts_without_traceback(tmp_path: Path):
    _fixture(tmp_path)
    _, _, _, output_root = write_cross_engine_handoff(tmp_path)
    registry_path = output_root / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry[0]["broker_calls"] = "not-an-integer"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    result = verify_cross_engine_handoff(tmp_path)

    assert result["valid"] is False
    assert any("expected integer" in error for error in result["errors"])


def test_verifier_detects_registry_csv_tampering(tmp_path: Path):
    _fixture(tmp_path)
    _, _, _, output_root = write_cross_engine_handoff(tmp_path)
    registry_path = output_root / "registry.csv"
    registry = pd.read_csv(registry_path)
    registry.loc[0, "strategy"] = "tampered_strategy"
    registry.to_csv(registry_path, index=False)

    result = verify_cross_engine_handoff(tmp_path)

    assert result["valid"] is False
    assert "registry CSV hash mismatch" in result["errors"]


def test_v218_finalizer_discovers_tests_and_keeps_no_authority():
    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts/run_cross_engine_finalization_v2_18.py").read_text(
        encoding="utf-8"
    )

    assert 'glob("test_*v2_18*.py")' in text
    assert '"BUILD_V2_18_HANDOFF"' in text
    assert '"AUDIT_V2_18_HANDOFF"' in text
    assert 'print("BROKER_CALLS 0")' in text
    assert 'print("ORDER_CALLS 0")' in text
    assert 'print("EXECUTION_AUTHORITY NONE")' in text
