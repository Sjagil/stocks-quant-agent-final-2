from stocks.shadow.contracts_v2_37 import ExitPolicyV237
from stocks.shadow.exits_v2_37 import evaluate_exit

def test_stop_take_trailing_time_and_strategy():
    p=ExitPolicyV237(stop_loss_pct=.03,take_profit_pct=.08,trailing_stop_pct=.04,max_holding_bars=20)
    assert evaluate_exit(entry_price=100,current_price=96,high_price=100,bars_held=2,policy=p).reason=="STOP_LOSS"
    assert evaluate_exit(entry_price=100,current_price=109,high_price=109,bars_held=2,policy=p).reason=="TAKE_PROFIT"
    assert evaluate_exit(entry_price=100,current_price=104,high_price=110,bars_held=5,policy=p).reason=="TRAILING_STOP"
    assert evaluate_exit(entry_price=100,current_price=101,high_price=102,bars_held=20,policy=p).reason=="TIME_EXIT"
    assert evaluate_exit(entry_price=100,current_price=101,high_price=102,bars_held=2,strategy_exit=True,policy=p).reason=="STRATEGY_EXIT"
