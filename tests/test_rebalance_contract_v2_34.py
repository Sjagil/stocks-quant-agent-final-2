import pandas as pd
from stocks.portfolio.rebalance_contract_v2_34 import decide_rebalance
def test_rebalance_requires_material_improvement():
 cur=pd.Series({'a':.2,'b':.2}); tar=pd.Series({'a':.25,'b':.15}); assert decide_rebalance(cur,tar,current_utility=.1,target_utility=.2).status=='REBALANCE_SHADOW'; assert decide_rebalance(cur,tar,current_utility=.2,target_utility=.1).status=='HOLD_SHADOW'
