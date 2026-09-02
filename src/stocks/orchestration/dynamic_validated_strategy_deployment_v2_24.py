from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from stocks.orchestration.strategy_forward_signals import (
    SUPPORTED_NEXT_OPEN_STRATEGIES,
)

SCHEMA = "dynamic_validated_strategy_deployment_v2_24"
REGISTRY_SCHEMA = "dynamic_validated_strategy_registry_v2_24"
AUDIT_SCHEMA = "dynamic_validated_strategy_deployment_audit_v2_24"
MANIFEST_SCHEMA = "dynamic_validated_strategy_evidence_manifest_v2_24"
VERIFY_SCHEMA = "dynamic_validated_strategy_deployment_verification_v2_24"
DEFAULT_CONFIG = Path("config/dynamic_validated_deployment_v2_24.yaml")
DEFAULT_OUTPUT_ROOT = Path(
    "artifacts/research_runtime/dynamic_validated_strategy_deployment_v2_24"
)
AUTHORITY_NONE = "NONE"


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
        default=str,
    )


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype={"hypothesis_id": str})


def _normalize_params(value: Any) -> tuple[str, str]:
    if isinstance(value, Mapping):
        payload = dict(value)
    else:
        try:
            payload = json.loads(str(value))
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid params_json") from exc
    if not isinstance(payload, dict) or not payload:
        raise ValueError("params_json must be a non-empty mapping")
    canonical = _canonical_json(payload)
    return canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_config(root: Path, config_path: str | Path | None) -> tuple[Path, dict[str, Any]]:
    path = (
        Path(config_path).resolve()
        if config_path is not None
        else (root / DEFAULT_CONFIG).resolve()
    )
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise ValueError(f"{path}: expected schema {SCHEMA}")
    return path, raw


def _resolve(root: Path, value: Any) -> Path:
    path = (root / str(value)).resolve()
    path.relative_to(root)
    return path


def _source_paths(root: Path, config: Mapping[str, Any]) -> dict[str, Path]:
    source = config.get("source")
    if not isinstance(source, Mapping):
        raise ValueError("dynamic deployment source config missing")
    required = (
        "final_roster",
        "final_roster_audit",
        "research_candidate_registry",
        "generated_adapter_audit",
    )
    return {name: _resolve(root, source[name]) for name in required}


def _policy(config: Mapping[str, Any]) -> Mapping[str, Any]:
    policy = config.get("deployment")
    if not isinstance(policy, Mapping):
        raise ValueError("dynamic deployment policy missing")
    if _boolean(policy.get("automatic_live_promotion")):
        raise ValueError("automatic live promotion must remain disabled")
    if int(policy.get("broker_calls", -1)) != 0 or int(policy.get("order_calls", -1)) != 0:
        raise ValueError("deployment policy cannot permit broker/order calls")
    if str(policy.get("execution_authority") or "").upper() != AUTHORITY_NONE:
        raise ValueError("deployment policy cannot grant execution authority")
    return policy


