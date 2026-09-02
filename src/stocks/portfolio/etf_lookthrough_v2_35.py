from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping
import pandas as pd
import numpy as np
from .asset_exposure_contracts_v2_35 import InstrumentExposureProfile, AssetKindV235

@dataclass(frozen=True)
class LookthroughResult:
    etf_symbol: str
    snapshot_available_at: str | None
    known_weight: float
    unknown_weight: float
    sector_exposure: Mapping[str, float]
    industry_exposure: Mapping[str, float]
    country_exposure: Mapping[str, float]
    currency_exposure: Mapping[str, float]
    factor_exposure: Mapping[str, float]
    commodity_exposure: Mapping[str, float]
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def point_in_time_holdings(holdings: pd.DataFrame, *, etf_symbol: str, decision_time) -> pd.DataFrame:
    required={"etf_symbol","constituent_symbol","weight","available_at"}
    missing=required-set(holdings.columns)
    if missing: raise ValueError(f"holdings missing columns: {sorted(missing)}")
    frame=holdings.copy()
    frame["etf_symbol"]=frame["etf_symbol"].astype(str).str.upper()
    frame["constituent_symbol"]=frame["constituent_symbol"].astype(str).str.upper()
    frame["available_at"]=pd.to_datetime(frame["available_at"],utc=True,errors="coerce")
    frame["weight"]=pd.to_numeric(frame["weight"],errors="coerce")
    decision=pd.Timestamp(decision_time)
    if decision.tzinfo is None: decision=decision.tz_localize("UTC")
    else: decision=decision.tz_convert("UTC")
    eligible=frame[(frame["etf_symbol"]==str(etf_symbol).upper()) & frame["available_at"].notna() & (frame["available_at"]<=decision)]
    if eligible.empty: return eligible.iloc[0:0].copy()
    snapshot=eligible["available_at"].max()
    out=eligible[eligible["available_at"]==snapshot].copy()
    out=out[np.isfinite(out["weight"]) & (out["weight"]>=0)]
    total=float(out["weight"].sum())
    if total<=0: return out.iloc[0:0].copy()
    if total>1.000001:
        out["weight"]=out["weight"]/total
    return out.sort_values(["weight","constituent_symbol"],ascending=[False,True]).reset_index(drop=True)

def _add(target: dict[str,float], key: str, value: float) -> None:
    target[key]=target.get(key,0.0)+float(value)

def build_etf_lookthrough(
    etf_symbol: str,
    holdings: pd.DataFrame,
    profiles: Mapping[str, InstrumentExposureProfile],
    *,
    decision_time,
) -> LookthroughResult:
    frame=point_in_time_holdings(holdings,etf_symbol=etf_symbol,decision_time=decision_time)
    sectors={}; industries={}; countries={}; currencies={}; factors={}; commodities={}
    known=0.0
    for row in frame.itertuples(index=False):
        weight=float(row.weight); profile=profiles.get(str(row.constituent_symbol).upper())
        if profile is None: continue
        known += weight
        _add(sectors,profile.sector,weight)
        _add(industries,profile.industry,weight)
        _add(countries,profile.country,weight)
        _add(currencies,profile.currency,weight)
        for k,v in profile.factor_exposures.items(): _add(factors,k,weight*v)
        for k,v in profile.commodity_exposures.items(): _add(commodities,k,weight*v)
    snapshot=None if frame.empty else pd.Timestamp(frame["available_at"].iloc[0]).isoformat()
    total=float(frame["weight"].sum()) if not frame.empty else 0.0
    unknown=max(0.0,total-known)
    return LookthroughResult(
        str(etf_symbol).upper(),snapshot,float(known),float(unknown),
        dict(sorted(sectors.items())),dict(sorted(industries.items())),
        dict(sorted(countries.items())),dict(sorted(currencies.items())),
        dict(sorted(factors.items())),dict(sorted(commodities.items())),
    )

__all__=["LookthroughResult","build_etf_lookthrough","point_in_time_holdings"]
