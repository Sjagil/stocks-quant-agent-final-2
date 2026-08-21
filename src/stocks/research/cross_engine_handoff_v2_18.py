from __future__ import annotations

import ast
import hashlib
import json
import math
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

SCHEMA = "cross_engine_validated_handoff_v2_18"
REGISTRY_SCHEMA = "cross_engine_strategy_registry_v2_18"
MANIFEST_SCHEMA = "cross_engine_evidence_manifest_v2_18"
AUDIT_SCHEMA = "cross_engine_handoff_audit_v2_18"

DEFAULT_CONFIG = Path("config/cross_engine_handoff_v2_18.yaml")
DEFAULT_OUTPUT_ROOT = Path("artifacts/research_runtime/cross_engine_handoff_v2_18")

SHA256_LENGTH = 64
AUTHORITY_NONE = "NONE"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path}: expected a YAML object")
    return payload


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path}: expected a JSON object")
    return payload


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(path)
    try:
        return pd.read_csv(path, dtype={"hypothesis_id": str})
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"{path}: empty CSV") from exc


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes"}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, float) and math.isnan(value):
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return [item for item in text.split("|") if item]
    if isinstance(parsed, (list, tuple, set)):
        return list(parsed)
    return [parsed]


def _as_int(value: Any, *, label: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: expected integer, got {value!r}") from exc
    return number


def _valid_sha256(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return len(text) == SHA256_LENGTH and all(
        char in "0123456789abcdef" for char in text
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _relative_to_root(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"artifact escapes project root: {path}") from exc


def _resolve_evidence_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"manifest path escapes project root: {relative}") from exc
    return candidate


def _require_columns(
    frame: pd.DataFrame,
    columns: set[str],
    *,
    source: str,
) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{source}: missing columns {missing}")


def _require_unique(
    frame: pd.DataFrame,
    columns: list[str],
    *,
    source: str,
) -> None:
    if frame.duplicated(columns).any():
        raise ValueError(f"{source}: duplicate keys {columns}")


def _authority_is_none(value: Any) -> bool:
    return str(value or "").strip().upper() == AUTHORITY_NONE


def _required_evidence_files(
    validation_root: Path,
    hypothesis_id: str,
    external_engines: list[str],
) -> list[Path]:
    strategy_root = validation_root / hypothesis_id
    files = [
        strategy_root / "packet_audit.json",
        strategy_root / "canonical_schedule.parquet",
        strategy_root / "native_ledger.parquet",
    ]
    for engine in external_engines:
        files.extend(
            [
                strategy_root / f"{engine}_ledger.parquet",
                strategy_root / f"{engine}_parity_rows.csv",
            ]
        )
    return files


def _evidence_entry(path: Path, root: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(path)
    return {
        "path": _relative_to_root(path, root),
        "sha256": sha256_file(path),
        "size_bytes": int(path.stat().st_size),
    }


def _strategy_config_map(
    validation_config: Mapping[str, Any],
) -> dict[str, str]:
    scope = validation_config.get("scope")
    if not isinstance(scope, Mapping):
        raise TypeError("v2.17 config: scope missing")
    strategies = scope.get("strategies")
    if not isinstance(strategies, list) or not strategies:
        raise ValueError("v2.17 config: scope.strategies missing")

    result: dict[str, str] = {}
    for item in strategies:
        if not isinstance(item, Mapping):
            raise TypeError("v2.17 config: invalid strategy entry")
        hypothesis_id = str(item.get("hypothesis_id") or "").strip()
        strategy = str(item.get("strategy") or "").strip()
        if not hypothesis_id or not strategy:
            raise ValueError("v2.17 config: incomplete strategy entry")
        if hypothesis_id in result:
            raise ValueError(f"v2.17 config: duplicate hypothesis {hypothesis_id}")
        result[hypothesis_id] = strategy
    return result


def _required_engines(
    validation_config: Mapping[str, Any],
) -> list[str]:
    engines = validation_config.get("engines")
    if not isinstance(engines, Mapping):
        raise TypeError("v2.17 config: engines missing")
    required = engines.get("required")
    if not isinstance(required, list) or not required:
        raise ValueError("v2.17 config: engines.required missing")
    normalized = [str(value).strip().lower() for value in required]
    if len(normalized) != len(set(normalized)):
        raise ValueError("v2.17 config: duplicate required engine")
    return normalized


def _validate_handoff_policy(config: Mapping[str, Any]) -> None:
    policy = config.get("handoff")
    if not isinstance(policy, Mapping):
        raise TypeError("v2.18 config: handoff policy missing")
    expected = {
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
        "execution_authority": AUTHORITY_NONE,
    }
    for key, required in expected.items():
        observed = policy.get(key)
        if isinstance(required, bool):
            observed = _as_bool(observed)
        elif isinstance(required, int):
            observed = _as_int(observed, label=f"handoff.{key}")
        else:
            observed = str(observed or "").strip().upper()
            required = str(required).upper()
        if observed != required:
            raise ValueError(f"v2.18 config: unsafe handoff.{key}={observed!r}")


def _validate_source_safety(validation_config: Mapping[str, Any]) -> None:
    canonical = validation_config.get("canonical_contract")
    promotion = validation_config.get("promotion")
    authority = validation_config.get("authority")
    if not all(
        isinstance(value, Mapping) for value in (canonical, promotion, authority)
    ):
        raise ValueError("v2.17 config: safety policy missing")
    if not _as_bool(canonical.get("whole_shares_only")):
        raise ValueError("v2.17 config: whole shares are not required")
    if _as_bool(canonical.get("fractional_shares_allowed")):
        raise ValueError("v2.17 config: fractional shares are allowed")
    if _as_bool(canonical.get("cross_engine_reselection")):
        raise ValueError("v2.17 config: cross-engine reselection is enabled")
    if not _as_bool(canonical.get("parameters_frozen")):
        raise ValueError("v2.17 config: parameters are not frozen")
    if _as_bool(promotion.get("automatic_live_promotion")):
        raise ValueError("v2.17 config: automatic live promotion is enabled")
    if not _authority_is_none(promotion.get("execution_authority")):
        raise ValueError("v2.17 config: promotion grants authority")
    if _as_bool(authority.get("broker_order_submission")):
        raise ValueError("v2.17 config: broker submission is enabled")
    if _as_bool(authority.get("external_engine_order_submission")):
        raise ValueError("v2.17 config: external order submission is enabled")
    if not _authority_is_none(authority.get("execution_authority")):
        raise ValueError("v2.17 config: authority is not NONE")


def build_cross_engine_handoff(
    project_root: str | Path,
    *,
    config_path: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    root = Path(project_root).resolve()
    handoff_config_path = (
        Path(config_path).resolve()
        if config_path is not None
        else root / DEFAULT_CONFIG
    )
    handoff_config = _read_yaml(handoff_config_path)
    if handoff_config.get("schema") != SCHEMA:
        raise ValueError(f"{handoff_config_path}: expected schema {SCHEMA}")
    _validate_handoff_policy(handoff_config)

    source = handoff_config.get("source")
    if not isinstance(source, Mapping):
        raise TypeError("v2.18 config: source missing")

    validation_config_path = _resolve_evidence_path(
        root,
        str(source.get("validation_config") or ""),
    )
    validation_root = _resolve_evidence_path(
        root,
        str(source.get("validation_root") or ""),
    )
    validation_config = _read_yaml(validation_config_path)
    expected_validation_schema = str(source.get("validation_config_schema") or "")
    if validation_config.get("schema") != expected_validation_schema:
        raise ValueError(
            "v2.17 validation config schema mismatch: "
            f"{validation_config.get('schema')!r}"
        )
    _validate_source_safety(validation_config)

    configured = _strategy_config_map(validation_config)
    required_engines = _required_engines(validation_config)
    if "native" not in required_engines:
        raise ValueError("v2.17 config: native engine is required")
    external_engines = [engine for engine in required_engines if engine != "native"]

    summary_path = validation_root / "strategy_summary.csv"
    engine_path = validation_root / "engine_results.csv"
    validation_audit_path = validation_root / "audit.json"
    summary = _read_csv(summary_path)
    engine_results = _read_csv(engine_path)
    validation_audit = _read_json(validation_audit_path)

    _require_columns(
        summary,
        {
            "hypothesis_id",
            "strategy",
            "symbols",
            "trades",
            "packet_hash",
            "bar_hash",
            "status",
            "blockers",
            "broker_calls",
            "order_calls",
            "execution_authority",
        },
        source="strategy_summary.csv",
    )
    _require_columns(
        engine_results,
        {
            "hypothesis_id",
            "strategy",
            "engine",
            "mode",
            "parity",
            "packet_hash",
            "bar_hash",
            "broker_calls",
            "order_calls",
            "execution_authority",
        },
        source="engine_results.csv",
    )
    summary["hypothesis_id"] = summary["hypothesis_id"].astype(str)
    engine_results["hypothesis_id"] = engine_results["hypothesis_id"].astype(str)
    engine_results["engine"] = engine_results["engine"].astype(str).str.lower()
    _require_unique(
        summary,
        ["hypothesis_id"],
        source="strategy_summary.csv",
    )
    _require_unique(
        engine_results,
        ["hypothesis_id", "engine"],
        source="engine_results.csv",
    )

    if set(summary["hypothesis_id"]) != set(configured):
        missing = sorted(set(configured).difference(summary["hypothesis_id"]))
        extra = sorted(set(summary["hypothesis_id"]).difference(configured))
        raise ValueError(
            f"strategy_summary.csv scope mismatch: missing={missing}, extra={extra}"
        )

    expected_audit_schema = str(source.get("validation_audit_schema") or "")
    if validation_audit.get("schema") != expected_audit_schema:
        raise ValueError("v2.17 validation audit schema mismatch")
    if _as_int(validation_audit.get("strategies"), label="audit strategies") != len(
        configured
    ):
        raise ValueError("v2.17 validation audit strategy count mismatch")
    if _as_int(validation_audit.get("validated"), label="audit validated") != len(
        configured
    ):
        raise ValueError("v2.17 validation audit is not fully validated")
    if list(validation_audit.get("required_engines") or []) != required_engines:
        raise ValueError("v2.17 validation audit engine order mismatch")
    if not _as_bool(validation_audit.get("parameters_frozen")):
        raise ValueError("v2.17 validation audit parameters are not frozen")
    if not _as_bool(validation_audit.get("whole_shares_only")):
        raise ValueError("v2.17 validation audit allows fractional shares")
    if _as_bool(validation_audit.get("fractional_shares_allowed")):
        raise ValueError("v2.17 validation audit allows fractional shares")
    if _as_bool(validation_audit.get("automatic_live_promotion")):
        raise ValueError("v2.17 validation audit grants live promotion")
    if _as_int(validation_audit.get("broker_calls"), label="audit broker_calls") != 0:
        raise ValueError("v2.17 validation audit contains broker calls")
    if _as_int(validation_audit.get("order_calls"), label="audit order_calls") != 0:
        raise ValueError("v2.17 validation audit contains order calls")
    if not _authority_is_none(validation_audit.get("execution_authority")):
        raise ValueError("v2.17 validation audit grants execution authority")

    evidence_paths = [
        handoff_config_path,
        validation_config_path,
        summary_path,
        engine_path,
        validation_audit_path,
    ]
    rows: list[dict[str, Any]] = []

    for hypothesis_id, strategy in configured.items():
        summary_row = summary.loc[summary["hypothesis_id"] == hypothesis_id].iloc[0]
        if str(summary_row["strategy"]) != strategy:
            raise ValueError(f"{hypothesis_id}: strategy mismatch")
        if str(summary_row["status"]) != "CROSS_ENGINE_VALIDATED":
            raise ValueError(f"{hypothesis_id}: not cross-engine validated")
        if _as_list(summary_row["blockers"]):
            raise ValueError(f"{hypothesis_id}: validation blockers present")
        if (
            _as_int(summary_row["broker_calls"], label=f"{hypothesis_id} broker_calls")
            != 0
        ):
            raise ValueError(f"{hypothesis_id}: broker calls observed")
        if (
            _as_int(summary_row["order_calls"], label=f"{hypothesis_id} order_calls")
            != 0
        ):
            raise ValueError(f"{hypothesis_id}: order calls observed")
        if not _authority_is_none(summary_row["execution_authority"]):
            raise ValueError(f"{hypothesis_id}: execution authority granted")

        packet_hash = str(summary_row["packet_hash"]).lower()
        bar_hash = str(summary_row["bar_hash"]).lower()
        if not _valid_sha256(packet_hash) or not _valid_sha256(bar_hash):
            raise ValueError(f"{hypothesis_id}: invalid packet/bar hash")

        symbols = _as_int(summary_row["symbols"], label="symbols")
        trades = _as_int(summary_row["trades"], label="trades")
        promotion = validation_config.get("promotion") or {}
        if symbols < _as_int(promotion.get("minimum_symbols"), label="minimum_symbols"):
            raise ValueError(f"{hypothesis_id}: insufficient symbol breadth")
        if trades < _as_int(
            promotion.get("minimum_total_trades"),
            label="minimum_total_trades",
        ):
            raise ValueError(f"{hypothesis_id}: insufficient trades")

        engine_rows = engine_results.loc[
            engine_results["hypothesis_id"] == hypothesis_id
        ].copy()
        observed_engines = set(engine_rows["engine"])
        if observed_engines != set(required_engines):
            raise ValueError(
                f"{hypothesis_id}: engine coverage mismatch "
                f"expected={required_engines}, "
                f"observed={sorted(observed_engines)}"
            )
        for engine in required_engines:
            engine_row = engine_rows.loc[engine_rows["engine"] == engine].iloc[0]
            if str(engine_row["strategy"]) != strategy:
                raise ValueError(f"{hypothesis_id}/{engine}: strategy mismatch")
            if str(engine_row["mode"]) != "FULL_ENGINE_REPLAY":
                raise ValueError(f"{hypothesis_id}/{engine}: partial replay")
            if not _as_bool(engine_row["parity"]):
                raise ValueError(f"{hypothesis_id}/{engine}: parity failed")
            if "error" in engine_row and str(
                engine_row.get("error") or ""
            ).strip().lower() not in {"", "nan"}:
                raise ValueError(f"{hypothesis_id}/{engine}: engine error present")
            if "warnings" in engine_row and str(
                engine_row.get("warnings") or ""
            ).strip().lower() not in {"", "nan"}:
                raise ValueError(f"{hypothesis_id}/{engine}: warnings present")
            if str(engine_row["packet_hash"]).lower() != packet_hash:
                raise ValueError(f"{hypothesis_id}/{engine}: packet hash mismatch")
            if str(engine_row["bar_hash"]).lower() != bar_hash:
                raise ValueError(f"{hypothesis_id}/{engine}: bar hash mismatch")
            if (
                _as_int(
                    engine_row["broker_calls"],
                    label=f"{hypothesis_id}/{engine} broker_calls",
                )
                != 0
            ):
                raise ValueError(f"{hypothesis_id}/{engine}: broker calls observed")
            if (
                _as_int(
                    engine_row["order_calls"],
                    label=f"{hypothesis_id}/{engine} order_calls",
                )
                != 0
            ):
                raise ValueError(f"{hypothesis_id}/{engine}: order calls observed")
            if not _authority_is_none(engine_row["execution_authority"]):
                raise ValueError(
                    f"{hypothesis_id}/{engine}: execution authority granted"
                )

        packet_path = validation_root / hypothesis_id / "packet_audit.json"
        packet_audit = _read_json(packet_path)
        expected_packet_schema = str(source.get("packet_audit_schema") or "")
        if packet_audit.get("schema") != expected_packet_schema:
            raise ValueError(f"{hypothesis_id}: packet audit schema mismatch")
        packet_checks = {
            "hypothesis_id": hypothesis_id,
            "strategy": strategy,
            "packet_hash": packet_hash,
            "bar_hash": bar_hash,
            "trades": trades,
            "symbols": symbols,
        }
        for key, expected in packet_checks.items():
            observed = packet_audit.get(key)
            if key in {"trades", "symbols"}:
                observed = _as_int(observed, label=f"packet {key}")
            else:
                observed = str(observed)
            if observed != expected:
                raise ValueError(f"{hypothesis_id}: packet audit {key} mismatch")
        if not _as_bool(packet_audit.get("parameters_frozen")):
            raise ValueError(f"{hypothesis_id}: packet parameters not frozen")
        if not _as_bool(packet_audit.get("whole_shares_only")):
            raise ValueError(f"{hypothesis_id}: packet allows fractional shares")
        if not _authority_is_none(packet_audit.get("execution_authority")):
            raise ValueError(f"{hypothesis_id}: packet grants authority")

        strategy_evidence = _required_evidence_files(
            validation_root,
            hypothesis_id,
            external_engines,
        )
        evidence_paths.extend(strategy_evidence)
        rows.append(
            {
                "registry_schema": REGISTRY_SCHEMA,
                "hypothesis_id": hypothesis_id,
                "strategy": strategy,
                "primary_timeframe": str(
                    validation_config.get("scope", {}).get("primary_timeframe", "")
                ),
                "execution_contract": str(
                    (
                        validation_config.get("scope", {}).get(
                            "supported_execution_contracts"
                        )
                        or [""]
                    )[0]
                ),
                "symbols": symbols,
                "trades": trades,
                "packet_hash": packet_hash,
                "bar_hash": bar_hash,
                "required_engines": "|".join(required_engines),
                "validation_status": "CROSS_ENGINE_VALIDATED",
                "handoff_status": "RESEARCH_HANDOFF_READY",
                "parameters_frozen": True,
                "whole_shares_only": True,
                "fractional_shares_allowed": False,
                "automatic_live_promotion": False,
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": AUTHORITY_NONE,
            }
        )

    registry = (
        pd.DataFrame(rows)
        .sort_values(["strategy", "hypothesis_id"])
        .reset_index(drop=True)
    )
    evidence_entries = [
        _evidence_entry(path, root)
        for path in sorted(set(evidence_paths), key=lambda item: str(item))
    ]
    evidence_digest = _canonical_hash(evidence_entries)
    evidence_manifest = {
        "schema": MANIFEST_SCHEMA,
        "source_validation_schema": expected_audit_schema,
        "file_count": len(evidence_entries),
        "files": evidence_entries,
        "manifest_sha256": evidence_digest,
    }

    records = registry.to_dict(orient="records")
    registry_digest = _canonical_hash(records)
    registry_csv_digest = hashlib.sha256(
        registry.to_csv(index=False, lineterminator="\n").encode("utf-8")
    ).hexdigest()
    audit = {
        "schema": AUDIT_SCHEMA,
        "handoff_ready": True,
        "configured_strategies": len(configured),
        "registered_strategies": len(registry),
        "required_engines": required_engines,
        "validation_status": "CROSS_ENGINE_VALIDATED",
        "registry_sha256": registry_digest,
        "registry_csv_sha256": registry_csv_digest,
        "evidence_manifest_sha256": evidence_digest,
        "evidence_file_count": len(evidence_entries),
        "parameters_frozen": True,
        "whole_shares_only": True,
        "fractional_shares_allowed": False,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": AUTHORITY_NONE,
    }
    return registry, evidence_manifest, audit


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def write_cross_engine_handoff(
    project_root: str | Path,
    *,
    config_path: str | Path | None = None,
    output_root: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any], Path]:
    root = Path(project_root).resolve()
    registry, evidence_manifest, audit = build_cross_engine_handoff(
        root,
        config_path=config_path,
    )
    destination = (
        Path(output_root).resolve()
        if output_root is not None
        else root / DEFAULT_OUTPUT_ROOT
    )
    destination.mkdir(parents=True, exist_ok=True)

    registry_records = registry.to_dict(orient="records")
    _atomic_write_text(
        destination / "registry.json",
        json.dumps(registry_records, indent=2, sort_keys=True) + "\n",
    )
    csv_text = registry.to_csv(index=False, lineterminator="\n")
    _atomic_write_text(destination / "registry.csv", csv_text)
    _atomic_write_text(
        destination / "evidence_manifest.json",
        json.dumps(evidence_manifest, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write_text(
        destination / "audit.json",
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
    )
    return registry, evidence_manifest, audit, destination


def verify_cross_engine_handoff(
    project_root: str | Path,
    *,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    destination = (
        Path(output_root).resolve()
        if output_root is not None
        else root / DEFAULT_OUTPUT_ROOT
    )
    errors: list[str] = []

    try:
        audit = _read_json(destination / "audit.json")
        manifest = _read_json(destination / "evidence_manifest.json")
        registry_json = json.loads(
            (destination / "registry.json").read_text(encoding="utf-8")
        )
        registry_csv = _read_csv(destination / "registry.csv")
    except (
        FileNotFoundError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        return {
            "schema": "cross_engine_handoff_verification_v2_18",
            "valid": False,
            "errors": [str(exc)],
            "execution_authority": AUTHORITY_NONE,
        }

    if audit.get("schema") != AUDIT_SCHEMA:
        errors.append("audit schema mismatch")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append("manifest schema mismatch")
    if not isinstance(registry_json, list) or not registry_json:
        errors.append("registry JSON is empty or invalid")
        registry_json = []

    entries = manifest.get("files")
    if not isinstance(entries, list):
        errors.append("manifest files are invalid")
        entries = []
    if _canonical_hash(entries) != str(manifest.get("manifest_sha256") or ""):
        errors.append("evidence manifest hash mismatch")
    if str(audit.get("evidence_manifest_sha256") or "") != str(
        manifest.get("manifest_sha256") or ""
    ):
        errors.append("audit/manifest hash mismatch")

    seen_paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            errors.append("invalid evidence entry")
            continue
        relative = str(entry.get("path") or "")
        if relative in seen_paths:
            errors.append(f"duplicate evidence path: {relative}")
            continue
        seen_paths.add(relative)
        try:
            path = _resolve_evidence_path(root, relative)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not path.is_file():
            errors.append(f"missing evidence file: {relative}")
            continue
        try:
            expected_size = _as_int(entry.get("size_bytes"), label=f"{relative} size")
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if int(path.stat().st_size) != expected_size:
                errors.append(f"evidence size mismatch: {relative}")
        if sha256_file(path) != str(entry.get("sha256") or ""):
            errors.append(f"evidence hash mismatch: {relative}")

    registry_hash = _canonical_hash(registry_json)
    if registry_hash != str(audit.get("registry_sha256") or ""):
        errors.append("registry hash mismatch")
    registry_csv_hash = sha256_file(destination / "registry.csv")
    if registry_csv_hash != str(audit.get("registry_csv_sha256") or ""):
        errors.append("registry CSV hash mismatch")
    if len(registry_json) != len(registry_csv):
        errors.append("registry JSON/CSV row count mismatch")
    json_ids = {
        str(row.get("hypothesis_id"))
        for row in registry_json
        if isinstance(row, Mapping)
    }
    if "hypothesis_id" not in registry_csv:
        errors.append("registry CSV hypothesis_id missing")
        csv_ids: set[str] = set()
    else:
        csv_ids = set(registry_csv["hypothesis_id"].astype(str))
    if json_ids != csv_ids:
        errors.append("registry JSON/CSV hypothesis mismatch")

    for row in registry_json:
        if not isinstance(row, Mapping):
            errors.append("invalid registry row")
            continue
        hypothesis_id = str(row.get("hypothesis_id") or "UNKNOWN")
        if row.get("registry_schema") != REGISTRY_SCHEMA:
            errors.append(f"{hypothesis_id}: registry schema mismatch")
        if row.get("validation_status") != "CROSS_ENGINE_VALIDATED":
            errors.append(f"{hypothesis_id}: validation status mismatch")
        if row.get("handoff_status") != "RESEARCH_HANDOFF_READY":
            errors.append(f"{hypothesis_id}: handoff status mismatch")
        if _as_bool(row.get("automatic_live_promotion")):
            errors.append(f"{hypothesis_id}: live promotion enabled")
        for field in ("broker_calls", "order_calls"):
            try:
                count = _as_int(row.get(field), label=field)
            except ValueError as exc:
                errors.append(f"{hypothesis_id}: {exc}")
            else:
                if count != 0:
                    errors.append(f"{hypothesis_id}: {field} present")
        if not _authority_is_none(row.get("execution_authority")):
            errors.append(f"{hypothesis_id}: execution authority granted")

    if not _as_bool(audit.get("handoff_ready")):
        errors.append("audit is not handoff-ready")
    count_checks = (
        (audit, "registered_strategies", len(registry_json), "audit"),
        (audit, "configured_strategies", len(registry_json), "audit"),
        (manifest, "file_count", len(entries), "manifest"),
        (audit, "evidence_file_count", len(entries), "audit"),
    )
    for payload, field, expected, source in count_checks:
        try:
            observed = _as_int(payload.get(field), label=f"{source} {field}")
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if observed != expected:
                errors.append(f"{source} {field} mismatch")
    if _as_bool(audit.get("automatic_live_promotion")):
        errors.append("audit enables live promotion")
    for field in ("broker_calls", "order_calls"):
        try:
            count = _as_int(audit.get(field), label=f"audit {field}")
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if count != 0:
                errors.append(f"audit {field} present")
    if not _authority_is_none(audit.get("execution_authority")):
        errors.append("audit grants execution authority")

    return {
        "schema": "cross_engine_handoff_verification_v2_18",
        "valid": not errors,
        "errors": errors,
        "registered_strategies": len(registry_json),
        "evidence_file_count": len(entries),
        "registry_sha256": registry_hash,
        "evidence_manifest_sha256": str(manifest.get("manifest_sha256") or ""),
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": AUTHORITY_NONE,
    }
