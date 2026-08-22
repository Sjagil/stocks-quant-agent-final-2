import pandas as pd
from stocks.portfolio.strategy_risk_budget_v2_34 import evidence_risk_budgets,portfolio_heat
def test_evidence_budget_prefers_better_strategy():
 mu=pd.Series({'a':.02,'b':.01}); b=evidence_risk_budgets(mu,validation_scores=pd.Series({'a':1,'b':.5}),stability_scores=pd.Series({'a':1,'b':.5}),liquidity_scores=pd.Series({'a':1,'b':1})); assert b['a']>b['b']; assert abs(b.sum()-1)<1e-12; assert abs(portfolio_heat(pd.Series({'a':.2}),pd.Series({'a':.05}))-.01)<1e-12
