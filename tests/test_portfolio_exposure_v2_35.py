import pandas as pd
from stocks.portfolio.asset_exposure_contracts_v2_35 import AssetKindV235, InstrumentExposureProfile
from stocks.portfolio.asset_exposure_engine_v2_35 import build_portfolio_exposure

def test_direct_and_etf_exposure():
    profiles={
      "A":InstrumentExposureProfile("A",AssetKindV235.STOCK,sector="TECH",industry="SW",country="US",currency="USD"),
      "B":InstrumentExposureProfile("B",AssetKindV235.STOCK,sector="HEALTH",industry="BIO",country="US",currency="USD"),
      "X":InstrumentExposureProfile("X",AssetKindV235.ETF,sector="DIVERSIFIED",industry="ETF",country="US",currency="USD"),
    }
    holdings=pd.DataFrame([
      {"etf_symbol":"X","constituent_symbol":"A","weight":0.5,"available_at":"2026-08-01T00:00:00Z"},
      {"etf_symbol":"X","constituent_symbol":"B","weight":0.5,"available_at":"2026-08-01T00:00:00Z"},
    ])
    out=build_portfolio_exposure({"A":0.2,"X":0.4},profiles,decision_time="2026-08-15T00:00:00Z",etf_holdings=holdings)
    assert abs(out.sector["TECH"]-0.4)<1e-12
    assert abs(out.cash_weight-0.4)<1e-12
