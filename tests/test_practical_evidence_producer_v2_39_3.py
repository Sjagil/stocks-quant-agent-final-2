import pandas as pd
from stocks.research.continuous.contracts_v2_39 import EntityV239,EvidenceRecordV239
from stocks.research.continuous.evidence_production_contracts_v2_39_3 import ProductionInputAuditV2393
from stocks.research.continuous.store_v2_39 import ResearchStoreV239
import stocks.research.continuous.practical_evidence_producer_v2_39_3 as mod


def _continuous():
    return {'runtime_root':'runtime','database_name':'r.db','health':{'minimum_shadow_trades_for_promotion_review':30,'minimum_independent_evidence_classes':2,'minimum_independent_evidence_sources':2,'minimum_oos_observations':60,'minimum_posterior_net_edge_bps':0,'minimum_cost_stress_multiplier':2,'require_cost_robustness_for_champion_review':True,'require_fresh_outcome_evidence':True,'minimum_quality_score_for_champion_review':.72,'promotion_evidence_fresh_hours':100000,'psi_quarantine':.25,'js_quarantine':.2,'decay_quarantine':.7,'disagreement_quarantine':.75},'bayesian':{'prior_mean_bps':0,'prior_strength':20},'quality_weights':{'statistical_validation':.15,'oos_robustness':.15,'cost_robustness':.15,'shadow_evidence':.15,'cross_engine':.1,'generalization':.1,'calibration':.05,'evidence_breadth':.1,'freshness':.05}}


def _production():
    return {'runtime_subdir':'prod','minimum_effective_oos_observations':60,'minimum_raw_oos_trades':60,'factory_1h':{'artifact_root':'factory'},'cost_stress':{'multipliers':[1,1.5,2,3],'required_multiplier':2,'require_effective_sample_for_pass':True},'produce_due':{'max_entities':10,'roles':['CHALLENGER'],'skip_quarantined':True,'require_foundation_first':True}}


def _store(tmp_path):
    s=ResearchStoreV239(tmp_path/'runtime/r.db')
    s.upsert_entity(EntityV239('STRATEGY:h','STRATEGY','trend','CANDIDATE_REGISTRY','v2.39','CHALLENGER',metadata={'strategy':'trend','family':'trend','params_json':'{}'}))
    s.add_evidence(EvidenceRecordV239('STRATEGY:h','REGISTRY_SNAPSHOT','2026-08-20T00:00:00+00:00',{'validation_status':'VALIDATED','promotion_stage':'CHALLENGER','cross_engine_validated':True,'dynamic_universe_generalized':True},'research_candidate_registry','reg',1))
    return s


def test_strong_observation_evidence_moves_gate_using_real_store(monkeypatch,tmp_path):
    s=_store(tmp_path)
    monkeypatch.setattr(mod,'audit_entity_inputs',lambda *a,**k: ProductionInputAuditV2393('STRATEGY:h','TEST','READY',True,(),{'base_cost_bps_per_side':3}))
    base=pd.Timestamp('2026-08-01T00:00:00Z')
    obs=pd.DataFrame([{'hypothesis_id':'h','fold':1+i//20,'symbol':'AAPL','entry_time':base+pd.Timedelta(hours=3*i),'exit_time':base+pd.Timedelta(hours=3*i+1),'gross_return':.004 if i%5 else -.001} for i in range(80)])
    monkeypatch.setattr(mod,'replay_factory_oos',lambda *a,**k:(obs,{'base_cost_bps_per_side':3.0,'selection_rule':'TEST_OPENED_ONLY_AFTER_TRAIN_VALID_SELECTION','provenance_hash':'prov'}))
    r=mod.produce_entity_evidence(tmp_path,s,'STRATEGY:h',production_cfg=_production(),continuous_cfg=_continuous())
    assert r.status=='PRODUCED_QUALIFIED'
    assert r.evidence_added==5
    assert r.after_assessment['quality_score']>r.before_assessment['quality_score']
    assert r.after_assessment['promotion_sources']==2
    assert r.after_assessment['gate_passed'] is True
    latest_exit=pd.to_datetime(obs['exit_time'],utc=True).max().isoformat()
    produced=[x for x in s.evidence_for('STRATEGY:h') if x['evidence_type'] in {'PURGED_WALK_FORWARD','EXECUTION_COST_STRESS'}]
    assert produced and all(x['as_of']==latest_exit for x in produced)


def test_same_production_rerun_does_not_duplicate_evidence(monkeypatch,tmp_path):
    s=_store(tmp_path)
    monkeypatch.setattr(mod,'audit_entity_inputs',lambda *a,**k: ProductionInputAuditV2393('STRATEGY:h','TEST','READY',True,(),{}))
    base=pd.Timestamp('2026-08-01T00:00:00Z')
    obs=pd.DataFrame([{'hypothesis_id':'h','fold':1,'symbol':'A','entry_time':base+pd.Timedelta(hours=3*i),'exit_time':base+pd.Timedelta(hours=3*i+1),'gross_return':.005} for i in range(80)])
    monkeypatch.setattr(mod,'replay_factory_oos',lambda *a,**k:(obs,{'base_cost_bps_per_side':3.0,'selection_rule':'TEST_OPENED_ONLY_AFTER_TRAIN_VALID_SELECTION','provenance_hash':'same'}))
    a=mod.produce_entity_evidence(tmp_path,s,'STRATEGY:h',production_cfg=_production(),continuous_cfg=_continuous())
    b=mod.produce_entity_evidence(tmp_path,s,'STRATEGY:h',production_cfg=_production(),continuous_cfg=_continuous())
    assert a.evidence_added==5 and b.evidence_added==0
