from datetime import datetime, timezone

from stocks.research.continuous.champion_gate_v2_39_2 import evaluate_champion_gate_v2392
from stocks.research.continuous.evidence_taxonomy_v2_39_2 import evidence_breadth_v2392

NOW = datetime(2026, 8, 24, 18, 0, tzinfo=timezone.utc)
POLICY = {"minimum_independent_evidence_classes": 2, "minimum_independent_evidence_sources": 2, "minimum_oos_observations": 60, "minimum_shadow_trades_for_promotion_review": 30, "minimum_posterior_net_edge_bps": 0, "minimum_cost_stress_multiplier": 2.0, "require_cost_robustness_for_champion_review": True, "require_fresh_outcome_evidence": True, "minimum_quality_score_for_champion_review": .72}


def gate(reg, records, q=.8):
    b = evidence_breadth_v2392(records, now=NOW)
    return evaluate_champion_gate_v2392(latest_registry=reg, records=records, breadth=b, shadow_trades=0, posterior_net_edge_bps=None, quality_score=q, policy=POLICY, severe_reasons=set())


def test_cross_generalization_alone_cannot_satisfy_breadth_or_freshness():
    reg = {"validation_status": "VALIDATED", "promotion_stage": "CHALLENGER", "cross_engine_validated": True, "dynamic_universe_generalized": True}
    records = [
        {"evidence_type": "CROSS_ENGINE_RESULT", "source": "cross_engine", "as_of": NOW.isoformat(), "metrics": {"passed": True}},
        {"evidence_type": "GENERALIZATION_RESULT", "source": "generalization", "as_of": NOW.isoformat(), "metrics": {"passed": True}},
    ]
    g = gate(reg, records)
    assert not g.passed
    assert "NEED_2_PROMOTION_EVIDENCE_CLASSES" in g.missing_requirements
    assert "NEED_2_PROMOTION_EVIDENCE_SOURCES" in g.missing_requirements
    assert "NEED_FRESH_DECISION_EVIDENCE" in g.missing_requirements


def test_diagnostic_oos_and_one_x_cost_do_not_pass():
    reg = {"validation_status": "VALIDATED", "promotion_stage": "CHALLENGER", "cross_engine_validated": True, "dynamic_universe_generalized": True}
    records = [
        {"evidence_type": "STATISTICAL_VALIDATION", "source": "validated_strategy_registry", "as_of": NOW.isoformat(), "sample_count": 100, "metrics": {"validation_score": .9}},
        {"evidence_type": "OOS_VALIDATION", "source": "validation_queue", "as_of": NOW.isoformat(), "sample_count": 0, "metrics": {"net_edge_bps": 12}},
        {"evidence_type": "COST_STRESS", "source": "execution", "as_of": NOW.isoformat(), "sample_count": 0, "metrics": {"net_edge_bps": 8, "stress_multiplier": 1.0}},
    ]
    g = gate(reg, records)
    assert not g.passed
    assert "NEED_POSITIVE_OOS_OR_SHADOW_EVIDENCE" in g.missing_requirements
    assert "NEED_POSITIVE_COST_STRESS_2X" in g.missing_requirements


def test_sufficient_oos_and_two_x_cost_can_pass():
    reg = {"validation_status": "VALIDATED", "promotion_stage": "CHALLENGER", "cross_engine_validated": True, "dynamic_universe_generalized": True}
    records = [
        {"evidence_type": "STATISTICAL_VALIDATION", "source": "validated_strategy_registry", "as_of": NOW.isoformat(), "sample_count": 100, "metrics": {"validation_score": .9}},
        {"evidence_type": "OOS_VALIDATION", "source": "oos_holdout", "as_of": NOW.isoformat(), "sample_count": 120, "metrics": {"net_edge_bps": 12, "quality_score": .9}},
        {"evidence_type": "COST_STRESS", "source": "execution_v236", "as_of": NOW.isoformat(), "sample_count": 120, "metrics": {"net_edge_bps": 8, "stress_multiplier": 2.0, "passed": True}},
    ]
    g = gate(reg, records, q=.8)
    assert g.passed
    assert g.readiness_score == 1.0
    assert "CHAMPION_REVIEW_GATE_PASS" in g.positive_reasons


def test_rejected_promotion_reason_is_unambiguous():
    reg = {"validation_status": "VALIDATED", "promotion_stage": "REJECTED_AFTER_GENERALIZATION", "cross_engine_validated": True, "dynamic_universe_generalized": False}
    g = gate(reg, [])
    assert "VALIDATION_STATUS_VALIDATED" in g.positive_reasons
    assert "UPSTREAM_PROMOTION_REJECTED" in g.blockers
    assert "UPSTREAM_VALIDATION_REJECTED" not in g.blockers
