import pandas as pd
from stocks.portfolio.portfolio_constraints_v2_34 import *

def test_projection_enforces_strategy_group_and_turnover_caps():
 raw=pd.Series({'a':.5,'b':.4,'c':.3}); meta=pd.DataFrame({'family':['f','f','g'],'cluster':['x','x','y']},index=raw.index); prev=pd.Series({'a':.1,'b':.1,'c':.1}); p=PortfolioConstraintPolicyV234(max_turnover=.1); out=project_strategy_weights(raw,meta,previous_weights=prev,policy=p); assert_projection_constraints(out,meta,p); assert out.turnover<=.10000001


def test_projection_scales_down_when_heat_exceeds_normal_cap():
 raw=pd.Series({'a':.5,'b':.5}); meta=pd.DataFrame({'family':['f','g'],'cluster':['x','y'],'stop_loss_fraction':[.20,.20]},index=raw.index); out=project_strategy_weights(raw,meta); assert_projection_constraints(out,meta); assert sum(out.weights.values())<=.20+1e-10
