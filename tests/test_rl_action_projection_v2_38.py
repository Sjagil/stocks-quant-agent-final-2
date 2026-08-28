import pandas as pd
from stocks.rl.action_projection_v2_38 import project_portfolio_action

def test_projection_enforces_acceptance_caps_turnover_heat():
 ids=["A","B","C"]; raw=pd.Series([.9,.8,.7],index=ids); cur=pd.Series([.05,.05,0],index=ids); acc=pd.Series([True,True,False],index=ids); p=project_portfolio_action(raw,current_weights=cur,accepted_mask=acc,family={"A":"F","B":"F","C":"G"},cluster={"A":"K","B":"K","C":"Q"},stop_distance=pd.Series([.1,.1,.1],index=ids)); assert p.weights["C"]==0; assert p.gross_exposure<=.75; assert p.one_way_turnover<=.30; assert p.portfolio_heat<=.04; assert p.execution_authority=="NONE"
def test_acceptance_mask_required():
 import pytest
 with pytest.raises(ValueError): project_portfolio_action(pd.Series([.2],index=["A"]))
