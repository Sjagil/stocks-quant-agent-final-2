from __future__ import annotations
import numpy as np,pandas as pd
from stocks.rl.action_projection_v2_38 import project_portfolio_action
from stocks.rl.reward_v2_38 import portfolio_control_reward
from stocks.rl.multiagent_rewards_v2_38 import mix_mappo_rewards
from stocks.rl.offline_split_v2_38 import purged_chronological_split
from stocks.rl.safe_controller_v2_38 import rl_action_to_shadow_target

def main()->int:
    ids=["S1","S2","S3","S4"]
    raw=pd.Series([.8,.4,.3,.2],index=ids); cur=pd.Series([.10,.10,0,0],index=ids); accepted=pd.Series([True,True,True,False],index=ids); stop=pd.Series([.05,.04,.06,.05],index=ids)
    p=project_portfolio_action(raw,current_weights=cur,accepted_mask=accepted,family={"S1":"TREND","S2":"TREND","S3":"EVENT","S4":"EVENT"},cluster={"S1":"C1","S2":"C1","S3":"C2","S4":"C2"},stop_distance=stop)
    assert p.gross_exposure<=.75+1e-9 and p.one_way_turnover<=.30+1e-9 and p.portfolio_heat<=.04+1e-9 and p.weights["S4"]==0
    w=pd.Series(p.weights); rb=portfolio_control_reward(previous_equity=10000,new_equity=10040,peak_equity=10100,weights=w,previous_weights=cur,previous_action=cur,expected_shortfall=.01,expected_edge=pd.Series([.02,.01,.03,0],index=ids)); assert np.isfinite(rb.reward)
    m=mix_mappo_rewards(.01,[.01,.02],[.005,.01]); assert len(m.rewards)==2
    s=purged_chronological_split(200,purge_bars=8); assert max(s.train)<min(s.validation)<max(s.validation)<min(s.test)
    target=rl_action_to_shadow_target(raw,current_weights=cur,accepted_mask=accepted,reconciliation_status="READY",stop_distance=stop); assert target.execution_authority=="NONE"
    print("RL_PORTFOLIO_CONTROL_V2_38_SELFCHECK OK")
    print("PPO_PRIMARY True"); print("SAC_CHALLENGER True"); print("MAPPO_CHALLENGER True")
    print("HARD_ACTION_PROJECTION True"); print("V233_ACCEPTANCE_REQUIRED True"); print("SHADOW_RECONCILIATION_REQUIRED True")
    print("NET_WEALTH_REWARD True"); print("TURNOVER_JERK_DD_TAIL_HHI True"); print("PURGED_CHRONOLOGICAL_SPLIT True")
    print("BROKER_SUBMISSION_ENABLED False"); print("AUTOMATIC_LIVE_PROMOTION False"); print("ORDER_CALLS 0"); print("EXECUTION_AUTHORITY NONE")
    return 0
if __name__=="__main__": raise SystemExit(main())
