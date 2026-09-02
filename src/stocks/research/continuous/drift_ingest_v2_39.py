from __future__ import annotations
import hashlib, json
from pathlib import Path
import pandas as pd
from .contracts_v2_39 import EvidenceRecordV239
from .drift_decay_v2_39 import dataframe_drift
from .store_v2_39 import ResearchStoreV239, utc_now

def compute_and_store_drift(store: ResearchStoreV239, entity_id: str, reference_path: str|Path, current_path: str|Path, *, features=None) -> dict:
    refp=Path(reference_path); curp=Path(current_path)
    ref=pd.read_csv(refp); cur=pd.read_csv(curp)
    report,severity=dataframe_drift(ref,cur,features=features)
    psi=float(pd.to_numeric(report.get('psi',pd.Series(dtype=float)),errors='coerce').max()) if not report.empty else 0.0
    js=float(pd.to_numeric(report.get('js_divergence',pd.Series(dtype=float)),errors='coerce').max()) if not report.empty else 0.0
    if not pd.notna(psi): psi=0.0
    if not pd.notna(js): js=0.0
    payload={'psi_max':psi,'js_max':js,'severity':severity,'features':report.to_dict(orient='records')}
    fp=hashlib.sha256((str(refp.resolve())+str(refp.stat().st_mtime_ns)+str(curp.resolve())+str(curp.stat().st_mtime_ns)+json.dumps(features,sort_keys=True,default=str)).encode()).hexdigest()[:20]
    ev=EvidenceRecordV239(entity_id,'DRIFT',utc_now(),payload,'v2.31_drift_bridge',f'drift:{fp}',sample_count=len(report))
    added=store.add_evidence(ev)
    return {'added':added,**payload}

__all__=["compute_and_store_drift"]
