from stocks.rl.evaluation_v2_38 import evaluate_rl_path
def test_eval_metrics():
 x=evaluate_rl_path([.01,-.005,.004],[.1,.2,.1],[.2,.25,.22]); assert x.observations==3; assert x.max_drawdown>=0; assert x.execution_authority=="NONE"
