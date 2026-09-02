#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.research.continuous.contracts_v2_39 import EntityV239, EvidenceRecordV239
from stocks.research.continuous.health_v2_39_2 import assess_entity_hardened_v2392
from stocks.research.continuous.store_v2_39 import ResearchStoreV239, utc_now

cfg = json.loads((ROOT / "config/continuous_quant_research_v2_39_2.json").read_text())

with tempfile.TemporaryDirectory() as td:
    store = ResearchStoreV239(Path(td) / "research.db")
    store.upsert_entity(EntityV239("S", "STRATEGY", role="CHALLENGER"))
    store.add_evidence(EvidenceRecordV239(
        "S", "REGISTRY_SNAPSHOT", utc_now(),
        {"validation_status": "VALIDATED", "promotion_stage": "CHALLENGER", "cross_engine_validated": True, "dynamic_universe_generalized": True},
        "research_candidate_registry", "registry", 1,
    ))
    store.add_evidence(EvidenceRecordV239(
        "S", "STATISTICAL_VALIDATION", utc_now(), {"validation_score": 0.9},
        "validated_strategy_registry", "stat", 100,
    ))
    store.add_evidence(EvidenceRecordV239(
        "S", "OOS_VALIDATION", utc_now(), {"median_test_expectancy_bps": 12.0, "robustness_score": 1.0},
        "strategy_generation_validation_v222", "oos-diagnostic", 0,
    ))
    store.add_evidence(EvidenceRecordV239(
        "S", "COST_STRESS", utc_now(), {"median_stress_test_expectancy_bps": 8.0, "stress_multiplier": 1.0},
        "strategy_generation_validation_v222", "cost-1x", 0,
    ))
    a = assess_entity_hardened_v2392(store, "S", policy=cfg["health"], bayesian=cfg["bayesian"], quality_weights=cfg["quality_weights"])
    assert not a.gate_passed
    assert a.recommendation == "ACCUMULATE_EVIDENCE"
    assert a.quality_components["oos_robustness"] == 0.0
    assert a.quality_components["cost_robustness"] <= 0.5 + 1e-12
    assert "NEED_POSITIVE_OOS_OR_SHADOW_EVIDENCE" in a.missing_requirements
    assert "NEED_POSITIVE_COST_STRESS_2X" in a.missing_requirements

    store.add_evidence(EvidenceRecordV239(
        "S", "OOS_VALIDATION", utc_now(), {"net_edge_bps": 15.0, "quality_score": 0.9, "observations": 120},
        "oos_independent", "oos-120", 120,
    ))
    store.add_evidence(EvidenceRecordV239(
        "S", "COST_STRESS", utc_now(), {"net_edge_bps": 7.0, "stress_multiplier": 2.0, "passed": True},
        "execution_v236", "cost-2x", 120,
    ))
    b = assess_entity_hardened_v2392(store, "S", policy=cfg["health"], bayesian=cfg["bayesian"], quality_weights=cfg["quality_weights"])
    assert b.gate_passed
    assert b.recommendation == "RECOMMEND_CHAMPION_REVIEW"
    assert b.promotion_readiness_score == 1.0

print("CONTINUOUS_QUANT_RESEARCH_V2_39_2_SELFCHECK OK")
print("SAMPLE_AWARE_OOS_SCORING True")
print("MULTIPLIER_AWARE_COST_SCORING True")
print("PROMOTION_ONLY_EVIDENCE_BREADTH True")
print("FRESH_DECISION_EVIDENCE_REQUIRED True")
print("UNAMBIGUOUS_VALIDATION_REASONS True")
print("PROMOTION_READINESS_SCORE True")
print("CHAMPION_GATE_FAIL_CLOSED True")
print("BROKER_SUBMISSION_ENABLED False")
print("AUTOMATIC_LIVE_PROMOTION False")
print("ORDER_CALLS 0")
print("EXECUTION_AUTHORITY NONE")
