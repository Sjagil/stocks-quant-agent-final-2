import pandas as pd
from stocks.research.gem_risk_flags_v2_35_1 import hard_blockers
from stocks.research.gem_contracts_v2_35_1 import GemScreenerPolicyV2351

def base():
    return pd.Series({"asset_kind":"STOCK","market_cap":300e6,"price":10,"avg_dollar_volume_20d":3e6,
      "data_quality_score":0.9,"fundamentals_age_days":90,"spread_bps":20,"share_dilution_yoy":0.02,
      "max_abs_daily_return_20d":0.1,"abnormal_volume_ratio":1.2,"news_source_diversity":0.6})

def test_pump_guard():
    x=base(); x["max_abs_daily_return_20d"]=0.5; x["abnormal_volume_ratio"]=8; x["news_source_diversity"]=0.1
    assert "PUMP_MANIPULATION_RISK" in hard_blockers(x,GemScreenerPolicyV2351())

def test_bad_liquidity_blocks():
    x=base(); x["avg_dollar_volume_20d"]=1000
    assert "LIQUIDITY_TOO_LOW" in hard_blockers(x,GemScreenerPolicyV2351())
