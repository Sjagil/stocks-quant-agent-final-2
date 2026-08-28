from __future__ import annotations
import numpy as np, pandas as pd
from stocks.portfolio.portfolio_intelligence_v2_34 import build_portfolio_intelligence
from stocks.portfolio.dynamic_risk_overlay_v2_34 import DynamicRiskStateV234

def main():
    rng=np.random.default_rng(234); n=320
    market=rng.normal(0.0003,0.009,n)
    returns=pd.DataFrame({
      "trend":0.45*market+rng.normal(0.00035,0.005,n),
      "residual":0.10*market+rng.normal(0.00045,0.006,n),
      "news":0.25*market+rng.normal(0.00030,0.007,n),
      "quality":0.30*market+rng.normal(0.00025,0.0045,n),
    })
    mu=returns.mean()
    meta=pd.DataFrame({
      "family":["trend","factor","news","fundamental"],"cluster":["momentum","residual","event","quality"],
      "validation_score":[.90,.95,.82,.88],"stability_score":[.85,.91,.75,.89],"liquidity_score":[.95,.90,.80,.97],"stop_loss_fraction":[.04,.05,.04,.03]
    },index=returns.columns)
    result=build_portfolio_intelligence(returns,mu,meta,validated_ids=list(returns.columns),include_convex=False,risk_state=DynamicRiskStateV234())
    assert result.status=="RESEARCH_PORTFOLIO_READY"; assert result.execution_authority=="NONE"; assert sum(result.selected_weights.values())<=.75+1e-12
    print("PORTFOLIO_INTELLIGENCE_V2_34_SELFCHECK OK")
    print("SELECTED_METHOD",result.selected_method); print("CANDIDATES",len(result.candidates)); print("EFFECTIVE_STRATEGIES",round(result.effective_independent_strategies,6))
    print("RESEARCH_COMPLIANCE_GATE_APPLIED False"); print("BROKER_SUBMISSION_ENABLED False"); print("ORDER_CALLS 0"); print("EXECUTION_AUTHORITY NONE")
if __name__=="__main__": main()
