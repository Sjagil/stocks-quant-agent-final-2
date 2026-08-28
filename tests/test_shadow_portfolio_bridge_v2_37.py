from types import SimpleNamespace
import pandas as pd
from stocks.shadow.portfolio_bridge_v2_37 import build_shadow_plan_from_rebalance

def test_portfolio_bridge_requires_net_positive_rebalance():
    cur=pd.Series({"AAA":0.1}); tar=pd.Series({"AAA":0.2})
    hold=SimpleNamespace(status="HOLD_SHADOW_COST_BLOCKED",blockers=("COST",))
    assert build_shadow_plan_from_rebalance(cur,tar,portfolio_value=100000,rebalance_projection=hold,
        strategy_id_by_symbol={"AAA":"S"},family_by_symbol={"AAA":"F"},gross_edge_bps_by_symbol={"AAA":100},decision_time="2026-08-24T10:00:00Z").status=="HOLD_SHADOW"
    go=SimpleNamespace(status="REBALANCE_SHADOW_NET_POSITIVE",blockers=())
    plan=build_shadow_plan_from_rebalance(cur,tar,portfolio_value=100000,rebalance_projection=go,
        strategy_id_by_symbol={"AAA":"S"},family_by_symbol={"AAA":"F"},gross_edge_bps_by_symbol={"AAA":100},decision_time="2026-08-24T10:00:00Z")
    assert plan.status=="PLAN_READY" and len(plan.decisions)==1
