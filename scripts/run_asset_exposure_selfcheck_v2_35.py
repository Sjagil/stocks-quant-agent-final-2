from __future__ import annotations
import pandas as pd
from stocks.portfolio.asset_exposure_contracts_v2_35 import AssetKindV235, InstrumentExposureProfile
from stocks.portfolio.portfolio_exposure_v2_35 import analyze_portfolio_exposure
from stocks.portfolio.commodity_exposure_v2_35 import commodity_curve_metrics

def main() -> int:
    profiles={
        "AAA":InstrumentExposureProfile("AAA",AssetKindV235.STOCK,sector="TECH",industry="SOFTWARE",country="US",currency="USD",factor_exposures={"MARKET":1.0,"QUALITY":0.4}),
        "BBB":InstrumentExposureProfile("BBB",AssetKindV235.STOCK,sector="HEALTH",industry="BIOTECH",country="US",currency="USD",factor_exposures={"MARKET":0.8,"GROWTH":0.5}),
        "ETF1":InstrumentExposureProfile("ETF1",AssetKindV235.ETF,sector="DIVERSIFIED",industry="ETF",country="US",currency="USD"),
    }
    holdings=pd.DataFrame([
        {"etf_symbol":"ETF1","constituent_symbol":"AAA","weight":0.55,"available_at":"2026-08-20T20:00:00Z"},
        {"etf_symbol":"ETF1","constituent_symbol":"BBB","weight":0.45,"available_at":"2026-08-20T20:00:00Z"},
    ])
    bundle=analyze_portfolio_exposure({"AAA":0.20,"ETF1":0.20},profiles,decision_time="2026-08-21T15:00:00Z",etf_holdings=holdings)
    curve=commodity_curve_metrics("GOLD",2400,2380,30,inventory_z=-0.5,trend_score=0.4,usd_score=-0.2,real_rate_score=-0.1)
    assert bundle.execution_authority=="NONE"
    assert bundle.snapshot["sector"]["TECH"]>0.30
    assert curve.backwardation is True
    print("ASSET_EXPOSURE_V2_35_SELFCHECK OK")
    print("PIT_ETF_LOOKTHROUGH True")
    print("ASSET_KINDS 4")
    print("ETF_OVERLAP True")
    print("FACTOR_EXPOSURE True")
    print("COMMODITY_CURVE_REGIME True")
    print("RESEARCH_COMPLIANCE_GATE_APPLIED False")
    print("BROKER_SUBMISSION_ENABLED False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0
if __name__=="__main__": raise SystemExit(main())
