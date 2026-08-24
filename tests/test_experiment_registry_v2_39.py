from stocks.research.continuous.contracts_v2_39 import EntityV239
from stocks.research.continuous.store_v2_39 import ResearchStoreV239

def test_experiment_history_is_persistent(tmp_path):
    s=ResearchStoreV239(tmp_path/'r.db'); s.upsert_entity(EntityV239('S','STRATEGY'))
    x=s.register_experiment(entity_id='S',experiment_type='COST_STRESS',hypothesis='survives 2x',config={'multiple':2})
    s.update_experiment(x,status='RUNNING'); s.update_experiment(x,status='SUCCEEDED',result_ref='artifact.json')
    row=s.experiments()[0]; assert row['experiment_id']==x and row['status']=='SUCCEEDED' and row['config']['multiple']==2
