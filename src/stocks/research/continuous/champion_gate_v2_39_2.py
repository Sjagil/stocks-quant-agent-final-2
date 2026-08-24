from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from .evidence_taxonomy_v2_39_2 import COST_ROBUSTNESS, OOS_VALIDATION, evidence_class


def _num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def _truthy(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"1", "true", "yes", "y", "pass", "passed", "validated"}


def _sample_count(record: dict) -> int:
    m = record.get("metrics", {})
    vals = [record.get("sample_count")]
    for key in ("observations", "n_obs", "n", "trades", "trade_count", "sample_count", "test_observations", "test_trades"):
        vals.append(m.get(key))
    numbers = [int(float(x)) for x in vals if _num(x) is not None and float(x) >= 0]
    return max(numbers, default=0)


def _positive(record: dict) -> bool:
    m = record.get("metrics", {})
    for key in (
        "net_edge_bps", "mean_net_edge_bps", "median_test_expectancy_bps", "expectancy_bps",
        "realized_net_return_bps", "median_stress_test_expectancy_bps",
    ):
        n = _num(m.get(key))
        if n is not None:
            return n > 0
    n = _num(m.get("net_return"))
    if n is not None:
        return n > 0
    return _truthy(m.get("passed")) or str(m.get("status", "")).upper() in {"PASS", "PASSED", "VALIDATED", "ACCEPT"}


@dataclass(frozen=True)
class ChampionGateV2392:
    passed: bool
    readiness_score: float
    positive_reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    promotion_classes: tuple[str, ...]
    promotion_sources: tuple[str, ...]
    fresh_decision_classes: tuple[str, ...]
    oos_observations: int
    shadow_trades: int
    cost_stress_max_positive_multiplier: float
    quality_score: float

    def as_dict(self):
        return asdict(self)