def _row_blockers(row: Mapping[str, Any], policy: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    strategy = str(row.get("strategy") or "")
    if str(row.get("roster_status") or "") != str(policy["required_roster_status"]):
        blockers.append("ROSTER_STATUS_NOT_ELIGIBLE")
    if str(row.get("execution_contract") or "") != str(policy["required_execution_contract"]):
        blockers.append("EXECUTION_CONTRACT_NOT_SUPPORTED")
    if _boolean(policy.get("require_research_deployment_ready", True)) and not _boolean(
        row.get("research_deployment_ready")
    ):
        blockers.append("RESEARCH_DEPLOYMENT_NOT_READY")
    if _boolean(policy.get("require_supported_forward_adapter", True)) and strategy not in SUPPORTED_NEXT_OPEN_STRATEGIES:
        blockers.append("FORWARD_ADAPTER_NOT_SUPPORTED")

    accepted_cross = {str(value) for value in policy.get("accepted_cross_engine_statuses", ())}
    observed_cross = str(row.get("cross_engine_status") or "")
    if accepted_cross and observed_cross not in accepted_cross:
        blockers.append("CROSS_ENGINE_EVIDENCE_NOT_ACCEPTED")

    accepted_general = {str(value) for value in policy.get("accepted_generalization_statuses", ())}
    observed_general = str(
        row.get("broad_generalization_status")
        or row.get("generalization_status")
        or ""
    )
    if accepted_general and observed_general not in accepted_general:
        blockers.append("GENERALIZATION_EVIDENCE_NOT_ACCEPTED")

    if str(row.get("execution_authority") or AUTHORITY_NONE).upper() != AUTHORITY_NONE:
        blockers.append("SOURCE_EXECUTION_AUTHORITY_PRESENT")
    return blockers


def build_dynamic_validated_strategy_deployment(
    project_root: str | Path,
    *,
    config_path: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    root = Path(project_root).resolve()
    policy_path, config = _load_config(root, config_path)
    policy = _policy(config)
    paths = _source_paths(root, config)

    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing dynamic deployment sources: " + "|".join(missing))

    roster = _read_csv(paths["final_roster"])
    if roster.empty:
        raise ValueError("final strategy roster is empty")
    required_columns = {
        "hypothesis_id",
        "strategy",
        "family",
        "source_engine",
        "params_json",
        "execution_contract",
        "roster_status",
        "research_deployment_ready",
        "cross_engine_status",
    }
    missing_columns = sorted(required_columns.difference(roster.columns))
    if missing_columns:
        raise ValueError("final roster missing columns: " + ",".join(missing_columns))

    adapter_audit = _read_json(paths["generated_adapter_audit"])
    if not adapter_audit.get("coverage_complete"):
        raise ValueError("v2.23 generated forward adapter coverage is not complete")
    if str(adapter_audit.get("execution_authority") or "").upper() != AUTHORITY_NONE:
        raise ValueError("v2.23 adapter audit grants execution authority")

    broad = roster.loc[
        roster["roster_status"].astype(str).eq(str(policy["required_roster_status"]))
    ].copy()
    if broad.empty:
        raise ValueError("no broadly validated finalists are available")

    source_hashes = {
        "config_sha256": sha256_file(policy_path),
        **{f"{name}_sha256": sha256_file(path) for name, path in paths.items()},
    }
    rows: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = []

    for row in broad.to_dict(orient="records"):
        hypothesis_id = str(row["hypothesis_id"])
        blockers = _row_blockers(row, policy)
        try:
            params_json, parameters_sha256 = _normalize_params(row.get("params_json"))
        except ValueError:
            params_json, parameters_sha256 = "{}", ""
            blockers.append("INVALID_FROZEN_PARAMETERS")

        evidence_payload = {
            "hypothesis_id": hypothesis_id,
            "strategy": str(row["strategy"]),
            "family": str(row["family"]),
            "source_engine": str(row["source_engine"]),
            "parameters_sha256": parameters_sha256,
            "cross_engine_status": str(row.get("cross_engine_status") or ""),
            "generalization_status": str(
                row.get("broad_generalization_status")
                or row.get("generalization_status")
                or ""
            ),
            "roster_status": str(row.get("roster_status") or ""),
            "execution_contract": str(row.get("execution_contract") or ""),
            "source_hashes": source_hashes,
        }
        evidence_sha256 = _canonical_hash(evidence_payload)

        base = {
            "hypothesis_id": hypothesis_id,
            "strategy": str(row["strategy"]),
            "family": str(row["family"]),
            "source_engine": str(row["source_engine"]),
            "primary_timeframe": str(row.get("primary_timeframe") or row.get("timeframe") or "1h"),
            "execution_contract": str(row.get("execution_contract") or ""),
            "params_json": params_json,
            "parameters_sha256": parameters_sha256,
            "cross_engine_status": str(row.get("cross_engine_status") or ""),
            "generalization_status": str(
                row.get("broad_generalization_status")
                or row.get("generalization_status")
                or ""
            ),
            "roster_status": str(row.get("roster_status") or ""),
            "forward_adapter": str(row["strategy"]),
            "evidence_sha256": evidence_sha256,
            "automatic_live_promotion": False,
            "broker_calls": 0,
            "order_calls": 0,
            "execution_authority": AUTHORITY_NONE,
        }
        if blockers:
            rejects.append({**base, "blockers": "|".join(dict.fromkeys(blockers))})
        else:
            rows.append(
                {
                    "registry_schema": REGISTRY_SCHEMA,
                    **base,
                    "deployment_status": "RESEARCH_SIGNAL_ELIGIBLE",
                }
            )

    registry = pd.DataFrame(rows)
    rejected = pd.DataFrame(rejects)
    if registry.empty:
        raise ValueError("dynamic deployment produced zero eligible strategies")
    registry = registry.sort_values(["strategy", "hypothesis_id"]).reset_index(drop=True)
    registry_records = registry.to_dict(orient="records")
    registry_sha256 = _canonical_hash(registry_records)
    source_fingerprint = _canonical_hash(source_hashes)

    manifest_entries = [
        {
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted([policy_path, *paths.values()], key=lambda value: str(value))
    ]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "files": manifest_entries,
        "file_count": len(manifest_entries),
        "manifest_sha256": _canonical_hash(manifest_entries),
        "source_fingerprint": source_fingerprint,
    }
    audit = {
        "schema": AUDIT_SCHEMA,
        "ready": True,
        "broad_finalists": int(len(broad)),
        "eligible_strategies": int(len(registry)),
        "excluded_finalists": int(len(rejected)),
        "eligible_strategy_names": sorted(registry["strategy"].astype(str).unique()),
        "excluded_strategy_names": sorted(rejected.get("strategy", pd.Series(dtype=str)).astype(str).unique()),
        "registry_sha256": registry_sha256,
        "source_fingerprint": source_fingerprint,
        "manifest_sha256": manifest["manifest_sha256"],
        "supported_forward_adapters": sorted(SUPPORTED_NEXT_OPEN_STRATEGIES),
        "strict_final_roster_gate": True,
        "parameters_frozen": True,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": AUTHORITY_NONE,
    }
    return registry, rejected, audit, manifest


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def write_dynamic_validated_strategy_deployment(
    project_root: str | Path,
    *,
    config_path: str | Path | None = None,
    output_root: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], Path]:
    root = Path(project_root).resolve()
    registry, rejected, audit, manifest = build_dynamic_validated_strategy_deployment(
        root, config_path=config_path
    )
    destination = (
        Path(output_root).resolve()
        if output_root is not None
        else root / DEFAULT_OUTPUT_ROOT
    )
    _atomic_write(destination / "registry.csv", registry.to_csv(index=False, lineterminator="\n"))
    _atomic_write(destination / "rejected.csv", rejected.to_csv(index=False, lineterminator="\n"))
    _atomic_write(destination / "audit.json", json.dumps(audit, indent=2, sort_keys=True) + "\n")
    _atomic_write(destination / "evidence_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return registry, rejected, audit, destination


def verify_dynamic_validated_strategy_deployment(
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
    registry_path = destination / "registry.csv"
    audit_path = destination / "audit.json"
    manifest_path = destination / "evidence_manifest.json"
    errors: list[str] = []
    if not registry_path.is_file() or not audit_path.is_file() or not manifest_path.is_file():
        return {
            "schema": VERIFY_SCHEMA,
            "valid": False,
            "errors": ["DEPLOYMENT_ARTIFACTS_MISSING"],
            "execution_authority": AUTHORITY_NONE,
        }
    registry = pd.read_csv(registry_path, dtype={"hypothesis_id": str})
    audit = _read_json(audit_path)
    manifest = _read_json(manifest_path)
    if registry.empty:
        errors.append("REGISTRY_EMPTY")
    observed_registry_sha = _canonical_hash(registry.to_dict(orient="records"))
    if observed_registry_sha != audit.get("registry_sha256"):
        errors.append("REGISTRY_HASH_MISMATCH")
    for entry in manifest.get("files", []):
        path = (root / str(entry.get("path") or "")).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            errors.append("MANIFEST_PATH_ESCAPE")
            continue
        if not path.is_file():
            errors.append("MANIFEST_SOURCE_MISSING")
        elif sha256_file(path) != entry.get("sha256"):
            errors.append("MANIFEST_SOURCE_HASH_MISMATCH")
    if _canonical_hash(manifest.get("files", [])) != manifest.get("manifest_sha256"):
        errors.append("MANIFEST_HASH_MISMATCH")
    if str(audit.get("execution_authority") or "").upper() != AUTHORITY_NONE:
        errors.append("EXECUTION_AUTHORITY_PRESENT")
    if int(audit.get("broker_calls", -1)) != 0 or int(audit.get("order_calls", -1)) != 0:
        errors.append("BROKER_OR_ORDER_CALLS_PRESENT")
    if not registry.empty:
        if not registry["strategy"].astype(str).isin(SUPPORTED_NEXT_OPEN_STRATEGIES).all():
            errors.append("UNSUPPORTED_FORWARD_ADAPTER_IN_REGISTRY")
        if not registry["deployment_status"].astype(str).eq("RESEARCH_SIGNAL_ELIGIBLE").all():
            errors.append("INVALID_DEPLOYMENT_STATUS")
    return {
        "schema": VERIFY_SCHEMA,
        "valid": not errors,
        "errors": list(dict.fromkeys(errors)),
        "eligible_strategies": int(len(registry)),
        "registry_sha256": audit.get("registry_sha256"),
        "source_fingerprint": audit.get("source_fingerprint"),
        "execution_authority": AUTHORITY_NONE,
        "broker_calls": 0,
        "order_calls": 0,
    }


__all__ = [
    "SCHEMA",
    "DEFAULT_OUTPUT_ROOT",
    "build_dynamic_validated_strategy_deployment",
    "write_dynamic_validated_strategy_deployment",
    "verify_dynamic_validated_strategy_deployment",
]
