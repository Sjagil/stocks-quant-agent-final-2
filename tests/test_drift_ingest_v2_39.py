import pandas as pd
from stocks.research.continuous.contracts_v2_39 import EntityV239
from stocks.research.continuous.drift_ingest_v2_39 import compute_and_store_drift
from stocks.research.continuous.store_v2_39 import ResearchStoreV239

def test_csv_drift_command_path(tmp_path):
 a=tmp_path/'a.csv'; b=tmp_path/'b.csv'; pd.DataFrame({'x':range(100)}).to_csv(a,index=False); pd.DataFrame({'x':range(100,200)}).to_csv(b,index=False)
 s=ResearchStoreV239(tmp_path/'r.db'); s.upsert_entity(EntityV239('S','STRATEGY')); out=compute_and_store_drift(s,'S',a,b)
 assert out['added'] and out['severity']>0
