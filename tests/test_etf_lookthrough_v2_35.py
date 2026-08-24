import pandas as pd
from stocks.portfolio.asset_exposure_contracts_v2_35 import AssetKindV235, InstrumentExposureProfile
from stocks.portfolio.etf_lookthrough_v2_35 import point_in_time_holdings, build_etf_lookthrough

def _profiles():
    return {
      "A":InstrumentExposureProfile("A",AssetKindV235.STOCK,sector="TECH",industry="SW",country="US",currency="USD",factor_exposures={"QUALITY":1}),
      "B":InstrumentExposureProfile("B",AssetKindV235.STOCK,sector="HEALTH",industry="BIO",country="US",currency="USD",factor_exposures={"QUALITY":0.2}),
    }

def test_pit_holdings_uses_latest_known_snapshot_only():
    f=pd.DataFrame([
      {"etf_symbol":"X","constituent_symbol":"A","weight":1.0,"available_at":"2026-08-01T00:00:00Z"},
      {"etf_symbol":"X","constituent_symbol":"B","weight":1.0,"available_at":"2026-08-30T00:00:00Z"},
    ])
    out=point_in_time_holdings(f,etf_symbol="X",decision_time="2026-08-15T00:00:00Z")
    assert list(out.constituent_symbol)==["A"]

def test_lookthrough_aggregates_exposure():
    f=pd.DataFrame([
      {"etf_symbol":"X","constituent_symbol":"A","weight":0.6,"available_at":"2026-08-01T00:00:00Z"},
      {"etf_symbol":"X","constituent_symbol":"B","weight":0.4,"available_at":"2026-08-01T00:00:00Z"},
    ])
    out=build_etf_lookthrough("X",f,_profiles(),decision_time="2026-08-15T00:00:00Z")
    assert abs(out.sector_exposure["TECH"]-0.6)<1e-12
    assert abs(out.factor_exposure["QUALITY"]-0.68)<1e-12
