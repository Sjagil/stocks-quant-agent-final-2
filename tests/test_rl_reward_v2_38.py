import pandas as pd
from stocks.rl.reward_v2_38 import portfolio_control_reward

def test_reward_penalizes_bad_risk_path():
 w=pd.Series([.3,.2],index=["A","B"]); p=pd.Series([.2,.2],index=["A","B"])
 good=portfolio_control_reward(previous_equity=10000,new_equity=10100,peak_equity=10100,weights=w,previous_weights=p,expected_shortfall=.005)
 bad=portfolio_control_reward(previous_equity=10000,new_equity=9900,peak_equity=10200,weights=w,previous_weights=p,expected_shortfall=.05)
 assert good.reward>bad.reward
