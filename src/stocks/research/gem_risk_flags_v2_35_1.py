from __future__ import annotations
import numpy as np, pandas as pd
from .gem_contracts_v2_35_1 import GemScreenerPolicyV2351

def hard_blockers(row: pd.Series, policy: GemScreenerPolicyV2351) -> tuple[str,...]:
    b=[]
    if str(row.get("asset_kind","STOCK")).upper()!="STOCK": b.append("NOT_COMMON_STOCK")
    def num(k,default=np.nan):
        try: return float(row.get(k,default))
        except Exception: return float("nan")
    market=num("market_cap"); price=num("price"); adv=num("avg_dollar_volume_20d"); quality=num("data_quality_score")
    age=num("fundamentals_age_days"); spread=num("spread_bps"); dilution=num("share_dilution_yoy",0.0)
    if not np.isfinite(market) or market<policy.min_market_cap: b.append("MARKET_CAP_TOO_LOW")
    if not np.isfinite(price) or price<policy.min_price: b.append("PRICE_TOO_LOW")
    if not np.isfinite(adv) or adv<policy.min_avg_dollar_volume_20d: b.append("LIQUIDITY_TOO_LOW")
    if not np.isfinite(quality) or quality<policy.min_data_quality_score: b.append("DATA_QUALITY_LOW")
    if not np.isfinite(age) or age>policy.max_fundamentals_age_days: b.append("FUNDAMENTALS_STALE")
    if np.isfinite(spread) and spread>policy.max_spread_bps: b.append("SPREAD_TOO_WIDE")
    if np.isfinite(dilution) and dilution>policy.max_dilution_yoy: b.append("DILUTION_EXTREME")
    move=abs(num("max_abs_daily_return_20d",0.0)); volume=num("abnormal_volume_ratio",1.0); diversity=num("news_source_diversity",0.0)
    if move>=policy.hard_pump_return and volume>=policy.hard_pump_volume_ratio and diversity<policy.min_news_diversity_for_extreme_move:
        b.append("PUMP_MANIPULATION_RISK")
    return tuple(b)

def risk_penalty(frame: pd.DataFrame) -> pd.Series:
    idx=frame.index
    vol=pd.to_numeric(frame.get("realized_volatility_20",pd.Series(0.25,index=idx)),errors="coerce").fillna(0.25)
    dd=pd.to_numeric(frame.get("max_drawdown_126",pd.Series(0.20,index=idx)),errors="coerce").fillna(0.20).abs()
    spread=pd.to_numeric(frame.get("spread_bps",pd.Series(20,index=idx)),errors="coerce").fillna(20)
    dilution=pd.to_numeric(frame.get("share_dilution_yoy",pd.Series(0,index=idx)),errors="coerce").fillna(0).clip(lower=0)
    leverage=pd.to_numeric(frame.get("net_debt_to_ebitda",pd.Series(1,index=idx)),errors="coerce").fillna(1).clip(lower=0)
    pump_move=pd.to_numeric(frame.get("max_abs_daily_return_20d",pd.Series(0,index=idx)),errors="coerce").fillna(0).abs()
    pump_vol=pd.to_numeric(frame.get("abnormal_volume_ratio",pd.Series(1,index=idx)),errors="coerce").fillna(1)
    penalty=(0.20*(vol/0.80).clip(0,1)+0.20*(dd/0.60).clip(0,1)+0.15*(spread/100).clip(0,1)+
             0.20*(dilution/0.30).clip(0,1)+0.15*(leverage/6).clip(0,1)+0.10*((pump_move/0.40)*(pump_vol/6)).clip(0,1))
    return penalty.clip(0,0.85)

def liquidity_quality(frame: pd.DataFrame) -> pd.Series:
    adv=pd.to_numeric(frame["avg_dollar_volume_20d"],errors="coerce").clip(lower=1)
    spread=pd.to_numeric(frame.get("spread_bps",pd.Series(20,index=frame.index)),errors="coerce").fillna(20)
    adv_score=((np.log10(adv)-6.0)/2.0).clip(0,1)
    spread_score=(1-spread/100).clip(0,1)
    return (0.7*adv_score+0.3*spread_score).clip(0,1)
__all__=["hard_blockers","liquidity_quality","risk_penalty"]
