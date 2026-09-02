from __future__ import annotations
from typing import Mapping
import pandas as pd
from .asset_exposure_contracts_v2_35 import InstrumentExposureProfile

def exposure_contribution_table(weights: Mapping[str,float], profiles: Mapping[str,InstrumentExposureProfile]) -> pd.DataFrame:
    rows=[]
    for symbol,weight in weights.items():
        p=profiles.get(str(symbol).upper())
        if p is None: continue
        for dimension,label in (("SECTOR",p.sector),("INDUSTRY",p.industry),("COUNTRY",p.country),("CURRENCY",p.currency)):
            rows.append({"symbol":str(symbol).upper(),"dimension":dimension,"bucket":label,"contribution":float(weight)})
        for k,v in p.factor_exposures.items():
            rows.append({"symbol":str(symbol).upper(),"dimension":"FACTOR","bucket":k,"contribution":float(weight)*float(v)})
        for k,v in p.commodity_exposures.items():
            rows.append({"symbol":str(symbol).upper(),"dimension":"COMMODITY","bucket":k,"contribution":float(weight)*float(v)})
    return pd.DataFrame(rows)
__all__=["exposure_contribution_table"]
