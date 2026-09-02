from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping
import pandas as pd
from .asset_exposure_contracts_v2_35 import InstrumentExposureProfile, ExposurePolicyV235
from .asset_exposure_engine_v2_35 import build_portfolio_exposure
from .exposure_constraints_v2_35 import evaluate_exposure_constraints
from .exposure_overlap_v2_35 import weighted_holdings_overlap

@dataclass(frozen=True)
class PortfolioExposureBundleV235:
    snapshot: dict[str,object]
    constraints: dict[str,object]
    pairwise_etf_overlap: Mapping[str,float]
    execution_authority: str="NONE"
    def as_dict(self): return asdict(self)

def _holdings_map(frame: pd.DataFrame, etf: str, decision_time) -> dict[str,float]:
    from .etf_lookthrough_v2_35 import point_in_time_holdings
    pit=point_in_time_holdings(frame,etf_symbol=etf,decision_time=decision_time)
    return {str(r.constituent_symbol).upper():float(r.weight) for r in pit.itertuples(index=False)}

def analyze_portfolio_exposure(
    weights: Mapping[str,float],
    profiles: Mapping[str,InstrumentExposureProfile],
    *, decision_time, etf_holdings: pd.DataFrame | None=None,
    policy: ExposurePolicyV235 | None=None,
) -> PortfolioExposureBundleV235:
    snapshot=build_portfolio_exposure(weights,profiles,decision_time=decision_time,etf_holdings=etf_holdings)
    overlaps={}
    if etf_holdings is not None:
        etfs=[s for s,w in weights.items() if w>0 and s in profiles and profiles[s].asset_kind.value in {"ETF","COMMODITY_ETF"}]
        maps={e:_holdings_map(etf_holdings,e,decision_time) for e in etfs}
        for i,a in enumerate(sorted(etfs)):
            for b in sorted(etfs)[i+1:]:
                overlaps[f"{a}|{b}"]=weighted_holdings_overlap(maps[a],maps[b])
    constraints=evaluate_exposure_constraints(snapshot,policy=policy,pairwise_etf_overlap=overlaps)
    return PortfolioExposureBundleV235(snapshot.as_dict(),constraints.as_dict(),dict(sorted(overlaps.items())))
__all__=["PortfolioExposureBundleV235","analyze_portfolio_exposure"]
