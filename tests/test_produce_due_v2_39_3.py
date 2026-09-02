from stocks.research.continuous.contracts_v2_39 import EntityV239,EvidenceRecordV239
from stocks.research.continuous.evidence_production_contracts_v2_39_3 import EvidenceProductionResultV2393
from stocks.research.continuous.store_v2_39 import ResearchStoreV239
import stocks.research.continuous.practical_evidence_producer_v2_39_3 as mod


def test_produce_due_prioritizes_foundation_ready_and_skips_rejected(monkeypatch,tmp_path):
    cfg={'runtime_root':'runtime','database_name':'r.db','health':{'minimum_shadow_trades_for_promotion_review':30,'minimum_independent_evidence_classes':2,'minimum_independent_evidence_sources':2,'minimum_oos_observations':60,'minimum_cost_stress_multiplier':2,'require_cost_robustness_for_champion_review':True,'require_fresh_outcome_evidence':True,'minimum_quality_score_for_champion_review':.72,'promotion_evidence_fresh_hours':999999,'psi_quarantine':.25,'js_quarantine':.2,'decay_quarantine':.7,'disagreement_quarantine':.75},'bayesian':{'prior_mean_bps':0,'prior_strength':20},'quality_weights':{'statistical_validation':.15,'oos_robustness':.15,'cost_robustness':.15,'shadow_evidence':.15,'cross_engine':.1,'generalization':.1,'calibration':.05,'evidence_breadth':.1,'freshness':.05}}
    prod={'runtime_subdir':'prod','produce_due':{'roles':['CHALLENGER'],'max_entities':10,'skip_quarantined':True,'require_foundation_first':True}}
    s=ResearchStoreV239(tmp_path/'runtime/r.db')
    for hid,stage,gen in [('good','CHALLENGER',True),('bad','REJECTED_AFTER_GENERALIZATION',False)]:
      s.upsert_entity(EntityV239(f'STRATEGY:{hid}','STRATEGY','x','CANDIDATE_REGISTRY','v','CHALLENGER',metadata={}))
      s.add_evidence(EvidenceRecordV239(f'STRATEGY:{hid}','REGISTRY_SNAPSHOT','2026-08-20T00:00:00+00:00',{'validation_status':'VALIDATED','promotion_stage':stage,'cross_engine_validated':True,'dynamic_universe_generalized':gen},'research_candidate_registry',hid,1))
    def fake(*args,**kwargs):
      eid=args[2]
      return EvidenceProductionResultV2393(eid,'PRODUCED_INSUFFICIENT',{},None,None,0,{}, {},str(tmp_path))
    monkeypatch.setattr(mod,'produce_entity_evidence',fake)
    out=mod.produce_due_evidence(tmp_path,s,production_cfg=prod,continuous_cfg=cfg)
    assert out['attempted']==1
    assert out['results'][0]['entity_id']=='STRATEGY:good'
    assert any(x['entity_id']=='STRATEGY:bad' for x in out['skipped'])
