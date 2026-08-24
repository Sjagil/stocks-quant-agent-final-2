from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping
import pandas as pd
from .asset_exposure_contracts_v2_35 import InstrumentExposureProfile, AssetKindV235
from .etf_lookthrough_v2_35 import build_etf_lookthrough, LookthroughResult

@dataclass(frozen=True)
class PortfolioExposureSnapshot:
    total_invested_weight: float
    cash_weight: float
    sector: Mapping[str,float]
    industry: Mapping[str,float]
    country: Mapping[str,float]
    currency: Mapping[str,float]
    factor: Mapping[str,float]
    commodity: Mapping[str,float]
    unknown_lookthrough_weight: float
    instrument_exposure_rows: tuple[dict[str,object], ...]
    execution_authority: str="NONE"
    def as_dict(self): return asdict(self)

def _add(target: dict[str,float], key: str, value: float):
    target[key]=target.get(key,0.0)+float(value)

def build_portfolio_exposure(
    weights: Mapping[str,float] | pd.Series,
    profiles: Mapping[str,InstrumentExposureProfile],
    *,
    decision_time,
    etf_holdings: pd.DataFrame | None=None,
) -> PortfolioExposureSnapshot:
    w=pd.Series(dict(weights),dtype=float)
    if (w< -1e-12).any(): raise ValueError("v2.35 exposure engine is long-only")
    if w.sum()>1.000001: raise ValueError("weights cannot exceed 100%")
    sectors={}; industries={}; countries={}; currencies={}; factors={}; commodities={}
    unknown=0.0; rows=[]
    for symbol,weight in w.items():
        weight=float(weight)
        if weight<=0: continue
        key=str(symbol).upper(); profile=profiles.get(key)
        if profile is None:
            unknown += weight
            rows.append({"symbol":key,"weight":weight,"status":"PROFILE_MISSING"})
            continue
        if profile.asset_kind in {AssetKindV235.ETF,AssetKindV235.COMMODITY_ETF} and etf_holdings is not None:
            lt=build_etf_lookthrough(key,etf_holdings,profiles,decision_time=decision_time)
            if lt.known_weight>0:
                for k,v in lt.sector_exposure.items(): _add(sectors,k,weight*v)
                for k,v in lt.industry_exposure.items(): _add(industries,k,weight*v)
                for k,v in lt.country_exposure.items(): _add(countries,k,weight*v)
                for k,v in lt.currency_exposure.items(): _add(currencies,k,weight*v)
                for k,v in lt.factor_exposure.items(): _add(factors,k,weight*v)
                for k,v in lt.commodity_exposure.items(): _add(commodities,k,weight*v)
                unknown += weight*lt.unknown_weight
                residual=max(0.0,1.0-lt.known_weight-lt.unknown_weight)
                if residual>0:
                    _add(sectors,profile.sector,weight*residual)
                    _add(industries,profile.industry,weight*residual)
                    _add(countries,profile.country,weight*residual)
                    _add(currencies,profile.currency,weight*residual)
                rows.append({"symbol":key,"weight":weight,"status":"ETF_LOOKTHROUGH","known_weight":lt.known_weight,"unknown_weight":lt.unknown_weight})
                continue
        _add(sectors,profile.sector,weight); _add(industries,profile.industry,weight)
        _add(countries,profile.country,weight); _add(currencies,profile.currency,weight)
        for k,v in profile.factor_exposures.items(): _add(factors,k,weight*v)
        for k,v in profile.commodity_exposures.items(): _add(commodities,k,weight*v)
        rows.append({"symbol":key,"weight":weight,"status":"DIRECT"})
    total=float(w.clip(lower=0).sum())
    return PortfolioExposureSnapshot(
        total,float(max(0.0,1-total)),dict(sorted(sectors.items())),dict(sorted(industries.items())),
        dict(sorted(countries.items())),dict(sorted(currencies.items())),dict(sorted(factors.items())),
        dict(sorted(commodities.items())),float(unknown),tuple(rows)
    )
__all__=["PortfolioExposureSnapshot","build_portfolio_exposure"]
