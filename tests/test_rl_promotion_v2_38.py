from stocks.rl.evaluation_v2_38 import RLEvaluationV238
from stocks.rl.promotion_gates_v2_38 import evaluate_rl_challenger
def test_promotion_is_challenger_only():
 b=RLEvaluationV238(.10,1,.10,.03,.10,.2,100); c=RLEvaluationV238(.12,1.1,.10,.03,.11,.2,100); d=evaluate_rl_challenger(c,b); assert d.status=="ELIGIBLE_FORWARD_SHADOW_CHALLENGER"; assert d.challenger_only and not d.automatic_live_promotion
