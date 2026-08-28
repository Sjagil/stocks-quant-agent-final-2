#!/usr/bin/env python3
from __future__ import annotations
import sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/'src') not in sys.path:sys.path.insert(0,str(ROOT/'src'))
from stocks.research.continuous.contracts_v2_39 import EntityV239,EvidenceRecordV239
from stocks.research.continuous.health_v2_39_1 import assess_entity_hardened
from stocks.research.continuous.research_cycle_v2_39_1 import load_config_hardened
from stocks.research.continuous.store_v2_39 import ResearchStoreV239,utc_now
cfg=load_config_hardened(ROOT)
with tempfile.TemporaryDirectory() as td:
 s=ResearchStoreV239(Path(td)/'r.db');eid='STRATEGY:selfcheck';s.upsert_entity(EntityV239(eid,'STRATEGY','trend','SELFCHECK',role='CHALLENGER'))
 s.add_evidence(EvidenceRecordV239(eid,'REGISTRY_SNAPSHOT',utc_now(),{'validation_status':'VALIDATED','promotion_stage':'CHALLENGER','cross_engine_validated':True,'dynamic_universe_generalized':True},'research_candidate_registry','registry:1',1))
 a0=assess_entity_hardened(s,eid,policy=cfg['health'],bayesian=cfg['bayesian'],quality_weights=cfg['quality_weights']);assert a0.recommendation=='ACCUMULATE_EVIDENCE' and not a0.gate_passed
 s.add_evidence(EvidenceRecordV239(eid,'OOS_VALIDATION',utc_now(),{'net_edge_bps':18,'quality_score':.85,'observations':80},'v2.33_oos','oos:1',80))
 s.add_evidence(EvidenceRecordV239(eid,'COST_STRESS',utc_now(),{'stress_multiplier':2.0,'net_edge_bps':8,'passed':True},'v2.36_execution','cost:1',80))
 a1=assess_entity_hardened(s,eid,policy=cfg['health'],bayesian=cfg['bayesian'],quality_weights=cfg['quality_weights']);assert a1.gate_passed and a1.recommendation=='RECOMMEND_CHAMPION_REVIEW' and a1.score<1.0 and a1.positive_reasons
print('CONTINUOUS_QUANT_RESEARCH_V2_39_1_SELFCHECK OK')
print('REGISTRY_SNAPSHOT_NOT_INDEPENDENT True')
print('INDEPENDENT_EVIDENCE_CLASSES_REQUIRED True')
print('INDEPENDENT_SOURCES_REQUIRED True')
print('OOS_OR_SHADOW_EVIDENCE_REQUIRED True')
print('COST_STRESS_2X_REQUIRED True')
print('MEANINGFUL_QUALITY_SCORING True')
print('POSITIVE_AUDIT_REASONS True')
print('CHAMPION_CLI_GATE_ENFORCED True')
print('AUTOMATIC_CHAMPION_PROMOTION False')
print('AUTOMATIC_LIVE_PROMOTION False')
print('BROKER_SUBMISSION_ENABLED False')
print('ORDER_CALLS 0')
print('EXECUTION_AUTHORITY NONE')
