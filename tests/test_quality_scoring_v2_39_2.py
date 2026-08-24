from datetime import datetime, timezone

from stocks.research.continuous.evidence_taxonomy_v2_39_2 import evidence_breadth_v2392
from stocks.research.continuous.quality_scoring_v2_39_2 import quality_score_v2392

NOW = datetime(2026, 8, 24, 18, 0, tzinfo=timezone.utc)
POLICY = {"minimum_oos_observations": 60, "minimum_cost_stress_multiplier": 2.0, "minimum_shadow_trades_for_promotion_review": 30, "minimum_independent_evidence_classes": 2, "minimum_independent_evidence_sources": 2}
WEIGHTS = {"statistical_validation": .15, "oos_robustness": .15, "cost_robustness": .15, "shadow_evidence": .15, "cross_engine": .10, "generalization": .10, "calibration": .05, "evidence_breadth": .10, "freshness": .05}
REG = {"validation_status": "VALIDATED", "cross_engine_validated": True, "dynamic_universe_generalized": True}


def q(records):
    b = evidence_breadth_v2392(records, now=NOW)
    return quality_score_v2392(latest_registry=REG, records=records, shadow_trades=0, posterior_net_edge_bps=None, breadth=b, weights=WEIGHTS, policy=POLICY, drift_severity=0, decay_severity=0, disagreement=0)


def test_zero_sample_oos_cannot_score_as_perfect_oos():
    records = [{"evidence_type": "OOS_VALIDATION", "source": "strategy_generation_validation_v222", "as_of": NOW.isoformat(), "sample_count": 0, "metrics": {"median_test_expectancy_bps": 10, "robustness_score": 1.0}}]
    score = q(records)
    assert score.components["oos_robustness"] == 0.0
    assert score.diagnostics["oos_observations"] == 0


def test_half_sample_oos_scores_below_full_sample():
    r30 = [{"evidence_type": "OOS_VALIDATION", "source": "oos", "as_of": NOW.isoformat(), "sample_count": 30, "metrics": {"net_edge_bps": 10, "quality_score": 1.0}}]
    r60 = [{"evidence_type": "OOS_VALIDATION", "source": "oos", "as_of": NOW.isoformat(), "sample_count": 60, "metrics": {"net_edge_bps": 10, "quality_score": 1.0}}]
    assert q(r30).components["oos_robustness"] < q(r60).components["oos_robustness"]
    assert q(r60).components["oos_robustness"] == 1.0


def test_positive_one_x_cost_is_partial_not_gate_grade_score():
    records = [{"evidence_type": "COST_STRESS", "source": "execution", "as_of": NOW.isoformat(), "metrics": {"net_edge_bps": 7, "stress_multiplier": 1.0, "quality_score": 1.0}}]
    score = q(records)
    assert 0 < score.components["cost_robustness"] <= 0.5
    assert score.diagnostics["max_positive_cost_stress_multiplier"] == 1.0


def test_positive_two_x_cost_gets_full_component_with_good_quality():
    records = [{"evidence_type": "COST_STRESS", "source": "execution", "as_of": NOW.isoformat(), "metrics": {"net_edge_bps": 7, "stress_multiplier": 2.0, "quality_score": 1.0}}]
    assert q(records).components["cost_robustness"] == 1.0
