from __future__ import annotations
from typing import Mapping
import math
import numpy as np
from .asset_exposure_contracts_v2_35 import ExposurePolicyV235, ExposureConstraintResult
from .asset_exposure_engine_v2_35 import PortfolioExposureSnapshot

def _breaches(exposures: Mapping[str,float], cap: float, prefix: str) -> list[str]:
    return [f"{prefix}_CAP:{k}:{v:.6f}>{cap:.6f}" for k,v in exposures.items() if float(v)>cap+1e-12]

def evaluate_exposure_constraints(
    snapshot: PortfolioExposureSnapshot,
    *, policy: ExposurePolicyV235 | None=None,
    pairwise_etf_overlap: Mapping[str,float] | None=None,
) -> ExposureConstraintResult:
    cfg=policy or ExposurePolicyV235(); blockers=[]
    blockers += _breaches(snapshot.sector,cfg.max_sector_weight,"SECTOR")
    blockers += _breaches(snapshot.industry,cfg.max_industry_weight,"INDUSTRY")
    blockers += _breaches(snapshot.country,cfg.max_country_weight,"COUNTRY")
    blockers += _breaches(snapshot.currency,cfg.max_currency_weight,"CURRENCY")
    blockers += _breaches({k:abs(v) for k,v in snapshot.commodity.items()},cfg.max_single_commodity_weight,"COMMODITY")
    if snapshot.unknown_lookthrough_weight>cfg.max_unknown_lookthrough_weight:
        blockers.append(f"UNKNOWN_LOOKTHROUGH_CAP:{snapshot.unknown_lookthrough_weight:.6f}>{cfg.max_unknown_lookthrough_weight:.6f}")
    for factor,value in snapshot.factor.items():
        cap=cfg.max_abs_factor_exposure.get(str(factor).upper())
        if cap is not None and abs(float(value))>cap+1e-12:
            blockers.append(f"FACTOR_CAP:{factor}:{value:.6f}>{cap:.6f}")
    if pairwise_etf_overlap:
        for pair,value in pairwise_etf_overlap.items():
            if float(value)>cfg.max_pairwise_etf_overlap+1e-12:
                blockers.append(f"ETF_OVERLAP_CAP:{pair}:{float(value):.6f}>{cfg.max_pairwise_etf_overlap:.6f}")
    diagnostics={
        "max_sector":max(snapshot.sector.values(),default=0.0),
        "max_industry":max(snapshot.industry.values(),default=0.0),
        "max_country":max(snapshot.country.values(),default=0.0),
        "max_currency":max(snapshot.currency.values(),default=0.0),
        "max_abs_factor":max((abs(v) for v in snapshot.factor.values()),default=0.0),
        "max_abs_commodity":max((abs(v) for v in snapshot.commodity.values()),default=0.0),
        "unknown_lookthrough_weight":snapshot.unknown_lookthrough_weight,
    }
    return ExposureConstraintResult("PASS" if not blockers else "BLOCK",tuple(blockers),diagnostics)
__all__=["evaluate_exposure_constraints"]
