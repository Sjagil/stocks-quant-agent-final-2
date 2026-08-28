from stocks.rl.multiagent_rewards_v2_38 import mix_mappo_rewards
def test_mappo_reward_mix():
 r=mix_mappo_rewards(1,[2,0],[1,-1]); assert r.rewards[0]>r.rewards[1]; assert r.execution_authority=="NONE"
