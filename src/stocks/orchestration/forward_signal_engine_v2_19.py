from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.orchestration.forward_signal_engine import (
    build_forward_signal_state,
)
from stocks.orchestration.validated_strategy_deployment_v2_19 import (
    DEFAULT_OUTPUT_ROOT as DEPLOYMENT_OUTPUT_ROOT,
)
from stocks.orchestration.validated_strategy_deployment_v2_19 import (
    verify_validated_strategy_deployment,
)

SCHEMA = "validated_forward_signal_state_v2_19"
DEFAULT_OUTPUT_ROOT = Path(
    "artifacts/research_runtime/validated_forward_signal_state_v2_19"
)
AUTHORITY_NONE = "NONE"


def build_validated_forward_signal_state(
    project_root: str | Path,
    *,
    deployment_root: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()
    source = (
        Path(deployment_root).resolve()
        if deployment_root is not None
        else root / DEPLOYMENT_OUTPUT_ROOT
    )
    verification = verify_validated_strategy_deployment(
        root,
        output_root=source,
    )
    if not verification.get("valid"):
        return pd.DataFrame(), {
            "schema": SCHEMA,
            "ready": False,
            "reason": "VALIDATED_DEPLOYMENT_VERIFICATION_FAILED",
            "errors": verification.get("errors") or [],
            "broker_calls": 0,
            "order_calls": 0,
            "execution_authority": AUTHORITY_NONE,
        }

    registry_path = source / "registry.csv"
    registry = pd.read_csv(registry_path, dtype={"hypothesis_id": str})
    frame, base_audit = build_forward_signal_state(
        root,
        strategy_registry=registry,
        required_status_column="deployment_status",
        required_status="RESEARCH_SIGNAL_ELIGIBLE",
    )
    source_reason = str(base_audit.get("reason") or "")
    if source_reason in {
        "CANDIDATE_STRATEGY_MATRIX_MISSING",
        "CANDIDATE_STRATEGY_MATRIX_EMPTY",
    }:
        return pd.DataFrame(), {
            "schema": SCHEMA,
            "ready": False,
            "reason": source_reason,
            "errors": [source_reason],
            "eligible_strategies": len(registry),
            "strict_validated_deployment_gate": True,
            "broker_calls": 0,
            "order_calls": 0,
            "execution_authority": AUTHORITY_NONE,
        }

    eligible_ids = set(registry["hypothesis_id"].astype(str))
    if not frame.empty:
        ready_rows = frame.loc[frame["new_entry_ready"].astype(bool)]
        unauthorized = sorted(
            set(ready_rows["hypothesis_id"].astype(str)).difference(eligible_ids)
        )
        if unauthorized:
            raise ValueError(
                "forward signal escaped validated deployment: " + "|".join(unauthorized)
            )
        frame["deployment_registry_sha256"] = verification["registry_sha256"]
        frame["execution_authority"] = AUTHORITY_NONE
        frame["broker_calls"] = 0
        frame["order_calls"] = 0

    audit = {
        **base_audit,
        "schema": SCHEMA,
        "ready": True,
        "eligible_strategies": len(eligible_ids),
        "deployment_registry_sha256": verification["registry_sha256"],
        "source_fingerprint": verification["source_fingerprint"],
        "strict_validated_deployment_gate": True,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": AUTHORITY_NONE,
    }
    return frame, audit


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def write_validated_forward_signal_state(
    project_root: str | Path,
    *,
    deployment_root: str | Path | None = None,
    output_root: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], Path]:
    root = Path(project_root).resolve()
    frame, audit = build_validated_forward_signal_state(
        root,
        deployment_root=deployment_root,
    )
    if not audit.get("ready"):
        raise ValueError(
            "validated forward signal gate is blocked: "
            + "|".join(audit.get("errors") or [str(audit.get("reason"))])
        )
    destination = (
        Path(output_root).resolve()
        if output_root is not None
        else root / DEFAULT_OUTPUT_ROOT
    )
    _atomic_write(
        destination / "signals.csv",
        frame.to_csv(index=False, lineterminator="\n"),
    )
    _atomic_write(
        destination / "audit.json",
        json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n",
    )
    return frame, audit, destination


__all__ = [
    "SCHEMA",
    "build_validated_forward_signal_state",
    "write_validated_forward_signal_state",
]
