import pytest, pandas as pd
from stocks.portfolio.asset_exposure_contracts_v2_35 import AssetKindV235, InstrumentExposureProfile, ExposurePolicyV235

def test_profile_normalizes_and_is_research_only():
    p=InstrumentExposureProfile("abc",AssetKindV235.STOCK,sector="Tech",factor_exposures={"market":1.1},data_asof="2026-08-20")
    assert p.symbol=="ABC" and p.sector=="TECH" and p.factor_exposures["MARKET"]==1.1 and p.execution_authority=="NONE"

def test_policy_rejects_bad_cap():
    with pytest.raises(ValueError): ExposurePolicyV235(max_sector_weight=1.5)
