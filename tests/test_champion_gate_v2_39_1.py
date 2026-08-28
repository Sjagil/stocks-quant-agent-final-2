from stocks.research.continuous.contracts_v2_39 import EntityV239,EvidenceRecordV239
from stocks.research.continuous.health_v2_39_1 import assess_entity_hardened
from stocks.research.continuous.store_v2_39 import ResearchStoreV239,utc_now
POL={'stale_evidence_hours':999,'promotion_evidence_fresh_hours':999,'psi_watch':.1,'psi_quarantine':.25,'js_watch':.08,'js_quarantine':.2,'decay_watch':.35,'decay_quarantine':.7,'disagreement_watch':.45,'disagreement_quarantine':.75,'minimum_shadow_trades_for_promotion_review':3,'minimum_independent_evidence_classes':2,'minimum_independent_evidence_sources':2,'minimum_oos_observations':5,'minimum_posterior_net_edge_bps':0,'minimum_cost_stress_multiplier':2.0,'require_cost_robustness_for_champion_review':True,'require_fresh_outcome_evidence':True,'minimum_quality_score_for_champion_review':.60}
B={'prior_mean_bps':0,'prior_strength':2};W={'statistical_validation':.15,'oos_robustness':.15,'cost_robustness':.15,'shadow_evidence':.15,'cross_engine':.10,'generalization':.10,'calibration':.05,'evidence_breadth':.10,'freshness':.05}
def setup(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db');s.upsert_entity(EntityV239('S','STRATEGY',role='CHALLENGER'));s.add_evidence(EvidenceRecordV239('S','REGISTRY_SNAPSHOT',utc_now(),{'validation_status':'VALIDATED','promotion_stage':'CHALLENGER','cross_engine_validated':True,'dynamic_universe_generalized':True},'research_candidate_registry','reg',1));return s
def test_single_registry_snapshot_never_promotes(tmp_path):
 a=assess_entity_hardened(setup(tmp_path),'S',policy=POL,bayesian=B,quality_weights=W);assert not a.gate_passed;assert a.recommendation=='ACCUMULATE_EVIDENCE';assert a.independent_classes==0;assert 'NEED_2_INDEPENDENT_EVIDENCE_CLASSES' in a.missing_requirements
def test_cross_generalized_metadata_alone_never_promotes(tmp_path):
 a=assess_entity_hardened(setup(tmp_path),'S',policy=POL,bayesian=B,quality_weights=W);assert 'CROSS_ENGINE_VALIDATED' in a.positive_reasons and 'DYNAMIC_UNIVERSE_GENERALIZED' in a.positive_reasons and not a.gate_passed
def test_positive_oos_plus_2x_cost_can_pass_without_shadow(tmp_path):
 s=setup(tmp_path);s.add_evidence(EvidenceRecordV239('S','OOS_VALIDATION',utc_now(),{'net_edge_bps':20,'quality_score':.9,'observations':8},'v2.33_oos','oos',8));s.add_evidence(EvidenceRecordV239('S','COST_STRESS',utc_now(),{'stress_multiplier':2.0,'net_edge_bps':9,'passed':True},'v2.36_execution','cost',8));a=assess_entity_hardened(s,'S',policy=POL,bayesian=B,quality_weights=W);assert a.gate_passed and a.recommendation=='RECOMMEND_CHAMPION_REVIEW';assert 'OOS_EVIDENCE_SUFFICIENT' in a.positive_reasons and 'COST_STRESS_PASS' in a.positive_reasons;assert .6<=a.score<1
def test_one_x_cost_does_not_satisfy_gate(tmp_path):
 s=setup(tmp_path);s.add_evidence(EvidenceRecordV239('S','OOS_VALIDATION',utc_now(),{'net_edge_bps':20,'observations':8},'v2.33_oos','oos',8));s.add_evidence(EvidenceRecordV239('S','COST_STRESS',utc_now(),{'stress_multiplier':1.0,'net_edge_bps':9},'v2.36_execution','cost',8));a=assess_entity_hardened(s,'S',policy=POL,bayesian=B,quality_weights=W);assert not a.gate_passed and 'NEED_POSITIVE_COST_STRESS_2X' in a.missing_requirements
def test_positive_shadow_plus_cost_can_pass(tmp_path):
 s=setup(tmp_path)
 for i,x in enumerate([10,12,15,11]):s.add_evidence(EvidenceRecordV239('S','SHADOW_TRADE',utc_now(),{'realized_net_return_bps':x},'v2.37_shadow',f'p{i}',1))
 s.add_evidence(EvidenceRecordV239('S','COST_STRESS',utc_now(),{'stress_multiplier':2.0,'net_edge_bps':5},'v2.36_execution','cost',4));a=assess_entity_hardened(s,'S',policy=POL,bayesian=B,quality_weights=W);assert a.gate_passed and 'SHADOW_SAMPLE_SUFFICIENT' in a.positive_reasons
