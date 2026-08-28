import json
from pathlib import Path

from stocks.research.continuous.contracts_v2_39 import EntityV239, EvidenceRecordV239
from stocks.research.continuous.export_v2_39_2 import export_snapshot_v2392
from stocks.research.continuous.store_v2_39 import ResearchStoreV239, utc_now

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config/continuous_quant_research_v2_39_2.json").read_text())


def test_export_contains_quality_and_readiness(tmp_path):
    store = ResearchStoreV239(tmp_path / "r.db")
    store.upsert_entity(EntityV239("S", "STRATEGY", family="trend", role="CHALLENGER"))
    store.add_evidence(EvidenceRecordV239("S", "REGISTRY_SNAPSHOT", utc_now(), {"validation_status": "VALIDATED", "promotion_stage": "CHALLENGER", "cross_engine_validated": True, "dynamic_universe_generalized": True}, "research_candidate_registry", "r", 1))
    status = export_snapshot_v2392(tmp_path / "out", store, cfg=CFG)
    assert status["schema"] == "continuous_quant_research_status_v2_39_2"
    a = status["assessments"][0]
    assert "quality_score" in a
    assert "promotion_readiness_score" in a
    assert (tmp_path / "out/quality_scorecard_v2_39_2.csv").is_file()
    assert (tmp_path / "out/evidence_gaps_v2_39_2.csv").is_file()
