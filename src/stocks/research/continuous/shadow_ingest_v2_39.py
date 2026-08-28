from __future__ import annotations
import hashlib, json
from pathlib import Path
from .evidence_v2_39 import load_records
from .store_v2_39 import ResearchStoreV239, utc_now
from .contracts_v2_39 import EvidenceRecordV239

def ingest_shadow_records(store: ResearchStoreV239, records, *, source_ref_prefix: str='shadow') -> dict:
    seen=added=0
    for r in records:
        seen+=1; sid=str(r.get('strategy_id') or '').strip()
        if not sid: continue
        entity_id=sid if sid.startswith('STRATEGY:') else f'STRATEGY:{sid}'
        if store.get_entity(entity_id) is None: store.register_manual(entity_id,'STRATEGY',source='V2_37_SHADOW')
        metrics={k:r.get(k) for k in ('symbol','forecast_gross_edge_bps','realized_gross_return_bps','realized_net_return_bps','forecast_error_bps','predicted_round_trip_cost_bps','realized_cost_bps','cost_prediction_error_bps','mfe_bps','mae_bps','bars_held','exit_reason') if k in r}
        identity=str(r.get('position_id') or hashlib.sha256(json.dumps(r,sort_keys=True,default=str).encode()).hexdigest()[:20])
        as_of=str(r.get('closed_at') or r.get('as_of') or utc_now())
        ev=EvidenceRecordV239(entity_id,'SHADOW_TRADE',as_of,metrics,'v2.37_shadow_lifecycle',f'{source_ref_prefix}:{identity}',sample_count=1)
        added += int(store.add_evidence(ev))
    return {'seen':seen,'added':added}

def ingest_shadow_file(store: ResearchStoreV239, path: str | Path) -> dict:
    p=Path(path); return ingest_shadow_records(store,load_records(p),source_ref_prefix=str(p.resolve()))

def ingest_shadow_inbox(project_root: Path, store: ResearchStoreV239, globs: list[str]) -> dict:
    files=[]; seen=added=0
    for pattern in globs:
        patt=str((project_root/pattern) if not Path(pattern).is_absolute() else pattern)
        import glob
        for name in sorted(glob.glob(patt)):
            p=Path(name); result=ingest_shadow_file(store,p); files.append(str(p)); seen+=result['seen']; added+=result['added']
    return {'files':files,'seen':seen,'added':added}

__all__=["ingest_shadow_file","ingest_shadow_inbox","ingest_shadow_records"]
