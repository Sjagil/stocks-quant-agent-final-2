from stocks.research.continuous.contracts_v2_39 import EntityV239
from stocks.research.continuous.export_v2_39 import export_snapshot
from stocks.research.continuous.store_v2_39 import ResearchStoreV239

def test_export_writes_operational_files(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db'); s.upsert_entity(EntityV239('S','STRATEGY')); s.add_recommendation('S','ACCUMULATE_EVIDENCE',.3,())
 out=export_snapshot(tmp_path/'runtime',s); assert (tmp_path/'runtime/status.json').is_file() and (tmp_path/'runtime/status.md').is_file() and out['execution_authority']=='NONE'
