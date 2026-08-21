from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
from datetime import datetime

import pandas as pd

from stocks.orchestration.dynamic_forward_signal_engine_v2_24 import (
    DEFAULT_OUTPUT_ROOT as SIGNAL_OUTPUT_ROOT,
    SCHEMA as SIGNAL_SCHEMA,
)
from stocks.orchestration.validated_portfolio_gateway_v2_20 import (
    DecisionGatewayPolicy,
    ValidatedDecisionBundle,
    build_validated_portfolio_intents,
)

SCHEMA = "dynamic_validated_portfolio_gateway_v2_24"
DEFAULT_OUTPUT_ROOT = Path(
    "artifacts/research_runtime/dynamic_validated_portfolio_gateway_v2_24"
)
DEFAULT_ELIGIBILITY_PATH = Path(
    "artifacts/research_runtime/shariah_financial_verification/verification.csv"
)
AUTHORITY_NONE = "NONE"


def build_dynamic_validated_portfolio_intents(
    signals: pd.DataFrame,
    signal_audit: Mapping[str, Any],
    eligibility: pd.DataFrame,
    *,
    decision_time: datetime,
    equity_eur: float,
    current_weights: Mapping[str, float] | None = None,
    policy: DecisionGatewayPolicy | None = None,
) -> ValidatedDecisionBundle:
    if signal_audit.get("schema") != SIGNAL_SCHEMA:
        raise ValueError("v2.24 dynamic signal audit schema mismatch")
    if not bool(signal_audit.get("ready")):
        raise ValueError("v2.24 dynamic signal audit is not ready")
    if not bool(signal_audit.get("strict_dynamic_deployment_gate")):
        raise ValueError("v2.24 dynamic deployment gate is missing")
    if str(signal_audit.get("execution_authority") or "").upper() != AUTHORITY_NONE:
        raise ValueError("v2.24 dynamic signal audit grants execution authority")
    if int(signal_audit.get("broker_calls", -1)) != 0 or int(signal_audit.get("order_calls", -1)) != 0:
        raise ValueError("v2.24 dynamic signal audit contains broker/order calls")

    # Reuse the already-tested v2.20 deterministic long-only/Shariah gateway.
    # Only the schema name is adapted; registry hash, source fingerprint, signal
    # authority and every signal row still go through the v2.20 checks.
    compatible_audit = dict(signal_audit)
    compatible_audit["schema"] = "validated_forward_signal_state_v2_19"
    compatible_audit["strict_validated_deployment_gate"] = True
    base = build_validated_portfolio_intents(
        signals,
        compatible_audit,
        eligibility,
        decision_time=decision_time,
        equity_eur=equity_eur,
        current_weights=current_weights,
        policy=policy,
    )
    audit = {
        **dict(base.audit),
        "schema": SCHEMA,
        "source_signal_schema": SIGNAL_SCHEMA,
        "dynamic_final_roster_deployment": True,
        "strict_dynamic_deployment_gate": True,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": AUTHORITY_NONE,
    }
    return ValidatedDecisionBundle(
        decision_id=base.decision_id,
        created_at=base.created_at,
        data_cutoff=base.data_cutoff,
        intents=base.intents,
        projection=base.projection,
        audit=audit,
        execution_authority=AUTHORITY_NONE,
    )


def build_dynamic_validated_portfolio_intents_from_project(
    project_root: str | Path,
    *,
    decision_time: datetime,
    equity_eur: float,
    current_weights: Mapping[str, float] | None = None,
    signal_root: str | Path | None = None,
    eligibility_path: str | Path | None = None,
    policy: DecisionGatewayPolicy | None = None,
) -> ValidatedDecisionBundle:
    root = Path(project_root).resolve()
    source = (
        Path(signal_root).resolve()
        if signal_root is not None
        else root / SIGNAL_OUTPUT_ROOT
    )
    eligibility_source = (
        Path(eligibility_path).resolve()
        if eligibility_path is not None
        else root / DEFAULT_ELIGIBILITY_PATH
    )
    signals = pd.read_csv(source / "signals.csv", dtype={"hypothesis_id": str})
    audit = json.loads((source / "audit.json").read_text(encoding="utf-8"))
    eligibility = pd.read_csv(eligibility_source)
    return build_dynamic_validated_portfolio_intents(
        signals,
        audit,
        eligibility,
        decision_time=decision_time,
        equity_eur=equity_eur,
        current_weights=current_weights,
        policy=policy,
    )


def write_dynamic_validated_portfolio_bundle(
    bundle: ValidatedDecisionBundle,
    output_root: str | Path,
) -> Path:
    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=True)
    targets = [
        {
            "symbol": target.symbol,
            "target_weight": target.target_weight,
            "confidence": target.confidence,
            "data_cutoff": target.data_cutoff.isoformat(),
            "strategy_ids": "|".join(target.strategy_ids),
            "hypothesis_ids": "|".join(target.hypothesis_ids),
        }
        for target in bundle.projection.targets
    ]
    intents = [
        {
            "intent_id": intent.intent_id,
            "symbol": intent.symbol,
            "action": getattr(intent.action, "value", str(intent.action)),
            "target_weight": intent.target_weight,
            "target_notional_eur": intent.target_notional_eur,
            "confidence": intent.confidence,
            "source": intent.source,
            "execution_authority": intent.execution_authority,
        }
        for intent in bundle.intents
    ]
    pd.DataFrame(targets).to_csv(output / "targets.csv", index=False)
    pd.DataFrame(intents).to_csv(output / "intents.csv", index=False)
    (output / "audit.json").write_text(
        json.dumps(dict(bundle.audit), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return output


__all__ = [
    "SCHEMA",
    "build_dynamic_validated_portfolio_intents",
    "build_dynamic_validated_portfolio_intents_from_project",
    "write_dynamic_validated_portfolio_bundle",
]
