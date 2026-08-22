import pandas as pd
from stocks.portfolio.portfolio_attribution_v2_34 import attribute_period
def test_attribution_reconciles_gross_and_cost_drag():
 w=pd.Series({'a':.2,'b':.3}); r=pd.Series({'a':.1,'b':-.02}); m=pd.DataFrame({'family':['x','y']},index=w.index); a=attribute_period(w,r,m,turnover=.1,estimated_cost_bps=10); assert abs(a.gross_return-sum(a.strategy_contribution.values()))<1e-12; assert a.net_return<a.gross_return
