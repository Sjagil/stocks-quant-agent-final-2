from __future__ import annotations
import numpy as np, pandas as pd
from .gem_feature_engine_v2_35_1 import component_score, safe_01

QUALITY={"roic":True,"fcf_margin":True,"gross_margin":True,"accrual_ratio":False,"net_debt_to_ebitda":False,"interest_coverage":True}
GROWTH={"revenue_growth_yoy":True,"eps_growth_yoy":True,"fcf_growth_yoy":True}
REVISIONS={"eps_revision":True,"earnings_surprise":True}
VALUE={"fcf_yield":True,"earnings_yield":True,"sales_yield":True}
MOMENTUM={"risk_adjusted_momentum_20":True,"relative_strength_20":True,"residual_momentum_20":True,"trend_regression_r2_20":True}
CATALYST={"news_weighted_sentiment":True,"news_source_diversity":True,"news_event_intensity":True}

def forecast_component(frame: pd.DataFrame) -> tuple[pd.Series,pd.Series]:
    idx=frame.index
    mean=pd.to_numeric(frame.get("forecast_mean",pd.Series(np.nan,index=idx)),errors="coerce")
    q10=pd.to_numeric(frame.get("forecast_q10",pd.Series(np.nan,index=idx)),errors="coerce")
    q90=pd.to_numeric(frame.get("forecast_q90",pd.Series(np.nan,index=idx)),errors="coerce")
    cost=pd.to_numeric(frame.get("expected_cost",pd.Series(0.0,index=idx)),errors="coerce").fillna(0.0)
    cal=pd.to_numeric(frame.get("calibration_score",pd.Series(0.5,index=idx)),errors="coerce").fillna(0.5).clip(0,1)
    net=mean-cost
    upside=(q90-cost).clip(lower=0)
    downside=(q10-cost).clip(upper=0).abs()
    asym=upside/(upside+downside+1e-12)
    positive=(net>0).astype(float)
    score=(0.45*asym+0.35*positive+0.20*cal).where(mean.notna() & q10.notna() & q90.notna())
    coverage=(mean.notna() & q10.notna() & q90.notna()).astype(float)
    return score.clip(0,1),coverage

def build_component_scores(frame: pd.DataFrame) -> pd.DataFrame:
    out=pd.DataFrame(index=frame.index)
    for name,spec in [("quality",QUALITY),("growth",GROWTH),("revisions",REVISIONS),("value",VALUE),("momentum",MOMENTUM),("catalyst",CATALYST)]:
        out[name],out[f"{name}_coverage"]=component_score(frame,spec)
    out["forecast"],out["forecast_coverage"]=forecast_component(frame)
    return out
__all__=["build_component_scores","forecast_component"]
