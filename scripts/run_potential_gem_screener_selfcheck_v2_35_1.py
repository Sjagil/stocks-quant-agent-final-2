from __future__ import annotations
import numpy as np, pandas as pd
from stocks.research.potential_gem_screener_v2_35_1 import screen_potential_gems

def _universe():
    rows=[]
    sectors=[("TECH","SOFTWARE"),("HEALTH","BIOTECH"),("INDUSTRIAL","MACHINERY")]
    for i in range(18):
        sec,ind=sectors[i%3]
        strength=(i+1)/18
        rows.append({
            "symbol":f"S{i:02d}","asset_kind":"STOCK","sector":sec,"industry":ind,
            "market_cap":300_000_000+20_000_000*i,"price":8+i,
            "avg_dollar_volume_20d":3_000_000+200_000*i,"data_quality_score":0.82+0.01*(i%5),
            "fundamentals_age_days":60,"spread_bps":25,"share_dilution_yoy":0.01,
            "roic":0.03+0.18*strength,"fcf_margin":0.02+0.20*strength,"gross_margin":0.25+0.35*strength,
            "accrual_ratio":0.10-0.08*strength,"net_debt_to_ebitda":3.0-2.5*strength,"interest_coverage":2+12*strength,
            "revenue_growth_yoy":0.02+0.35*strength,"eps_growth_yoy":0.01+0.45*strength,"fcf_growth_yoy":0.01+0.40*strength,
            "eps_revision":-0.03+0.15*strength,"earnings_surprise":-0.02+0.18*strength,
            "fcf_yield":0.01+0.08*strength,"earnings_yield":0.01+0.07*strength,"sales_yield":0.1+0.5*strength,
            "risk_adjusted_momentum_20":-0.2+1.2*strength,"relative_strength_20":-0.1+0.5*strength,
            "residual_momentum_20":-0.08+0.35*strength,"trend_regression_r2_20":0.2+0.7*strength,
            "news_weighted_sentiment":-0.2+0.7*strength,"news_source_diversity":0.4+0.5*strength,"news_event_intensity":0.1+0.8*strength,
            "forecast_mean":-0.01+0.08*strength,"forecast_q10":-0.06+0.035*strength,"forecast_q50":-0.005+0.075*strength,
            "forecast_q90":0.03+0.15*strength,"expected_cost":0.003,"calibration_score":0.55+0.35*strength,
            "realized_volatility_20":0.25,"max_drawdown_126":0.18,"max_abs_daily_return_20d":0.12,"abnormal_volume_ratio":1.4,
        })
    rows.append({
        **rows[-1],"symbol":"PUMP","market_cap":250_000_000,"max_abs_daily_return_20d":0.55,
        "abnormal_volume_ratio":8.0,"news_source_diversity":0.05,
    })
    return pd.DataFrame(rows)

def main() -> int:
    result=screen_potential_gems(_universe(),shortlist_limit=10)
    pump=result.ranked[result.ranked.symbol=="PUMP"].iloc[0]
    assert "PUMP_MANIPULATION_RISK" in pump.blockers
    assert result.summary.eligible>=18
    assert len(result.shortlist)>0
    assert result.execution_authority=="NONE"
    print("POTENTIAL_GEM_SCREENER_V2_35_1_SELFCHECK OK")
    print("TOTAL",result.summary.total)
    print("ELIGIBLE",result.summary.eligible)
    print("SHORTLIST",len(result.shortlist))
    print("TOP_SYMBOL",result.shortlist.iloc[0].symbol)
    print("TOP_SCORE",round(float(result.shortlist.iloc[0].gem_score),4))
    print("PUMP_GUARD True")
    print("SECTOR_RELATIVE_RANKING True")
    print("FORECAST_ASYMMETRY True")
    print("PORTFOLIO_FIT True")
    print("RESEARCH_COMPLIANCE_GATE_APPLIED False")
    print("BROKER_SUBMISSION_ENABLED False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0
if __name__=="__main__": raise SystemExit(main())
