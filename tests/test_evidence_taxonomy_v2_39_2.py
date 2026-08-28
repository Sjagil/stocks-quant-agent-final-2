from datetime import datetime, timezone

from stocks.research.continuous.evidence_taxonomy_v2_39_2 import (
    COST_ROBUSTNESS, CROSS_ENGINE, GENERALIZATION, OOS_VALIDATION, STATISTICAL_VALIDATION,
    evidence_breadth_v2392,
)

NOW = datetime(2026, 8, 24, 18, 0, tzinfo=timezone.utc)


def rec(t, source, as_of="2026-08-24T17:00:00+00:00"):
    return {"evidence_type": t, "source": source, "as_of": as_of, "metrics": {}}


def test_cross_and_generalization_do_not_count_as_promotion_breadth():
    b = evidence_breadth_v2392([
        rec("CROSS_ENGINE_RESULT", "cross_engine_v217"),
        rec("GENERALIZATION_RESULT", "dynamic_universe_generalization"),
    ], now=NOW)
    assert set(b.independent_classes) == {CROSS_ENGINE, GENERALIZATION}
    assert b.promotion_classes == ()
    assert b.promotion_sources == ()
    assert b.fresh_decision_classes == ()


def test_promotion_breadth_counts_stat_oos_cost_but_not_registry_metadata():
    b = evidence_breadth_v2392([
        rec("REGISTRY_SNAPSHOT", "research_candidate_registry"),
        rec("STATISTICAL_VALIDATION", "validated_strategy_registry"),
        rec("OOS_VALIDATION", "oos_holdout"),
        rec("COST_STRESS", "execution_v236"),
    ], now=NOW)
    assert set(b.promotion_classes) == {STATISTICAL_VALIDATION, OOS_VALIDATION, COST_ROBUSTNESS}
    assert "registry_metadata" not in b.promotion_sources
    assert set(b.fresh_decision_classes) == {OOS_VALIDATION, COST_ROBUSTNESS}


def test_old_decision_evidence_does_not_satisfy_freshness():
    b = evidence_breadth_v2392([
        rec("OOS_VALIDATION", "oos_holdout", "2026-01-01T00:00:00+00:00"),
    ], fresh_hours=720, now=NOW)
    assert b.promotion_classes == (OOS_VALIDATION,)
    assert b.fresh_decision_classes == ()
