import pandas as pd
from stocks.research.continuous.candidate_sync_v2_39 import sync_candidate_registry
from stocks.research.continuous.store_v2_39 import ResearchStoreV239

def test_sync_existing_registry_is_immediately_usable(tmp_path):
 p=tmp_path/'artifacts/research_runtime/research_candidate_registry'; p.mkdir(parents=True)
 pd.DataFrame([{'hypothesis_id':'h1','family':'trend','promotion_stage':'CHALLENGER','validation_status':'VALIDATED','cross_engine_validated':True,'dynamic_universe_generalized':True}]).to_csv(p/'registry.csv',index=False)
 s=ResearchStoreV239(tmp_path/'r.db'); out=sync_candidate_registry(tmp_path,s,rebuild=False)
 assert out['candidate_count']==1; e=s.get_entity('STRATEGY:h1'); assert e['role']=='CHALLENGER' and e['is_active']==1
