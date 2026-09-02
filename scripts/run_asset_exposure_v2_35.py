from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from stocks.portfolio.asset_exposure_contracts_v2_35 import AssetKindV235, InstrumentExposureProfile, ExposurePolicyV235
from stocks.portfolio.portfolio_exposure_v2_35 import analyze_portfolio_exposure

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,help="JSON containing weights/profiles and optional holdings_csv")
    p.add_argument("--output",default="artifacts/asset_exposure_v2_35/exposure.json")
    args=p.parse_args()
    payload=json.loads(Path(args.input).read_text())
    profiles={}
    for row in payload["profiles"]:
        profiles[str(row["symbol"]).upper()]=InstrumentExposureProfile(
            symbol=row["symbol"],asset_kind=AssetKindV235(row["asset_kind"]),
            sector=row.get("sector","UNKNOWN"),industry=row.get("industry","UNKNOWN"),
            country=row.get("country","UNKNOWN"),currency=row.get("currency","UNKNOWN"),
            factor_exposures=row.get("factor_exposures",{}),commodity_exposures=row.get("commodity_exposures",{}),
            data_asof=row.get("data_asof"),source=row.get("source","INPUT"),
        )
    holdings=pd.read_csv(payload["holdings_csv"]) if payload.get("holdings_csv") else None
    result=analyze_portfolio_exposure(payload["weights"],profiles,decision_time=payload["decision_time"],etf_holdings=holdings)
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result.as_dict(),indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("ASSET_EXPOSURE_V2_35",result.constraints["status"])
    print("OUTPUT",out)
    print("EXECUTION_AUTHORITY",result.execution_authority)
    return 0
if __name__=="__main__": raise SystemExit(main())
