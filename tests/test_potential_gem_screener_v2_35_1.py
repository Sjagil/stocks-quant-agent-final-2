import pandas as pd
from stocks.research.potential_gem_screener_v2_35_1 import screen_potential_gems

def universe():
    rows=[]
    for i in range(12):
      x=(i+1)/12
      rows.append({"symbol":f"S{i}","asset_kind":"STOCK","sector":["TECH","HEALTH","IND"][i%3],"industry":["SW","BIO","MACH"][i%3],
      "market_cap":400e6,"price":12,"avg_dollar_volume_20d":5e6,"data_quality_score":0.9,"fundamentals_age_days":60,"spread_bps":20,
      "share_dilution_yoy":0.01,"roic":x,"fcf_margin":x,"gross_margin":x,"accrual_ratio":1-x,"net_debt_to_ebitda":2-x,"interest_coverage":2+10*x,
      "revenue_growth_yoy":x,"eps_growth_yoy":x,"fcf_growth_yoy":x,"eps_revision":x,"earnings_surprise":x,"fcf_yield":x,"earnings_yield":x,"sales_yield":x,
      "risk_adjusted_momentum_20":x,"relative_strength_20":x,"residual_momentum_20":x,"trend_regression_r2_20":x,
      "news_weighted_sentiment":x,"news_source_diversity":0.5+0.4*x,"news_event_intensity":x,
      "forecast_mean":0.01+0.05*x,"forecast_q10":-0.05+0.02*x,"forecast_q90":0.05+0.10*x,"expected_cost":0.002,"calibration_score":0.7,
      "realized_volatility_20":0.25,"max_drawdown_126":0.15,"max_abs_daily_return_20d":0.1,"abnormal_volume_ratio":1.2})
    return pd.DataFrame(rows)

def test_screener_ranks_and_shortlists():
    r=screen_potential_gems(universe(),shortlist_limit=6)
    assert r.summary.total==12 and r.summary.eligible==12
    assert len(r.shortlist)>0
    assert r.ranked.iloc[0].gem_score>=r.ranked.iloc[-1].gem_score
    assert r.execution_authority=="NONE"
