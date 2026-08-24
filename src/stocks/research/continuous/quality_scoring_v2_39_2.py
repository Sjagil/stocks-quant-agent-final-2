from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from .evidence_taxonomy_v2_39_2 import (
    CALIBRATION, COST_ROBUSTNESS, OOS_VALIDATION, evidence_class,
)


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


def _records(records: list[dict], cls: str) -> list[dict]:
    return [r for r in records if evidence_class(r.get("evidence_type", "")) == cls]


def _sample_count(record: dict) -> int:
    metrics = record.get("metrics", {})
    candidates = [record.get("sample_count")]
    for key in ("observations", "n_obs", "n", "trades", "trade_count", "sample_count", "test_observations", "test_trades"):
        candidates.append(metrics.get(key))
    values = [int(float(x)) for x in candidates if _num(x) is not None and float(x) >= 0]
    return max(values, default=0)


def _metric_quality(records: list[dict]) -> float:
    vals: list[float] = []
    for r in records:
        m = r.get("metrics", {})
        for key in ("quality_score", "validation_score", "robustness_score", "wfe", "psr", "probabilistic_sharpe_ratio"):
            n = _num(m.get(key))
            if n is None:
                continue
            if 1 < abs(n) <= 100:
                n /= 100.0
            vals.append(max(0.0, min(1.0, n)))
            break
    if vals:
        return sum(vals) / len(vals)
    return 0.5 if records else 0.0


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
class QualityScoreV2392:
    total: float
    components: dict[str, float]
    penalty: float
    diagnostics: dict[str, float | int | bool]

    def as_dict(self):
        return asdict(self)


def quality_score_v2392(
    *,
    latest_registry: dict,
    records: list[dict],
    shadow_trades: int,
    posterior_net_edge_bps: float | None,
    breadth,
    weights: dict,
    policy: dict,
    drift_severity: float,
    decay_severity: float,
    disagreement: float,
) -> QualityScoreV2392:
    val = str(latest_registry.get("validation_status") or "").upper()
    validation = 1.0 if val == "VALIDATED" else (0.55 if val == "PROVISIONAL" else 0.0)
    cross = 1.0 if _truthy(latest_registry.get("cross_engine_validated")) else 0.0
    generalization = 1.0 if _truthy(latest_registry.get("dynamic_universe_generalized")) else 0.0

    min_oos = max(1, int(policy.get("minimum_oos_observations", 60)))
    oos_records = _records(records, OOS_VALIDATION)
    # Conservative: correlated rows from the same upstream artifact are not summed.
    oos_observations = max((_sample_count(r) for r in oos_records), default=0)
    oos_coverage = min(1.0, oos_observations / min_oos)
    oos_positive = any(_positive(r) for r in oos_records)
    oos_metric = _metric_quality(oos_records)
    oos_score = oos_coverage * ((0.60 if oos_positive else 0.0) + 0.40 * oos_metric)
    oos_score = max(0.0, min(1.0, oos_score))

    min_cost_multiplier = max(1e-9, float(policy.get("minimum_cost_stress_multiplier", 2.0)))
    cost_records = _records(records, COST_ROBUSTNESS)
    positive_multipliers: list[float] = []
    for r in cost_records:
        if not _positive(r):
            continue
        multiplier = _num(r.get("metrics", {}).get("stress_multiplier"))
        positive_multipliers.append(multiplier if multiplier is not None else 1.0)
    max_positive_cost_multiplier = max(positive_multipliers, default=0.0)
    cost_coverage = min(1.0, max_positive_cost_multiplier / min_cost_multiplier)
    cost_metric = _metric_quality(cost_records)
    cost_score = cost_coverage * (0.65 + 0.35 * cost_metric) if positive_multipliers else 0.0
    cost_score = max(0.0, min(1.0, cost_score))

    min_shadow = max(1, int(policy.get("minimum_shadow_trades_for_promotion_review", 30)))
    shadow_coverage = min(1.0, shadow_trades / min_shadow)
    posterior_strength = 0.0
    if posterior_net_edge_bps is not None and posterior_net_edge_bps > 0:
        posterior_strength = max(0.0, min(1.0, float(posterior_net_edge_bps) / 20.0))
    shadow_score = 0.60 * shadow_coverage + 0.40 * posterior_strength

    calibration_records = _records(records, CALIBRATION)
    calibration = _metric_quality(calibration_records)

    class_target = max(1, int(policy.get("minimum_independent_evidence_classes", 2)))
    source_target = max(1, int(policy.get("minimum_independent_evidence_sources", 2)))
    breadth_score = (
        0.5 * min(1.0, len(breadth.promotion_classes) / class_target)
        + 0.5 * min(1.0, len(breadth.promotion_sources) / source_target)
    )
    freshness = 1.0 if breadth.fresh_decision_classes else 0.0

    components = {
        "statistical_validation": validation,
        "oos_robustness": oos_score,
        "cost_robustness": cost_score,
        "shadow_evidence": shadow_score,
        "cross_engine": cross,
        "generalization": generalization,
        "calibration": calibration,
        "evidence_breadth": breadth_score,
        "freshness": freshness,
    }
    defaults = {
        "statistical_validation": 0.15,
        "oos_robustness": 0.15,
        "cost_robustness": 0.15,
        "shadow_evidence": 0.15,
        "cross_engine": 0.10,
        "generalization": 0.10,
        "calibration": 0.05,
        "evidence_breadth": 0.10,
        "freshness": 0.05,
    }
    ww = {k: float(weights.get(k, v)) for k, v in defaults.items()}
    total_weight = sum(ww.values()) or 1.0
    base = sum(components[k] * ww[k] for k in components) / total_weight
    penalty = min(
        0.45,
        0.15 * max(0.0, min(1.0, drift_severity))
        + 0.15 * max(0.0, min(1.0, decay_severity))
        + 0.10 * max(0.0, min(1.0, disagreement)),
    )
    diagnostics = {
        "oos_observations": int(oos_observations),
        "minimum_oos_observations": int(min_oos),
        "oos_positive": bool(oos_positive),
        "max_positive_cost_stress_multiplier": float(max_positive_cost_multiplier),
        "minimum_cost_stress_multiplier": float(min_cost_multiplier),
        "shadow_trades": int(shadow_trades),
        "minimum_shadow_trades": int(min_shadow),
    }
    return QualityScoreV2392(
        float(max(0.0, min(1.0, base - penalty))),
        {k: float(v) for k, v in components.items()},
        float(penalty),
        diagnostics,
    )


__all__ = ["QualityScoreV2392", "quality_score_v2392"]
