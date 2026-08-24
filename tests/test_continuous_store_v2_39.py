from pathlib import Path
from stocks.research.continuous.contracts_v2_39 import EntityV239,EvidenceRecordV239
from stocks.research.continuous.store_v2_39 import ResearchStoreV239,utc_now

def test_store_persists_and_deduplicates(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db'); s.upsert_entity(EntityV239('STRATEGY:a','STRATEGY'))
 e=EvidenceRecordV239('STRATEGY:a','GENERIC',utc_now(),{'x':1},'test','same',1)
 assert s.add_evidence(e) is True and s.add_evidence(e) is False
 s2=ResearchStoreV239(tmp_path/'r.db'); assert s2.get_entity('STRATEGY:a')['entity_type']=='STRATEGY'; assert s2.counts()['evidence']==1

def test_manual_role_is_locked(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db'); s.upsert_entity(EntityV239('X','MODEL',role='CANDIDATE')); s.set_role_manual('X','CHAMPION','reviewed')
 s.upsert_entity(EntityV239('X','MODEL',role='CANDIDATE')); assert s.get_entity('X')['role']=='CHAMPION'
