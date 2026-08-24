from __future__ import annotations
from dataclasses import dataclass
import numpy as np, pandas as pd
from .gem_contracts_v2_35_1 import GemScreenerPolicyV2351, GemScreenSummary
from .gem_components_v2_35_1 import build_component_scores
from .gem_risk_flags_v2_35_1 import hard_blockers
from .gem_scoring_v2_35_1 import final_gem_score
from .gem_diversity_v2_35_1 import diversify_gem_shortlist

REQUIRED={"symbol","asset_kind","sector","industry","market_cap","price","avg_dollar_volume_20d","data_quality_score","fundamentals_age_days"}

@dataclass(frozen=True)
class PotentialGemScreenResult:
    ranked: pd.DataFrame
    shortlist: pd.DataFrame
    summary: GemScreenSummary
    execution_authority: str="NONE"

def _tier(score: float, blockers: tuple[str,...], cfg: GemScreenerPolicyV2351) -> str:
    if blockers: return "REJECT"
    if not np.isfinite(score): return "REJECT"
    if score>=cfg.tier_a_score: return "GEM_A"
    if score>=cfg.tier_b_score: return "GEM_B"
    if score>=cfg.watch_score: return "WATCH"
    return "REJECT"

def screen_potential_gems(
    universe: pd.DataFrame,
    *,
    policy: GemScreenerPolicyV2351 | None=None,
    current_sector_exposure: dict[str,float] | None=None,
    current_industry_exposure: dict[str,float] | None=None,
    shortlist_limit: int=20,
) -> PotentialGemScreenResult:
    cfg=policy or GemScreenerPolicyV2351()
    missing=REQUIRED-set(universe.columns)
    if missing: raise ValueError(f"universe missing required columns: {sorted(missing)}")
    frame=universe.copy().reset_index(drop=True)
    frame["symbol"]=frame["symbol"].astype(str).str.upper()
    frame["sector"]=frame["sector"].fillna("UNKNOWN").astype(str).str.upper()
    frame["industry"]=frame["industry"].fillna("UNKNOWN").astype(str).str.upper()
    comps=build_component_scores(frame)
    scored=final_gem_score(frame,comps,policy=cfg,current_sector_exposure=current_sector_exposure,current_industry_exposure=current_industry_exposure)
    blockers=[]; tiers=[]
    for i,row in frame.iterrows():
        b=hard_blockers(row,cfg); blockers.append(b); tiers.append(_tier(float(scored.loc[i,"gem_score"]),b,cfg))
    ranked=pd.concat([frame,scored],axis=1)
    ranked["blockers"]=["|".join(x) for x in blockers]
    ranked["tier"]=tiers
    ranked["eligible"]=ranked["blockers"].eq("")
    ranked=ranked.sort_values(["eligible","gem_score","symbol"],ascending=[False,False,True]).reset_index(drop=True)
    ranked["rank"]=range(1,len(ranked)+1)
    shortlist=diversify_gem_shortlist(ranked[ranked["tier"].isin(["GEM_A","GEM_B","WATCH"])],limit=shortlist_limit,policy=cfg)
    summary=GemScreenSummary(
        total=len(ranked),eligible=int(ranked["eligible"].sum()),
        tier_a=int((ranked["tier"]=="GEM_A").sum()),tier_b=int((ranked["tier"]=="GEM_B").sum()),
        watch=int((ranked["tier"]=="WATCH").sum()),rejected=int((ranked["tier"]=="REJECT").sum()),
    )
    return PotentialGemScreenResult(ranked,shortlist,summary)

__all__=["PotentialGemScreenResult","screen_potential_gems"]
