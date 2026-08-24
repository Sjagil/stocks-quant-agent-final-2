from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable

from .store_v2_39 import parse_utc

UPSTREAM_METADATA = "UPSTREAM_METADATA"
STATISTICAL_VALIDATION = "STATISTICAL_VALIDATION"
OOS_VALIDATION = "OOS_VALIDATION"
COST_ROBUSTNESS = "COST_ROBUSTNESS"
SHADOW_OUTCOME = "SHADOW_OUTCOME"
CALIBRATION = "CALIBRATION"
CROSS_ENGINE = "CROSS_ENGINE"
GENERALIZATION = "GENERALIZATION"
DRIFT_MONITOR = "DRIFT_MONITOR"
OTHER = "OTHER"

_METADATA_TYPES = {"REGISTRY_SNAPSHOT", "CANDIDATE_REGISTRY", "UPSTREAM_METADATA"}
_OOS_TYPES = {
    "OOS", "OOS_VALIDATION", "PURGED_WALK_FORWARD", "WALK_FORWARD", "HOLDOUT",
    "HOLDOUT_VALIDATION", "RL_OOS", "FORWARD_VALIDATION",
}
_COST_TYPES = {"COST_STRESS", "EXECUTION_COST_STRESS", "COST_ROBUSTNESS", "IMPLEMENTATION_SHORTFALL_STRESS"}
_SHADOW_TYPES = {"SHADOW_TRADE", "SHADOW_OUTCOME", "FORWARD_SHADOW"}
_CAL_TYPES = {"FORECAST_CALIBRATION", "COST_CALIBRATION", "CALIBRATION"}
_CROSS_TYPES = {"CROSS_ENGINE", "CROSS_ENGINE_RESULT", "CROSS_ENGINE_VALIDATION"}
_GEN_TYPES = {"GENERALIZATION", "GENERALIZATION_RESULT", "DYNAMIC_UNIVERSE_GENERALIZATION"}
_STAT_TYPES = {"STATISTICAL_VALIDATION", "V233_VALIDATION", "ANTI_OVERFIT_VALIDATION"}
_DRIFT_TYPES = {"DRIFT", "FEATURE_DRIFT", "MODEL_DRIFT"}

# Broad research independence: useful for diagnostics and disagreement analysis.
INDEPENDENT_OUTCOME_CLASSES = {
    STATISTICAL_VALIDATION, OOS_VALIDATION, COST_ROBUSTNESS, SHADOW_OUTCOME,
    CALIBRATION, CROSS_ENGINE, GENERALIZATION,
}

# Promotion-grade evidence excludes cross-engine/generalization because those are
# already explicit foundation gates. Counting them again as evidence breadth would
# double-count the same upstream facts.
PROMOTION_EVIDENCE_CLASSES = {
    STATISTICAL_VALIDATION, OOS_VALIDATION, COST_ROBUSTNESS, SHADOW_OUTCOME, CALIBRATION,
}

# Freshness for champion review must come from evidence that can change economic
# confidence today. Static cross-engine/generalization metadata cannot satisfy it.
FRESH_DECISION_CLASSES = {OOS_VALIDATION, COST_ROBUSTNESS, SHADOW_OUTCOME, CALIBRATION}


def evidence_class(evidence_type: str) -> str:
    t = str(evidence_type or "").strip().upper()
    if t in _METADATA_TYPES:
        return UPSTREAM_METADATA
    if t in _OOS_TYPES:
        return OOS_VALIDATION
    if t in _COST_TYPES:
        return COST_ROBUSTNESS
    if t in _SHADOW_TYPES:
        return SHADOW_OUTCOME
    if t in _CAL_TYPES:
        return CALIBRATION
    if t in _CROSS_TYPES:
        return CROSS_ENGINE
    if t in _GEN_TYPES:
        return GENERALIZATION
    if t in _STAT_TYPES:
        return STATISTICAL_VALIDATION
    if t in _DRIFT_TYPES:
        return DRIFT_MONITOR
    return OTHER



def promotion_grade_record(record: dict) -> bool:
    # Backward compatible: legacy evidence without explicit qualification
    # remains eligible; explicit failed/insufficient evidence does not.
    metrics = record.get("metrics", {}) or {}

    if "passed" in metrics:
        value = metrics.get("passed")
        if isinstance(value, bool):
            passed = value
        else:
            passed = str(value).strip().lower() in {
                "1", "true", "yes", "y", "pass", "passed", "validated", "accept",
            }
        if not passed:
            return False

    status = str(metrics.get("status") or "").strip().upper()
    if (
        status in {
            "INSUFFICIENT", "BLOCKED", "FAILED", "FAIL",
            "REJECT", "REJECTED", "NOT_EVALUABLE",
        }
        or status.startswith("NOT_EVALUABLE_")
    ):
        return False

    return True

