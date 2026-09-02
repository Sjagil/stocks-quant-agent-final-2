from stocks.rl.policy_challengers_v2_38 import challenger_specs
def test_algorithm_roles():
 x={s.algorithm:s for s in challenger_specs()}; assert set(x)=={"PPO","SAC","MAPPO"}; assert x["PPO"].role=="PRIMARY_PORTFOLIO_CONTROLLER"; assert x["MAPPO"].centralized_critic
