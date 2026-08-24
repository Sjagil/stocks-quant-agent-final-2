from datetime import datetime, timezone

from stocks.research.continuous.champion_gate_v2_39_2 import evaluate_champion_gate_v2392
from stocks.research.continuous.evidence_taxonomy_v2_39_2 import (
    COST_ROBUSTNESS,
    OOS_VALIDATION,
    STATISTICAL_VALIDATION,
    evidence_breadth_v2392,
    promotion_grade_record,
)
from stocks.research.continuous.quality_scoring_v2_39_2 import quality_score_v2392


def _record(evidence_type, source, metrics, *, sample_count=0, as_of="2026-08-25T00:00:00+00:00"):
    return {
        "evidence_type": evidence_type,
        "source": source,
        "metrics": dict(metrics),
        "sample_count": sample_count,
        "as_of": as_of,
    }


def _policy():
    return {
        "minimum_oos_observations": 60,
        "minimum_cost_stress_multiplier": 2.0,
        "minimum_shadow_trades_for_promotion_review": 30,
        "minimum_independent_evidence_classes": 2,
        "minimum_independent_evidence_sources": 2,
        "minimum_quality_score_for_champion_review": 0.72,
        "minimum_posterior_net_edge_bps": 0.0,
        "require_cost_robustness_for_champion_review": True,
        "require_fresh_outcome_evidence": True,
    }


def _registry():
    return {
        "validation_status": "VALIDATED",
        "cross_engine_validated": True,
        "dynamic_universe_generalized": True,
    }


def test_insufficient_positive_rows_do_not_receive_promotion_credit():
    records = [
        _record(
            "V233_VALIDATION",
            "statistical_validation_v2.33",
            {"passed": True, "psr": 0.97},
            sample_count=100,
        ),
        _record(
            "PURGED_WALK_FORWARD",
            "purged_walk_forward_v2.39.3",
            {
                "status": "INSUFFICIENT",
                "passed": False,
                "observations": 11,
                "net_edge_bps": 212.87,
                "profit_factor": 2.92,
            },
            sample_count=11,
        ),
        _record(
            "EXECUTION_COST_STRESS",
            "v2.36_practical_cost_stress_v2.39.3",
            {
                "passed": False,
                "positive": True,
                "stress_multiplier": 3.0,
                "expectancy_bps": 200.0,
                "effective_observations": 11,
            },
            sample_count=11,
        ),
    ]

    assert promotion_grade_record(records[1]) is False
    assert promotion_grade_record(records[2]) is False

    breadth = evidence_breadth_v2392(
        records,
        fresh_hours=720.0,
        now=datetime(2026, 8, 25, 1, 0, tzinfo=timezone.utc),
    )
    assert breadth.promotion_classes == (STATISTICAL_VALIDATION,)
    assert OOS_VALIDATION not in breadth.promotion_classes
    assert COST_ROBUSTNESS not in breadth.promotion_classes
    assert breadth.fresh_decision_classes == ()

    quality = quality_score_v2392(
        latest_registry=_registry(),
        records=records,
        shadow_trades=0,
        posterior_net_edge_bps=None,
        breadth=breadth,
        weights={},
        policy=_policy(),
        drift_severity=0.0,
        decay_severity=0.0,
        disagreement=0.0,
    )
    assert quality.diagnostics["oos_observations"] == 11
    assert quality.diagnostics["oos_positive"] is False
    assert quality.diagnostics["max_positive_cost_stress_multiplier"] == 0.0
    assert quality.components["oos_robustness"] == 0.0
    assert quality.components["cost_robustness"] == 0.0

    gate = evaluate_champion_gate_v2392(
        latest_registry=_registry(),
        records=records,
        breadth=breadth,
        shadow_trades=0,
        posterior_net_edge_bps=None,
        quality_score=quality.total,
        policy=_policy(),
        severe_reasons=set(),
    )
    assert "COST_STRESS_PASS" not in gate.positive_reasons
    assert "NEED_POSITIVE_COST_STRESS_2X" in gate.missing_requirements
    assert "NEED_POSITIVE_OOS_OR_SHADOW_EVIDENCE" in gate.missing_requirements
    assert gate.passed is False


def test_legacy_positive_rows_without_explicit_pass_remain_compatible():
    records = [
        _record(
            "PURGED_WALK_FORWARD",
            "walkforward_legacy",
            {"observations": 80, "net_edge_bps": 25.0},
            sample_count=80,
        ),
        _record(
            "EXECUTION_COST_STRESS",
            "v2.36_execution",
            {"stress_multiplier": 2.0, "expectancy_bps": 8.0},
            sample_count=80,
        ),
    ]
    assert all(promotion_grade_record(r) for r in records)

    breadth = evidence_breadth_v2392(
        records,
        fresh_hours=720.0,
        now=datetime(2026, 8, 25, 1, 0, tzinfo=timezone.utc),
    )
    assert OOS_VALIDATION in breadth.promotion_classes
    assert COST_ROBUSTNESS in breadth.promotion_classes
    assert OOS_VALIDATION in breadth.fresh_decision_classes
    assert COST_ROBUSTNESS in breadth.fresh_decision_classes

    quality = quality_score_v2392(
        latest_registry=_registry(),
        records=records,
        shadow_trades=0,
        posterior_net_edge_bps=None,
        breadth=breadth,
        weights={},
        policy=_policy(),
        drift_severity=0.0,
        decay_severity=0.0,
        disagreement=0.0,
    )
    assert quality.diagnostics["oos_positive"] is True
    assert quality.diagnostics["max_positive_cost_stress_multiplier"] == 2.0
