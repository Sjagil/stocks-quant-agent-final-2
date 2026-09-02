from stocks.portfolio.validation_bridge_v2_34 import validated_strategy_ids
def test_only_unblocked_promoted_strategies_pass():
 rows=[{'strategy_id':'a','status':'PROMOTE_VALIDATION','blockers':[]},{'strategy_id':'b','status':'REJECT_OR_REWORK','blockers':['PBO']},{'strategy_id':'c','status':'PROMOTE_VALIDATION','blockers':['X']}]; assert validated_strategy_ids(rows)==('a',)