def evaluate_champion_gate_v2392(
    *,
    latest_registry: dict,
    records: list[dict],
    breadth,
    shadow_trades: int,
    posterior_net_edge_bps: float | None,
    quality_score: float,
    policy: dict,
    severe_reasons: set[str] | None = None,
) -> ChampionGateV2392:
    severe_reasons = set(severe_reasons or set())
    positive: list[str] = []
    blockers: list[str] = []
    missing: list[str] = []
    criteria: list[bool] = []

    validation_status = str(latest_registry.get("validation_status") or "").upper()
    promotion_stage = str(latest_registry.get("promotion_stage") or "").upper()
    cross = _truthy(latest_registry.get("cross_engine_validated"))
    generalized = _truthy(latest_registry.get("dynamic_universe_generalized"))

    validation_ok = validation_status == "VALIDATED"
    criteria.append(validation_ok)
    if validation_ok:
        positive.append("VALIDATION_STATUS_VALIDATED")
    else:
        missing.append("NEED_VALIDATION_STATUS_VALIDATED")

    criteria.append(cross)
    if cross:
        positive.append("CROSS_ENGINE_VALIDATED")
    else:
        missing.append("NEED_CROSS_ENGINE_VALIDATION")

    criteria.append(generalized)
    if generalized:
        positive.append("DYNAMIC_UNIVERSE_GENERALIZED")
    else:
        missing.append("NEED_DYNAMIC_UNIVERSE_GENERALIZATION")

    if validation_status == "REJECTED":
        blockers.append("UPSTREAM_VALIDATION_REJECTED")
    if promotion_stage.startswith("REJECTED"):
        blockers.append("UPSTREAM_PROMOTION_REJECTED")

    min_classes = int(policy.get("minimum_independent_evidence_classes", 2))
    min_sources = int(policy.get("minimum_independent_evidence_sources", 2))
    classes_ok = len(breadth.promotion_classes) >= min_classes
    sources_ok = len(breadth.promotion_sources) >= min_sources
    criteria.extend([classes_ok, sources_ok])
    if classes_ok:
        positive.append("PROMOTION_EVIDENCE_CLASS_BREADTH_SUFFICIENT")
    else:
        missing.append(f"NEED_{min_classes}_PROMOTION_EVIDENCE_CLASSES")
    if sources_ok:
        positive.append("PROMOTION_EVIDENCE_SOURCE_INDEPENDENCE_SUFFICIENT")
    else:
        missing.append(f"NEED_{min_sources}_PROMOTION_EVIDENCE_SOURCES")

    freshness_required = bool(policy.get("require_fresh_outcome_evidence", True))
    fresh_ok = bool(breadth.fresh_decision_classes) or not freshness_required
    criteria.append(fresh_ok)
    if breadth.fresh_decision_classes:
        positive.append("FRESH_DECISION_EVIDENCE_PRESENT")
    elif freshness_required:
        missing.append("NEED_FRESH_DECISION_EVIDENCE")

    oos_records = [r for r in records if evidence_class(r.get("evidence_type", "")) == OOS_VALIDATION]
    # Conservative maximum avoids double-counting duplicated/correlated artifact rows.
    oos_observations = max((_sample_count(r) for r in oos_records), default=0)
    min_oos = int(policy.get("minimum_oos_observations", 60))
    oos_ok = oos_observations >= min_oos and any(_positive(r) for r in oos_records)
    if oos_ok:
        positive.append("OOS_EVIDENCE_SUFFICIENT")

    min_shadow = int(policy.get("minimum_shadow_trades_for_promotion_review", 30))
    shadow_ok = (
        shadow_trades >= min_shadow
        and posterior_net_edge_bps is not None
        and posterior_net_edge_bps > float(policy.get("minimum_posterior_net_edge_bps", 0.0))
    )
    if shadow_ok:
        positive.extend(["SHADOW_SAMPLE_SUFFICIENT", "POSTERIOR_NET_EDGE_POSITIVE"])
    performance_ok = oos_ok or shadow_ok
    criteria.append(performance_ok)
    if not performance_ok:
        missing.append("NEED_POSITIVE_OOS_OR_SHADOW_EVIDENCE")

    cost_records = [r for r in records if evidence_class(r.get("evidence_type", "")) == COST_ROBUSTNESS]
    min_multiplier = float(policy.get("minimum_cost_stress_multiplier", 2.0))
    positive_multipliers: list[float] = []
    for r in cost_records:
        if not _positive(r):
            continue
        mult = _num(r.get("metrics", {}).get("stress_multiplier"))
        positive_multipliers.append(mult if mult is not None else 1.0)
    max_positive_multiplier = max(positive_multipliers, default=0.0)
    cost_required = bool(policy.get("require_cost_robustness_for_champion_review", True))
    cost_ok = max_positive_multiplier >= min_multiplier or not cost_required
    criteria.append(cost_ok)
    if max_positive_multiplier >= min_multiplier:
        positive.append("COST_STRESS_PASS")
    elif cost_required:
        missing.append(f"NEED_POSITIVE_COST_STRESS_{min_multiplier:g}X")

    quality_min = float(policy.get("minimum_quality_score_for_champion_review", 0.72))
    quality_ok = quality_score >= quality_min
    criteria.append(quality_ok)
    if quality_ok:
        positive.append("QUALITY_SCORE_SUFFICIENT")
    else:
        missing.append(f"NEED_QUALITY_SCORE_{quality_min:.2f}")

    blockers.extend(sorted(severe_reasons))
    no_blockers = not blockers
    criteria.append(no_blockers)
    readiness = sum(bool(x) for x in criteria) / max(1, len(criteria))
    passed = no_blockers and not missing
    if passed:
        positive.append("CHAMPION_REVIEW_GATE_PASS")

    return ChampionGateV2392(
        bool(passed),
        float(readiness),
        tuple(dict.fromkeys(positive)),
        tuple(dict.fromkeys(blockers)),
        tuple(dict.fromkeys(missing)),
        tuple(breadth.promotion_classes),
        tuple(breadth.promotion_sources),
        tuple(breadth.fresh_decision_classes),
        int(oos_observations),
        int(shadow_trades),
        float(max_positive_multiplier),
        float(quality_score),
    )


__all__ = ["ChampionGateV2392", "evaluate_champion_gate_v2392"]
