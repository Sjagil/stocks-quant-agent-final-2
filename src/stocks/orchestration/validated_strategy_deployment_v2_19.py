from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from stocks.research.cross_engine_handoff_v2_18 import (
    verify_cross_engine_handoff,
)

SCHEMA = "validated_strategy_research_deployment_v2_19"
REGISTRY_SCHEMA = "validated_strategy_deployment_registry_v2_19"
MANIFEST_SCHEMA = "validated_strategy_deployment_manifest_v2_19"
AUDIT_SCHEMA = "validated_strategy_deployment_audit_v2_19"
VERIFY_SCHEMA = "validated_strategy_deployment_verification_v2_19"

DEFAULT_CONFIG = Path("config/validated_strategy_deployment_v2_19.yaml")
DEFAULT_OUTPUT_ROOT = Path(
    "artifacts/research_runtime/validated_strategy_deployment_v2_19"
)
AUTHORITY_NONE = "NONE"
SHA256_LENGTH = 64


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path}: expected a YAML object")
    return payload


def _read_json(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(path)
    try:
        return pd.read_csv(path, dtype={"hypothesis_id": str})
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"{path}: empty CSV") from exc


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_sha256(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return len(text) == SHA256_LENGTH and all(
        char in "0123456789abcdef" for char in text
    )


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def _as_int(value: Any, *, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: expected integer, got {value!r}") from exc


def _authority_is_none(value: Any) -> bool:
    return str(value or "").strip().upper() == AUTHORITY_NONE


def _resolve_inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {relative}") from exc
    return candidate


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {path}") from exc


def _require_columns(
    frame: pd.DataFrame,
    columns: set[str],
    *,
    source: str,
) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{source}: missing columns {missing}")


def _normalize_parameters(value: Any) -> tuple[str, str]:
    if isinstance(value, Mapping):
        payload = dict(value)
    else:
        try:
            payload = json.loads(str(value))
        except json.JSONDecodeError as exc:
            raise ValueError("invalid params_json") from exc
    if not isinstance(payload, dict) or not payload:
        raise ValueError("params_json must be a non-empty object")
    canonical = _canonical_json(payload)
    return canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_policy(config: Mapping[str, Any]) -> tuple[list[str], int]:
    policy = config.get("deployment")
    automation = config.get("automation")
    if not isinstance(policy, Mapping) or not isinstance(automation, Mapping):
        raise TypeError("v2.19 config: deployment/automation policy missing")

    expected = {
        "required_handoff_status": "RESEARCH_HANDOFF_READY",
        "required_roster_status": "BROADLY_VALIDATED_FINALIST",
        "require_exact_handoff_scope": True,
        "require_frozen_parameter_payload": True,
        "primary_timeframe": "1h",
        "execution_contract": "NEXT_OPEN_REPLAY",
        "overlap_policy": "REJECT",
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
            observed = _as_int(observed, label=f"deployment.{key}")
        else:
            observed = str(observed or "").strip()
        if observed != required:
            raise ValueError(f"v2.19 config: unsafe deployment.{key}={observed!r}")

    adapters = policy.get("required_signal_adapters")
    if not isinstance(adapters, list) or not adapters:
        raise ValueError("v2.19 config: required_signal_adapters missing")
    normalized = [str(item).strip() for item in adapters]
    if len(normalized) != len(set(normalized)):
        raise ValueError("v2.19 config: duplicate signal adapter")

    if str(automation.get("mode") or "") != "EXTERNAL_TRIGGER":
        raise ValueError("v2.19 config: automation mode must be EXTERNAL_TRIGGER")
    if str(automation.get("timezone") or "") != "UTC":
        raise ValueError("v2.19 config: automation timezone must be UTC")
    if not _as_bool(automation.get("write_only_when_changed")):
        raise ValueError("v2.19 config: idempotent writes must be enabled")
    timeout = _as_int(
        automation.get("lock_timeout_seconds"),
        label="automation.lock_timeout_seconds",
    )
    if timeout < 60:
        raise ValueError("v2.19 config: lock timeout is too short")
    return normalized, timeout


def _manifest_entry(path: Path, root: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(path)
    return {
        "path": _relative_to_root(path, root),
        "sha256": sha256_file(path),
        "size_bytes": int(path.stat().st_size),
    }


def build_validated_strategy_deployment(
    project_root: str | Path,
    *,
    config_path: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    root = Path(project_root).resolve()
    policy_path = (
        Path(config_path).resolve()
        if config_path is not None
        else root / DEFAULT_CONFIG
    )
    config = _read_yaml(policy_path)
    if config.get("schema") != SCHEMA:
        raise ValueError(f"{policy_path}: expected schema {SCHEMA}")
    adapters, lock_timeout = _validate_policy(config)

    source = config.get("source")
    if not isinstance(source, Mapping):
        raise TypeError("v2.19 config: source missing")
    handoff_root = _resolve_inside(root, str(source.get("handoff_root") or ""))
    roster_path = _resolve_inside(root, str(source.get("final_roster") or ""))

    handoff_verification = verify_cross_engine_handoff(
        root,
        output_root=handoff_root,
    )
    if not handoff_verification.get("valid"):
        raise ValueError(
            "v2.18 handoff verification failed: "
            + "|".join(handoff_verification.get("errors") or ["UNKNOWN"])
        )

    handoff_audit_path = handoff_root / "audit.json"
    handoff_registry_path = handoff_root / "registry.json"
    handoff_manifest_path = handoff_root / "evidence_manifest.json"
    handoff_audit = _read_json(handoff_audit_path)
    handoff_registry = _read_json(handoff_registry_path)
    if not isinstance(handoff_audit, dict) or not isinstance(handoff_registry, list):
        raise TypeError("v2.18 handoff outputs are invalid")
    if handoff_audit.get("schema") != source.get("handoff_audit_schema"):
        raise ValueError("v2.18 handoff audit schema mismatch")
    if not handoff_registry:
        raise ValueError("v2.18 handoff registry is empty")

    registry = pd.DataFrame(handoff_registry)
    _require_columns(
        registry,
        {
            "registry_schema",
            "hypothesis_id",
            "strategy",
            "primary_timeframe",
            "execution_contract",
            "packet_hash",
            "bar_hash",
            "handoff_status",
            "parameters_frozen",
            "automatic_live_promotion",
            "broker_calls",
            "order_calls",
            "execution_authority",
        },
        source="v2.18 registry",
    )
    registry["hypothesis_id"] = registry["hypothesis_id"].astype(str)
    if registry["hypothesis_id"].duplicated().any():
        raise ValueError("v2.18 registry has duplicate hypothesis_id")

    roster = _read_csv(roster_path)
    _require_columns(
        roster,
        {
            "hypothesis_id",
            "strategy",
            "roster_status",
            "params_json",
        },
        source="final roster",
    )
    roster["hypothesis_id"] = roster["hypothesis_id"].astype(str)
    if roster["hypothesis_id"].duplicated().any():
        raise ValueError("final roster has duplicate hypothesis_id")
    roster_map = {
        str(row["hypothesis_id"]): row for row in roster.to_dict(orient="records")
    }

    policy = config["deployment"]
    required_status = str(policy["required_handoff_status"])
    required_roster_status = str(policy["required_roster_status"])
    expected_registry_schema = str(source["handoff_registry_schema"])
    observed_strategies = set(registry["strategy"].astype(str))
    if observed_strategies != set(adapters):
        raise ValueError(
            "v2.18 strategy scope mismatch: "
            f"expected={sorted(adapters)}, observed={sorted(observed_strategies)}"
        )

    rows: list[dict[str, Any]] = []
    for handoff_row in registry.to_dict(orient="records"):
        hypothesis_id = str(handoff_row["hypothesis_id"])
        strategy = str(handoff_row["strategy"])
        if handoff_row["registry_schema"] != expected_registry_schema:
            raise ValueError(f"{hypothesis_id}: handoff registry schema mismatch")
        if handoff_row["handoff_status"] != required_status:
            raise ValueError(f"{hypothesis_id}: handoff is not ready")
        if not _as_bool(handoff_row["parameters_frozen"]):
            raise ValueError(f"{hypothesis_id}: handoff parameters are not frozen")
        if _as_bool(handoff_row["automatic_live_promotion"]):
            raise ValueError(f"{hypothesis_id}: handoff enables live promotion")
        if _as_int(handoff_row["broker_calls"], label="broker_calls") != 0:
            raise ValueError(f"{hypothesis_id}: handoff has broker calls")
        if _as_int(handoff_row["order_calls"], label="order_calls") != 0:
            raise ValueError(f"{hypothesis_id}: handoff has order calls")
        if not _authority_is_none(handoff_row["execution_authority"]):
            raise ValueError(f"{hypothesis_id}: handoff grants authority")
        if str(handoff_row["primary_timeframe"]) != policy["primary_timeframe"]:
            raise ValueError(f"{hypothesis_id}: timeframe mismatch")
        if str(handoff_row["execution_contract"]) != policy["execution_contract"]:
            raise ValueError(f"{hypothesis_id}: execution contract mismatch")
        if not _valid_sha256(handoff_row["packet_hash"]) or not _valid_sha256(
            handoff_row["bar_hash"]
        ):
            raise ValueError(f"{hypothesis_id}: invalid source hashes")

        roster_row = roster_map.get(hypothesis_id)
        if roster_row is None:
            raise ValueError(f"{hypothesis_id}: final roster row missing")
        if str(roster_row["strategy"]) != strategy:
            raise ValueError(f"{hypothesis_id}: final roster strategy mismatch")
        if str(roster_row["roster_status"]) != required_roster_status:
            raise ValueError(f"{hypothesis_id}: final roster status is not eligible")
        params_json, parameters_sha256 = _normalize_parameters(
            roster_row["params_json"]
        )

        rows.append(
            {
                "registry_schema": REGISTRY_SCHEMA,
                "hypothesis_id": hypothesis_id,
                "strategy": strategy,
                "signal_adapter": strategy,
                "primary_timeframe": str(policy["primary_timeframe"]),
                "execution_contract": str(policy["execution_contract"]),
                "params_json": params_json,
                "parameters_sha256": parameters_sha256,
                "source_packet_hash": str(handoff_row["packet_hash"]),
                "source_bar_hash": str(handoff_row["bar_hash"]),
                "source_registry_sha256": str(handoff_audit["registry_sha256"]),
                "source_evidence_manifest_sha256": str(
                    handoff_audit["evidence_manifest_sha256"]
                ),
                "deployment_status": "RESEARCH_SIGNAL_ELIGIBLE",
                "automatic_live_promotion": False,
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": AUTHORITY_NONE,
            }
        )

    deployment = (
        pd.DataFrame(rows)
        .sort_values(["strategy", "hypothesis_id"])
        .reset_index(drop=True)
    )
    records = deployment.to_dict(orient="records")
    registry_sha256 = _canonical_hash(records)
    registry_csv_sha256 = hashlib.sha256(
        deployment.to_csv(index=False, lineterminator="\n").encode("utf-8")
    ).hexdigest()

    evidence_paths = [
        policy_path,
        handoff_audit_path,
        handoff_registry_path,
        handoff_manifest_path,
        roster_path,
    ]
    entries = [
        _manifest_entry(path, root)
        for path in sorted(evidence_paths, key=lambda item: str(item))
    ]
    manifest_sha256 = _canonical_hash(entries)
    source_fingerprint = _canonical_hash(
        {
            "deployment_config": sha256_file(policy_path),
            "handoff_registry": handoff_audit["registry_sha256"],
            "handoff_evidence": handoff_audit["evidence_manifest_sha256"],
            "roster": sha256_file(roster_path),
        }
    )
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "file_count": len(entries),
        "files": entries,
        "manifest_sha256": manifest_sha256,
        "source_fingerprint": source_fingerprint,
    }
    audit = {
        "schema": AUDIT_SCHEMA,
        "deployment_ready": True,
        "configured_strategies": len(adapters),
        "eligible_strategies": len(deployment),
        "signal_adapters": adapters,
        "registry_sha256": registry_sha256,
        "registry_csv_sha256": registry_csv_sha256,
        "source_manifest_sha256": manifest_sha256,
        "source_fingerprint": source_fingerprint,
        "lock_timeout_seconds": lock_timeout,
        "overlap_policy": "REJECT",
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": AUTHORITY_NONE,
    }
    return deployment, manifest, audit


def _write_if_changed(path: Path, text: str) -> bool:
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)
    return True


@contextmanager
def exclusive_run_lock(
    path: Path,
    *,
    timeout_seconds: int,
):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        age_seconds = max(0.0, time.time() - path.stat().st_mtime)
        if age_seconds > timeout_seconds:
            path.unlink()
        else:
            raise RuntimeError(f"AUTOMATION_RUN_ALREADY_ACTIVE:{path}")

    payload = {
        "schema": "validated_strategy_automation_lock_v2_19",
        "pid": os.getpid(),
        "execution_authority": AUTHORITY_NONE,
    }
    try:
        descriptor = os.open(
            path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as exc:
        raise RuntimeError(f"AUTOMATION_RUN_ALREADY_ACTIVE:{path}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True)
            handle.write("\n")
        yield path
    finally:
        path.unlink(missing_ok=True)


def write_validated_strategy_deployment(
    project_root: str | Path,
    *,
    config_path: str | Path | None = None,
    output_root: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any], Path, bool]:
    root = Path(project_root).resolve()
    registry, manifest, audit = build_validated_strategy_deployment(
        root,
        config_path=config_path,
    )
    destination = (
        Path(output_root).resolve()
        if output_root is not None
        else root / DEFAULT_OUTPUT_ROOT
    )
    contents = {
        "registry.json": json.dumps(
            registry.to_dict(orient="records"), indent=2, sort_keys=True
        )
        + "\n",
        "registry.csv": registry.to_csv(index=False, lineterminator="\n"),
        "source_manifest.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        "audit.json": json.dumps(audit, indent=2, sort_keys=True) + "\n",
    }
    changes = [
        _write_if_changed(destination / name, text) for name, text in contents.items()
    ]
    changed = any(changes)
    return registry, manifest, audit, destination, changed


def verify_validated_strategy_deployment(
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
        manifest = _read_json(destination / "source_manifest.json")
        registry_json = _read_json(destination / "registry.json")
        registry_csv = _read_csv(destination / "registry.csv")
    except (
        FileNotFoundError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        return {
            "schema": VERIFY_SCHEMA,
            "valid": False,
            "errors": [str(exc)],
            "execution_authority": AUTHORITY_NONE,
        }

    if not isinstance(audit, dict) or audit.get("schema") != AUDIT_SCHEMA:
        errors.append("audit schema mismatch")
        audit = audit if isinstance(audit, dict) else {}
    if not isinstance(manifest, dict) or manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append("manifest schema mismatch")
        manifest = manifest if isinstance(manifest, dict) else {}
    if not isinstance(registry_json, list) or not registry_json:
        errors.append("registry JSON is empty or invalid")
        registry_json = []

    entries = manifest.get("files")
    if not isinstance(entries, list):
        errors.append("manifest files are invalid")
        entries = []
    if _canonical_hash(entries) != str(manifest.get("manifest_sha256") or ""):
        errors.append("source manifest hash mismatch")
    if str(audit.get("source_manifest_sha256") or "") != str(
        manifest.get("manifest_sha256") or ""
    ):
        errors.append("audit/source manifest hash mismatch")
    if str(audit.get("source_fingerprint") or "") != str(
        manifest.get("source_fingerprint") or ""
    ):
        errors.append("audit/source fingerprint mismatch")

    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            errors.append("invalid manifest entry")
            continue
        relative = str(entry.get("path") or "")
        if relative in seen:
            errors.append(f"duplicate manifest path: {relative}")
            continue
        seen.add(relative)
        try:
            path = _resolve_inside(root, relative)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not path.is_file():
            errors.append(f"missing source file: {relative}")
            continue
        if sha256_file(path) != str(entry.get("sha256") or ""):
            errors.append(f"source hash mismatch: {relative}")
        try:
            expected_size = _as_int(entry.get("size_bytes"), label=relative)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if int(path.stat().st_size) != expected_size:
                errors.append(f"source size mismatch: {relative}")

    registry_hash = _canonical_hash(registry_json)
    if registry_hash != str(audit.get("registry_sha256") or ""):
        errors.append("registry hash mismatch")
    if sha256_file(destination / "registry.csv") != str(
        audit.get("registry_csv_sha256") or ""
    ):
        errors.append("registry CSV hash mismatch")
    if len(registry_json) != len(registry_csv):
        errors.append("registry JSON/CSV row count mismatch")

    json_ids: set[str] = set()
    for row in registry_json:
        if not isinstance(row, Mapping):
            errors.append("invalid registry row")
            continue
        hypothesis_id = str(row.get("hypothesis_id") or "UNKNOWN")
        json_ids.add(hypothesis_id)
        if row.get("registry_schema") != REGISTRY_SCHEMA:
            errors.append(f"{hypothesis_id}: registry schema mismatch")
        if row.get("deployment_status") != "RESEARCH_SIGNAL_ELIGIBLE":
            errors.append(f"{hypothesis_id}: deployment status mismatch")
        params_json = str(row.get("params_json") or "")
        try:
            _, parameter_hash = _normalize_parameters(params_json)
        except ValueError as exc:
            errors.append(f"{hypothesis_id}: {exc}")
        else:
            if parameter_hash != str(row.get("parameters_sha256") or ""):
                errors.append(f"{hypothesis_id}: parameter hash mismatch")
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

    csv_ids = (
        set(registry_csv["hypothesis_id"].astype(str))
        if "hypothesis_id" in registry_csv
        else set()
    )
    if json_ids != csv_ids:
        errors.append("registry JSON/CSV hypothesis mismatch")
    for field in ("configured_strategies", "eligible_strategies"):
        try:
            count = _as_int(audit.get(field), label=f"audit {field}")
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if count != len(registry_json):
                errors.append(f"audit {field} mismatch")
    if not _as_bool(audit.get("deployment_ready")):
        errors.append("audit is not deployment-ready")
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

    try:
        expected_registry, expected_manifest, expected_audit = (
            build_validated_strategy_deployment(root)
        )
    except (FileNotFoundError, TypeError, ValueError) as exc:
        errors.append(f"source deployment rebuild failed: {exc}")
    else:
        expected_hash = _canonical_hash(expected_registry.to_dict(orient="records"))
        if registry_hash != expected_hash:
            errors.append("registry differs from rebuilt source deployment")
        if str(manifest.get("manifest_sha256") or "") != str(
            expected_manifest["manifest_sha256"]
        ):
            errors.append("source manifest differs from rebuilt deployment")
        if str(audit.get("source_fingerprint") or "") != str(
            expected_audit["source_fingerprint"]
        ):
            errors.append("source fingerprint differs from rebuilt deployment")

    return {
        "schema": VERIFY_SCHEMA,
        "valid": not errors,
        "errors": errors,
        "eligible_strategies": len(registry_json),
        "registry_sha256": registry_hash,
        "source_fingerprint": str(audit.get("source_fingerprint") or ""),
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": AUTHORITY_NONE,
    }


__all__ = [
    "AUDIT_SCHEMA",
    "MANIFEST_SCHEMA",
    "REGISTRY_SCHEMA",
    "SCHEMA",
    "build_validated_strategy_deployment",
    "exclusive_run_lock",
    "verify_validated_strategy_deployment",
    "write_validated_strategy_deployment",
]
