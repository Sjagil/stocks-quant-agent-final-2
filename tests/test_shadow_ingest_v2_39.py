from stocks.research.continuous.shadow_ingest_v2_39 import ingest_shadow_records
from stocks.research.continuous.store_v2_39 import ResearchStoreV239

def test_shadow_feedback_becomes_evidence(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db'); r={'position_id':'p1','strategy_id':'abc','realized_net_return_bps':12,'realized_gross_return_bps':20,'forecast_gross_edge_bps':25,'realized_cost_bps':8}
 out=ingest_shadow_records(s,[r]); assert out['added']==1; assert s.counts()['evidence']==1; assert s.get_entity('STRATEGY:abc')
