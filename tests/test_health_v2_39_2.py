import json
from pathlib import Path

from stocks.research.continuous.contracts_v2_39 import EntityV239, EvidenceRecordV239
from stocks.research.continuous.health_v2_39_2 import assess_entity_hardened_v2392
from stocks.research.continuous.store_v2_39 import ResearchStoreV239, utc_now

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config/continuous_quant_research_v2_39_2.json").read_text())


def assess(store, eid="S"):
    return assess_entity_hardened_v2392(store, eid, policy=CFG["health"], bayesian=CFG["bayesian"], quality_weights=CFG["quality_weights"])


def registry(store, *, promotion="CHALLENGER", validation="VALIDATED", cross=True, generalized=True):
    store.add_evidence(EvidenceRecordV239("S", "REGISTRY_SNAPSHOT", utc_now(), {"validation_status": validation, "promotion_stage": promotion, "cross_engine_validated": cross, "dynamic_universe_generalized": generalized}, "research_candidate_registry", f"reg-{promotion}-{validation}", 1))


def test_realistic_diagnostic_artifacts_do_not_inflate_score_to_0765(tmp_path):
    s = ResearchStoreV239(tmp_path / "r.db")
    s.upsert_entity(EntityV239("S", "STRATEGY", role="CHALLENGER"))
    registry(s)
    s.add_evidence(EvidenceRecordV239("S", "STATISTICAL_VALIDATION", utc_now(), {"validation_score": 1.0}, "validated_strategy_registry", "stat", 100))
    s.add_evidence(EvidenceRecordV239("S", "OOS_VALIDATION", utc_now(), {"median_test_expectancy_bps": 12, "robustness_score": 1.0}, "strategy_generation_validation_v222", "oos", 0))
    s.add_evidence(EvidenceRecordV239("S", "COST_STRESS", utc_now(), {"median_stress_test_expectancy_bps": 8, "stress_multiplier": 1.0}, "strategy_generation_validation_v222", "cost", 0))
    a = assess(s)
    assert a.recommendation == "ACCUMULATE_EVIDENCE"
    assert not a.gate_passed
    assert a.score < .72
    assert a.quality_components["oos_robustness"] == 0
    assert a.quality_components["cost_robustness"] <= .5
    assert a.promotion_readiness_score < 1


def test_rejected_promotion_is_quarantined_without_contradictory_validation_rejection_label(tmp_path):
    s = ResearchStoreV239(tmp_path / "r.db")
    s.upsert_entity(EntityV239("S", "STRATEGY", role="CHALLENGER"))
    registry(s, promotion="REJECTED_AFTER_GENERALIZATION", validation="VALIDATED", generalized=False)
    a = assess(s)
    assert a.health == "QUARANTINED"
    assert a.recommendation == "RECOMMEND_RETIRE_REVIEW"
    assert "VALIDATION_STATUS_VALIDATED" in a.positive_reasons
    assert "UPSTREAM_PROMOTION_REJECTED" in a.blockers
    assert "UPSTREAM_VALIDATION_REJECTED" not in a.blockers


def test_full_gate_passes_with_real_sample_and_two_x_cost(tmp_path):
    s = ResearchStoreV239(tmp_path / "r.db")
    s.upsert_entity(EntityV239("S", "STRATEGY", role="CHALLENGER"))
    registry(s)
    s.add_evidence(EvidenceRecordV239("S", "STATISTICAL_VALIDATION", utc_now(), {"validation_score": .9}, "validated_strategy_registry", "stat", 100))
    s.add_evidence(EvidenceRecordV239("S", "OOS_VALIDATION", utc_now(), {"net_edge_bps": 14, "quality_score": .9, "observations": 120}, "oos_holdout", "oos", 120))
    s.add_evidence(EvidenceRecordV239("S", "COST_STRESS", utc_now(), {"net_edge_bps": 7, "quality_score": .9, "stress_multiplier": 2.0}, "execution_v236", "cost", 120))
    a = assess(s)
    assert a.gate_passed
    assert a.recommendation == "RECOMMEND_CHAMPION_REVIEW"
    assert a.score >= .72
    assert a.promotion_readiness_score == 1.0
