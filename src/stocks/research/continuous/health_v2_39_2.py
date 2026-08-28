from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math

from .bayesian_shrinkage_v2_39 import shrink_mean
from .champion_gate_v2_39_2 import evaluate_champion_gate_v2392
from .contracts_v2_39 import ResearchHealth
from .disagreement_v2_39 import robust_disagreement
from .drift_decay_v2_39 import performance_decay
from .evidence_taxonomy_v2_39_2 import evidence_breadth_v2392
from .quality_scoring_v2_39_2 import quality_score_v2392
from .store_v2_39 import ResearchStoreV239, parse_utc


def _num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


@dataclass(frozen=True)
class HardenedAssessmentV2392:
    entity_id: str
    health: str
    recommendation: str
    score: float
    promotion_readiness_score: float
    positive_reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    posterior_net_edge_bps: float | None
    shadow_trades: int
    independent_sources: int
    independent_classes: int
    promotion_sources: int
    promotion_classes: int
    fresh_decision_classes: tuple[str, ...]
    drift_severity: float
    decay_severity: float
    disagreement: float
    quality_components: dict[str, float]
    quality_diagnostics: dict[str, float | int | bool]
    gate_passed: bool
    execution_authority: str = "NONE"

    @property
    def reasons(self):
        return self.positive_reasons + self.blockers + self.warnings + self.missing_requirements

    def as_dict(self):
        d = asdict(self)
        d["quality_score"] = self.score
        d["reasons"] = self.reasons
        return d


