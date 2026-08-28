from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Iterable
from .contracts_v2_39 import EvidenceRecordV239
from .store_v2_39 import ResearchStoreV239, utc_now

def ingest_evidence_records(store: ResearchStoreV239, records: Iterable[dict]) -> dict:
    added=0; seen=0
    for r in records:
        seen+=1
        entity_id=str(r.get('entity_id') or '').strip()
        if not entity_id: raise ValueError('entity_id required')
        if store.get_entity(entity_id) is None:
            store.register_manual(entity_id,str(r.get('entity_type') or 'UNKNOWN'),str(r.get('family') or 'UNKNOWN'),str(r.get('source') or 'EVIDENCE_IMPORT'))
        metrics=r.get('metrics')
        if metrics is None:
            reserved={'entity_id','entity_type','family','evidence_type','as_of','source','source_ref','sample_count'}
            metrics={k:v for k,v in r.items() if k not in reserved}
        if isinstance(metrics,str): metrics=json.loads(metrics)
        ev=EvidenceRecordV239(entity_id,str(r.get('evidence_type') or 'GENERIC'),str(r.get('as_of') or utc_now()),dict(metrics),str(r.get('source') or 'MANUAL_IMPORT'),str(r.get('source_ref') or f"manual:{seen}:{utc_now()}"),int(r.get('sample_count') or 0))
        added += int(store.add_evidence(ev))
    return {'seen':seen,'added':added}

def load_records(path: str | Path) -> list[dict]:
    p=Path(path)
    if p.suffix.lower()=='.jsonl': return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    if p.suffix.lower()=='.json':
        data=json.loads(p.read_text()); return data if isinstance(data,list) else [data]
    if p.suffix.lower()=='.csv':
        with p.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
    raise ValueError('supported: .jsonl .json .csv')

__all__=["ingest_evidence_records","load_records"]