def source_group(record: dict) -> str:
    source = str(record.get("source") or "").strip().lower()
    for marker, group in (
        ("v2.37", "shadow_v237"), ("shadow", "shadow_v237"),
        ("v2.36", "execution_v236"), ("execution", "execution_v236"),
        ("v2.33", "stat_validation_v233"), ("statistical", "stat_validation_v233"),
        ("validated_strategy_registry", "stat_validation_registry"),
        ("strategy_generation_validation", "strategy_generation_validation"),
        ("walk", "oos_validation"), ("holdout", "oos_validation"),
        ("lean", "cross_engine"), ("nautilus", "cross_engine"),
        ("pybroker", "cross_engine"), ("cross_engine", "cross_engine"),
        ("generalization", "generalization"), ("dynamic_universe", "generalization"),
        ("v2.38", "rl_v238"), ("rl", "rl_v238"),
        ("forecast", "forecast"), ("calibration", "calibration"),
        ("research_candidate_registry", "registry_metadata"), ("registry", "registry_metadata"),
    ):
        if marker in source:
            return group
    return source or "unknown"


@dataclass(frozen=True)
class EvidenceBreadthV2392:
    independent_classes: tuple[str, ...]
    independent_sources: tuple[str, ...]
    promotion_classes: tuple[str, ...]
    promotion_sources: tuple[str, ...]
    fresh_outcome_classes: tuple[str, ...]
    fresh_decision_classes: tuple[str, ...]
    latest_outcome_time: str | None
    latest_decision_time: str | None

    def as_dict(self) -> dict:
        return asdict(self)


def evidence_breadth_v2392(
    records: Iterable[dict],
    *,
    fresh_hours: float = 720.0,
    now: datetime | None = None,
) -> EvidenceBreadthV2392:
    now = now or datetime.now(timezone.utc)
    classes: set[str] = set()
    sources: set[str] = set()
    promotion_classes: set[str] = set()
    promotion_sources: set[str] = set()
    fresh_outcome: set[str] = set()
    fresh_decision: set[str] = set()
    latest_outcome = None
    latest_decision = None

    for record in records:
        cls = evidence_class(record.get("evidence_type", ""))
        if cls not in INDEPENDENT_OUTCOME_CLASSES:
            continue
        group = source_group(record)
        classes.add(cls)
        sources.add(group)
        promotion_grade = promotion_grade_record(record)
        if cls in PROMOTION_EVIDENCE_CLASSES and promotion_grade:
            promotion_classes.add(cls)
            promotion_sources.add(group)

        dt = parse_utc(record.get("as_of"))
        if dt is not None:
            if latest_outcome is None or dt > latest_outcome:
                latest_outcome = dt
            is_fresh = (now - dt).total_seconds() <= float(fresh_hours) * 3600
            if promotion_grade and is_fresh:
                fresh_outcome.add(cls)
            if promotion_grade and cls in FRESH_DECISION_CLASSES:
                if latest_decision is None or dt > latest_decision:
                    latest_decision = dt
                if is_fresh:
                    fresh_decision.add(cls)

    return EvidenceBreadthV2392(
        tuple(sorted(classes)),
        tuple(sorted(sources)),
        tuple(sorted(promotion_classes)),
        tuple(sorted(promotion_sources)),
        tuple(sorted(fresh_outcome)),
        tuple(sorted(fresh_decision)),
        latest_outcome.isoformat() if latest_outcome else None,
        latest_decision.isoformat() if latest_decision else None,
    )


__all__ = [
    "UPSTREAM_METADATA", "STATISTICAL_VALIDATION", "OOS_VALIDATION", "COST_ROBUSTNESS",
    "SHADOW_OUTCOME", "CALIBRATION", "CROSS_ENGINE", "GENERALIZATION", "DRIFT_MONITOR",
    "OTHER", "INDEPENDENT_OUTCOME_CLASSES", "PROMOTION_EVIDENCE_CLASSES",
    "FRESH_DECISION_CLASSES", "EvidenceBreadthV2392", "evidence_class", "source_group",
    "promotion_grade_record", "evidence_breadth_v2392",
]