def assess_entity_hardened_v2392(
    store: ResearchStoreV239,
    entity_id: str,
    *,
    policy: dict,
    bayesian: dict,
    quality_weights: dict,
) -> HardenedAssessmentV2392:
    ent = store.get_entity(entity_id)
    if ent is None:
        raise KeyError(entity_id)
    if ent["role"] == "RETIRED":
        return HardenedAssessmentV2392(
            entity_id, "RETIRED", "HOLD_RETIRED", 0.0, 0.0, (), ("MANUALLY_RETIRED",), (), (),
            None, 0, 0, 0, 0, 0, (), 0.0, 0.0, 0.0, {}, {}, False,
        )

    evidence = store.evidence_for(entity_id)
    registry = [x for x in evidence if x["evidence_type"] == "REGISTRY_SNAPSHOT"]
    latest_registry = registry[-1]["metrics"] if registry else {}
    validation_status = str(latest_registry.get("validation_status") or "").upper()
    promotion_stage = str(latest_registry.get("promotion_stage") or "").upper()

    shadow = [x for x in evidence if x["evidence_type"] == "SHADOW_TRADE"]
    shadow_returns = [_num(x["metrics"].get("realized_net_return_bps")) for x in shadow]
    shadow_returns = [x for x in shadow_returns if x is not None]
    shrink = shrink_mean(
        shadow_returns,
        prior_mean=float(bayesian.get("prior_mean_bps", 0.0)),
        prior_strength=float(bayesian.get("prior_strength", 20.0)),
    )
    decay = performance_decay(shadow_returns)

    drift_records = [x for x in evidence if x["evidence_type"] == "DRIFT"]
    psi = max([_num(x["metrics"].get("psi_max")) or 0.0 for x in drift_records], default=0.0)
    js = max([_num(x["metrics"].get("js_max")) or 0.0 for x in drift_records], default=0.0)
    drift_severity = max(
        min(1.0, psi / max(float(policy.get("psi_quarantine", 0.25)), 1e-12)),
        min(1.0, js / max(float(policy.get("js_quarantine", 0.20)), 1e-12)),
    )

    scores: list[float] = []
    for record in evidence:
        if record["evidence_type"] == "REGISTRY_SNAPSHOT":
            continue
        for key in ("quality_score", "validation_score", "score"):
            n = _num(record["metrics"].get(key))
            if n is not None:
                scores.append(n / 100.0 if 1 < abs(n) <= 100 else n)
                break
    disagreement = robust_disagreement(scores)

    warnings: list[str] = []
    severe: list[str] = []
    latest = store.latest_evidence_time(entity_id)
    stale = True
    if latest:
        age_hours = (datetime.now(timezone.utc) - parse_utc(latest)).total_seconds() / 3600.0
        stale = age_hours > float(policy.get("stale_evidence_hours", 168))
    if stale:
        warnings.append("EVIDENCE_STALE")

    if validation_status == "REJECTED":
        severe.append("UPSTREAM_VALIDATION_REJECTED")
    if promotion_stage.startswith("REJECTED"):
        severe.append("UPSTREAM_PROMOTION_REJECTED")
    if psi >= float(policy.get("psi_quarantine", 0.25)) or js >= float(policy.get("js_quarantine", 0.20)):
        severe.append("SEVERE_DRIFT")
    elif psi >= float(policy.get("psi_watch", 0.10)) or js >= float(policy.get("js_watch", 0.08)):
        warnings.append("DRIFT_WATCH")
    if decay.severity >= float(policy.get("decay_quarantine", 0.70)):
        severe.append("SEVERE_PERFORMANCE_DECAY")
    elif decay.severity >= float(policy.get("decay_watch", 0.35)):
        warnings.append("PERFORMANCE_DECAY_WATCH")
    if disagreement >= float(policy.get("disagreement_quarantine", 0.75)):
        severe.append("SEVERE_ENSEMBLE_DISAGREEMENT")
    elif disagreement >= float(policy.get("disagreement_watch", 0.45)):
        warnings.append("ENSEMBLE_DISAGREEMENT_WATCH")
    if shadow_returns and shrink.posterior_mean < float(policy.get("minimum_posterior_net_edge_bps", 0.0)):
        severe.append("POSTERIOR_NET_EDGE_NEGATIVE")

    breadth = evidence_breadth_v2392(
        evidence,
        fresh_hours=float(policy.get("promotion_evidence_fresh_hours", 720)),
    )
    posterior = None if shrink.observations == 0 else shrink.posterior_mean
    quality = quality_score_v2392(
        latest_registry=latest_registry,
        records=evidence,
        shadow_trades=len(shadow_returns),
        posterior_net_edge_bps=posterior,
        breadth=breadth,
        weights=quality_weights,
        policy=policy,
        drift_severity=drift_severity,
        decay_severity=decay.severity,
        disagreement=disagreement,
    )
    gate = evaluate_champion_gate_v2392(
        latest_registry=latest_registry,
        records=evidence,
        breadth=breadth,
        shadow_trades=len(shadow_returns),
        posterior_net_edge_bps=posterior,
        quality_score=quality.total,
        policy=policy,
        severe_reasons=set(severe),
    )

    if severe:
        health = ResearchHealth.QUARANTINED.value
    elif warnings:
        health = ResearchHealth.WATCH.value
    elif not evidence:
        health = ResearchHealth.NEW.value
    else:
        health = ResearchHealth.HEALTHY.value

    role = ent["role"]
    if role == "CHAMPION":
        recommendation = (
            "RECOMMEND_DEACTIVATE" if health == "QUARANTINED"
            else "RECOMMEND_REVALIDATE" if health == "WATCH"
            else "HOLD_CHAMPION"
        )
    elif health == "QUARANTINED":
        recommendation = (
            "RECOMMEND_RETIRE_REVIEW"
            if {"UPSTREAM_VALIDATION_REJECTED", "UPSTREAM_PROMOTION_REJECTED"}.intersection(severe)
            else "REJECT_OR_REWORK"
        )
    elif health == "WATCH":
        recommendation = "REVALIDATE"
    elif gate.passed:
        recommendation = "RECOMMEND_CHAMPION_REVIEW"
    else:
        recommendation = "ACCUMULATE_EVIDENCE"

    return HardenedAssessmentV2392(
        entity_id=entity_id,
        health=health,
        recommendation=recommendation,
        score=quality.total,
        promotion_readiness_score=gate.readiness_score,
        positive_reasons=gate.positive_reasons,
        blockers=tuple(dict.fromkeys(severe + list(gate.blockers))),
        warnings=tuple(dict.fromkeys(warnings)),
        missing_requirements=gate.missing_requirements,
        posterior_net_edge_bps=posterior,
        shadow_trades=len(shadow_returns),
        independent_sources=len(breadth.independent_sources),
        independent_classes=len(breadth.independent_classes),
        promotion_sources=len(breadth.promotion_sources),
        promotion_classes=len(breadth.promotion_classes),
        fresh_decision_classes=tuple(breadth.fresh_decision_classes),
        drift_severity=drift_severity,
        decay_severity=decay.severity,
        disagreement=disagreement,
        quality_components=quality.components,
        quality_diagnostics=quality.diagnostics,
        gate_passed=gate.passed,
    )


__all__ = ["HardenedAssessmentV2392", "assess_entity_hardened_v2392"]
