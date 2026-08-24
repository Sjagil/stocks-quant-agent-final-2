from __future__ import annotations
import pandas as pd
from .gem_contracts_v2_35_1 import GemScreenerPolicyV2351

def diversify_gem_shortlist(frame: pd.DataFrame, *, limit: int=20, policy: GemScreenerPolicyV2351 | None=None) -> pd.DataFrame:
    cfg=policy or GemScreenerPolicyV2351()
    ranked=frame.sort_values(["gem_score","symbol"],ascending=[False,True])
    sector_count={}; industry_count={}; chosen=[]
    for idx,row in ranked.iterrows():
        sector=str(row.get("sector","UNKNOWN")).upper(); industry=str(row.get("industry","UNKNOWN")).upper()
        if sector_count.get(sector,0)>=cfg.max_per_sector: continue
        if industry_count.get(industry,0)>=cfg.max_per_industry: continue
        chosen.append(idx); sector_count[sector]=sector_count.get(sector,0)+1; industry_count[industry]=industry_count.get(industry,0)+1
        if len(chosen)>=limit: break
    out=ranked.loc[chosen].copy()
    out["shortlist_rank"]=range(1,len(out)+1)
    return out

__all__=["diversify_gem_shortlist"]
