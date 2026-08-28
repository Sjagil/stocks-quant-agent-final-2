from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pandas as pd

from stocks.contracts import IntentAction, TradeIntent
from stocks.portfolio.deterministic_allocator_v2_20 import (
    AUTHORITY_NONE,
    AllocationPolicy,
    AlphaProposal,
    AssetKind,
    ProjectionResult,
    project_long_only,
)

SCHEMA = "validated_portfolio_gateway_v2_20"
SIGNAL_AUDIT_SCHEMA = "validated_forward_signal_state_v2_19"
DEFAULT_SIGNAL_ROOT = Path(
    "artifacts/research_runtime/validated_forward_signal_state_v2_19"
)
DEFAULT_ELIGIBILITY_PATH = Path(
    "artifacts/research_runtime/shariah_financial_verification/verification.csv"
)
SHA256_LENGTH = 64


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def _finite(value: Any, *, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _sha256(value: Any, *, field: str) -> str:
    normalized = str(value or "").strip().lower()
    if len(normalized) != SHA256_LENGTH or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field} must be a SHA-256 hex digest")
    return normalized


def _utc(value: datetime | str, *, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed.astimezone(UTC)


def _required_columns(frame: pd.DataFrame, required: set[str], *, source: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{source}: missing columns {missing}")


@dataclass(frozen=True)
class DecisionGatewayPolicy:
    allocation: AllocationPolicy = field(default_factory=AllocationPolicy)
    max_signal_age: timedelta = timedelta(hours=2)
    minimum_strategy_votes: int = 1
    require_closed_bars: bool = True
    automatic_live_promotion: bool = False
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        if self.max_signal_age <= timedelta(0):
            raise ValueError("max_signal_age must be positive")
        if self.minimum_strategy_votes < 1:
            raise ValueError("minimum_strategy_votes must be positive")
        if not self.require_closed_bars:
            raise ValueError("validated gateway requires closed bars")
        if self.automatic_live_promotion:
            raise ValueError("automatic live promotion must remain disabled")
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("decision gateway cannot grant execution authority")


@dataclass(frozen=True)
class ValidatedDecisionBundle:
    decision_id: str
    created_at: datetime
    data_cutoff: datetime | None
    intents: tuple[TradeIntent, ...]
    projection: ProjectionResult
    audit: Mapping[str, Any]
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _sha256(self.decision_id, field="decision_id")
        _utc(self.created_at, field="created_at")
        if self.data_cutoff is not None:
            cutoff = _utc(self.data_cutoff, field="data_cutoff")
            if cutoff > self.created_at:
                raise ValueError("data_cutoff cannot be after decision time")
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("decision bundle cannot grant execution authority")
        if any(intent.execution_authority != AUTHORITY_NONE for intent in self.intents):
            raise ValueError("decision bundle contains an authorized intent")
        object.__setattr__(self, "audit", MappingProxyType(dict(self.audit)))


def _validate_signal_authority(signals: pd.DataFrame) -> None:
    if (
        not signals["execution_authority"]
        .astype(str)
        .str.upper()
        .eq(AUTHORITY_NONE)
        .all()
    ):
        raise ValueError("signal frame grants execution authority")
    for column in ("broker_calls", "order_calls"):
        values = pd.to_numeric(signals[column], errors="coerce")
        if values.isna().any() or not values.eq(0).all():
            raise ValueError(f"signal frame has non-zero {column}")
    if (
        "automatic_live_promotion" in signals
        and signals["automatic_live_promotion"].map(_boolean).any()
    ):
        raise ValueError("signal frame enables automatic live promotion")


def _validate_signal_audit(signal_audit: Mapping[str, Any]) -> tuple[str, str]:
    if signal_audit.get("schema") != SIGNAL_AUDIT_SCHEMA:
        raise ValueError("validated signal audit schema mismatch")
    if not _boolean(signal_audit.get("ready")):
        raise ValueError("validated signal audit is not ready")
    if not _boolean(signal_audit.get("strict_validated_deployment_gate")):
        raise ValueError("strict validated deployment gate is missing")
    if _boolean(signal_audit.get("automatic_live_promotion")):
        raise ValueError("signal audit enables automatic live promotion")
    if str(signal_audit.get("execution_authority") or "").upper() != AUTHORITY_NONE:
        raise ValueError("signal audit grants execution authority")
    if int(signal_audit.get("broker_calls", -1)) != 0:
        raise ValueError("signal audit has broker calls")
    if int(signal_audit.get("order_calls", -1)) != 0:
        raise ValueError("signal audit has order calls")
    return (
        _sha256(
            signal_audit.get("deployment_registry_sha256"),
            field="deployment_registry_sha256",
        ),
        _sha256(
            signal_audit.get("source_fingerprint"),
            field="source_fingerprint",
        ),
    )


def _eligibility_map(eligibility: pd.DataFrame) -> dict[str, dict[str, Any]]:
    _required_columns(
        eligibility,
        {"symbol", "trade_eligible"},
        source="Shariah eligibility",
    )
    normalized = eligibility.copy()
    normalized["symbol"] = normalized["symbol"].astype(str).str.upper().str.strip()
    if normalized["symbol"].eq("").any():
        raise ValueError("Shariah eligibility contains an empty symbol")
    if normalized["symbol"].duplicated().any():
        raise ValueError("Shariah eligibility contains duplicate symbols")
    return {str(row["symbol"]): row for row in normalized.to_dict(orient="records")}


def _asset_kind(row: Mapping[str, Any]) -> AssetKind:
    raw = str(
        row.get("asset_kind")
        or row.get("asset_type")
        or row.get("instrument_type")
        or row.get("security_type")
        or "STOCK"
    ).upper()
    if raw in {"ETF", "FUND", "EXCHANGE_TRADED_FUND"}:
        return AssetKind.ETF
    if raw in {"STOCK", "EQUITY", "COMMON_STOCK"}:
        return AssetKind.STOCK
    raise ValueError(f"unsupported asset kind: {raw}")


def _build_proposals(
    signals: pd.DataFrame,
    eligibility: pd.DataFrame,
    *,
    decision_time: datetime,
    policy: DecisionGatewayPolicy,
) -> tuple[list[AlphaProposal], dict[str, tuple[str, ...]]]:
    eligibility_by_symbol = _eligibility_map(eligibility)
    ready = signals.loc[
        signals["new_entry_ready"].map(_boolean)
        & signals["local_evidence_positive"].map(_boolean)
    ].copy()
    proposals: list[AlphaProposal] = []
    rejected: dict[str, tuple[str, ...]] = {}

    for symbol, group in ready.groupby("symbol", sort=True):
        normalized_symbol = str(symbol).upper().strip()
        reasons: list[str] = []
        eligibility_row = eligibility_by_symbol.get(normalized_symbol)
        if eligibility_row is None:
            reasons.append("SHARIAH_ELIGIBILITY_MISSING")
        elif not _boolean(eligibility_row.get("trade_eligible")):
            reasons.append("SHARIAH_NOT_VERIFIED")

        parsed_times = pd.to_datetime(
            group["signal_bar_time"],
            utc=True,
            errors="coerce",
        )
        if parsed_times.isna().any():
            reasons.append("INVALID_SIGNAL_BAR_TIME")
            data_cutoff = None
        else:
            data_cutoff = parsed_times.max().to_pydatetime()
            if data_cutoff > decision_time:
                reasons.append("POINT_IN_TIME_VIOLATION")
            elif decision_time - data_cutoff > policy.max_signal_age:
                reasons.append("STALE_SIGNAL")

        strategy_ids = tuple(sorted(set(group["strategy"].astype(str))))
        hypothesis_ids = tuple(sorted(set(group["hypothesis_id"].astype(str))))
        if len(hypothesis_ids) < policy.minimum_strategy_votes:
            reasons.append("INSUFFICIENT_STRATEGY_VOTES")

        scores = pd.to_numeric(group["applicability_score"], errors="coerce")
        if scores.isna().any() or not scores.map(math.isfinite).all():
            reasons.append("INVALID_APPLICABILITY_SCORE")
            best_score = 0.0
            average_score = 0.0
        else:
            best_score = max(0.0, min(100.0, float(scores.max()))) / 100.0
            average_score = max(0.0, min(100.0, float(scores.mean()))) / 100.0
        confidence = min(
            1.0,
            0.55 * best_score
            + 0.25 * average_score
            + 0.20 * min(len(hypothesis_ids) / 2.0, 1.0),
        )

        if reasons:
            rejected[normalized_symbol] = tuple(dict.fromkeys(reasons))
            continue
        assert eligibility_row is not None
        assert data_cutoff is not None
        proposals.append(
            AlphaProposal(
                symbol=normalized_symbol,
                asset_kind=_asset_kind(eligibility_row),
                alpha_score=best_score,
                confidence=confidence,
                data_cutoff=data_cutoff,
                strategy_ids=strategy_ids,
                hypothesis_ids=hypothesis_ids,
                shariah_eligible=True,
            )
        )

    return proposals, rejected


def _empty_projection(rejected: Mapping[str, tuple[str, ...]]) -> ProjectionResult:
    return ProjectionResult(
        targets=(),
        rejected=rejected,
        total_weight=0.0,
        cash_weight=1.0,
    )


def build_validated_portfolio_intents(
    signals: pd.DataFrame,
    signal_audit: Mapping[str, Any],
    eligibility: pd.DataFrame,
    *,
    decision_time: datetime,
    equity_eur: float,
    current_weights: Mapping[str, float] | None = None,
    policy: DecisionGatewayPolicy | None = None,
) -> ValidatedDecisionBundle:
    """Build execution-neutral intents from the strict v2.19 signal state.

    This is a pure, deterministic gateway. It accepts no broker object, performs
    no account lookup and cannot submit an order. The caller must provide the
    decision clock, equity and current weights explicitly.
    """

    active_policy = policy or DecisionGatewayPolicy()
    created_at = _utc(decision_time, field="decision_time")
    equity = _finite(equity_eur, field="equity_eur")
    if equity <= 0.0:
        raise ValueError("equity_eur must be positive")
    registry_sha256, source_fingerprint = _validate_signal_audit(signal_audit)

    required = {
        "symbol",
        "hypothesis_id",
        "strategy",
        "new_entry_ready",
        "local_evidence_positive",
        "applicability_score",
        "signal_bar_time",
        "deployment_registry_sha256",
        "execution_contract",
        "execution_authority",
        "broker_calls",
        "order_calls",
    }
    _required_columns(signals, required, source="validated forward signals")
    normalized = signals.copy()
    normalized["symbol"] = normalized["symbol"].astype(str).str.upper().str.strip()
    _validate_signal_authority(normalized)
    if (
        not normalized["deployment_registry_sha256"]
        .astype(str)
        .str.lower()
        .eq(registry_sha256)
        .all()
    ):
        raise ValueError("signal registry hash does not match validated audit")
    if not normalized["execution_contract"].astype(str).eq("NEXT_OPEN_REPLAY").all():
        raise ValueError("unsupported signal execution contract")

    weights = {
        str(symbol).upper().strip(): _finite(value, field=f"weight:{symbol}")
        for symbol, value in (current_weights or {}).items()
    }
    if any(value < 0.0 for value in weights.values()):
        raise ValueError("current_weights cannot contain short exposure")
    if sum(weights.values()) > 1.0 + 1e-12:
        raise ValueError("current_weights imply leverage")

    proposals, pre_projection_rejected = _build_proposals(
        normalized,
        eligibility,
        decision_time=created_at,
        policy=active_policy,
    )
    projection = (
        project_long_only(proposals, policy=active_policy.allocation)
        if proposals
        else _empty_projection(pre_projection_rejected)
    )
    combined_rejected = {
        **pre_projection_rejected,
        **dict(projection.rejected),
    }
    if combined_rejected != dict(projection.rejected):
        projection = ProjectionResult(
            targets=projection.targets,
            rejected=dict(sorted(combined_rejected.items())),
            total_weight=projection.total_weight,
            cash_weight=projection.cash_weight,
        )

    data_cutoff = (
        max(target.data_cutoff for target in projection.targets)
        if projection.targets
        else None
    )
    decision_payload = {
        "schema": SCHEMA,
        "created_at": created_at.isoformat(),
        "data_cutoff": data_cutoff.isoformat() if data_cutoff else None,
        "deployment_registry_sha256": registry_sha256,
        "source_fingerprint": source_fingerprint,
        "equity_eur": round(equity, 8),
        "current_weights": dict(sorted(weights.items())),
        "targets": [
            {
                "symbol": target.symbol,
                "target_weight": target.target_weight,
                "strategy_ids": target.strategy_ids,
                "hypothesis_ids": target.hypothesis_ids,
            }
            for target in projection.targets
        ],
        "rejected": dict(projection.rejected),
        "policy": {
            "max_total_weight": active_policy.allocation.max_total_weight,
            "max_stock_weight": active_policy.allocation.max_stock_weight,
            "max_etf_weight": active_policy.allocation.max_etf_weight,
            "max_open_positions": active_policy.allocation.max_open_positions,
            "minimum_confidence": active_policy.allocation.minimum_confidence,
        },
    }
    decision_id = _canonical_hash(decision_payload)

    intents: list[TradeIntent] = []
    for target in projection.targets:
        current = weights.get(target.symbol, 0.0)
        if target.target_weight > current + 1e-12:
            action = IntentAction.INCREASE
        elif target.target_weight < current - 1e-12:
            action = IntentAction.DECREASE
        else:
            action = IntentAction.HOLD
        intent_id = _canonical_hash(
            {
                "decision_id": decision_id,
                "symbol": target.symbol,
                "action": action.value,
                "target_weight": target.target_weight,
            }
        )
        intents.append(
            TradeIntent(
                created_at=created_at,
                symbol=target.symbol,
                action=action,
                target_weight=target.target_weight,
                target_notional_eur=round(equity * target.target_weight, 8),
                confidence=target.confidence,
                source=SCHEMA,
                execution_authority=AUTHORITY_NONE,
                rationale=(
                    "CROSS_ENGINE_VALIDATED_SIGNAL",
                    "SHARIAH_VERIFIED",
                    "DETERMINISTIC_LONG_ONLY_PROJECTION",
                ),
                metadata={
                    "decision_id": decision_id,
                    "data_cutoff": target.data_cutoff.isoformat(),
                    "deployment_registry_sha256": registry_sha256,
                    "source_fingerprint": source_fingerprint,
                    "strategy_ids": list(target.strategy_ids),
                    "hypothesis_ids": list(target.hypothesis_ids),
                    "asset_kind": target.asset_kind.value,
                    "automatic_live_promotion": False,
                    "broker_calls": 0,
                    "order_calls": 0,
                },
                intent_id=intent_id,
            )
        )

    audit = {
        "schema": SCHEMA,
        "ready": True,
        "decision_id": decision_id,
        "decision_time": created_at.isoformat(),
        "data_cutoff": data_cutoff.isoformat() if data_cutoff else None,
        "input_signal_rows": len(normalized),
        "ready_signal_rows": int(
            (
                normalized["new_entry_ready"].map(_boolean)
                & normalized["local_evidence_positive"].map(_boolean)
            ).sum()
        ),
        "projected_positions": len(projection.targets),
        "intent_count": len(intents),
        "rejected_symbols": dict(projection.rejected),
        "total_weight": projection.total_weight,
        "cash_weight": projection.cash_weight,
        "deployment_registry_sha256": registry_sha256,
        "source_fingerprint": source_fingerprint,
        "closed_bars_only": True,
        "point_in_time_validated": True,
        "long_only": True,
        "shariah_only": True,
        "leverage_allowed": False,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": AUTHORITY_NONE,
    }
    return ValidatedDecisionBundle(
        decision_id=decision_id,
        created_at=created_at,
        data_cutoff=data_cutoff,
        intents=tuple(intents),
        projection=projection,
        audit=audit,
    )


def build_validated_portfolio_intents_from_project(
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
        else root / DEFAULT_SIGNAL_ROOT
    )
    eligibility_source = (
        Path(eligibility_path).resolve()
        if eligibility_path is not None
        else root / DEFAULT_ELIGIBILITY_PATH
    )
    signal_path = source / "signals.csv"
    audit_path = source / "audit.json"
    if not signal_path.is_file():
        raise FileNotFoundError(signal_path)
    if not audit_path.is_file():
        raise FileNotFoundError(audit_path)
    if not eligibility_source.is_file():
        raise FileNotFoundError(eligibility_source)
    signals = pd.read_csv(signal_path, dtype={"hypothesis_id": str})
    signal_audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if not isinstance(signal_audit, dict):
        raise TypeError("validated signal audit must be a JSON object")
    eligibility = pd.read_csv(eligibility_source)
    return build_validated_portfolio_intents(
        signals,
        signal_audit,
        eligibility,
        decision_time=decision_time,
        equity_eur=equity_eur,
        current_weights=current_weights,
        policy=policy,
    )


__all__ = [
    "SCHEMA",
    "DecisionGatewayPolicy",
    "ValidatedDecisionBundle",
    "build_validated_portfolio_intents",
    "build_validated_portfolio_intents_from_project",
]
