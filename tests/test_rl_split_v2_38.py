from stocks.rl.offline_split_v2_38 import purged_chronological_split
def test_purged_split_is_chronological():
 s=purged_chronological_split(200,purge_bars=5); assert max(s.train)<min(s.validation)<max(s.validation)<min(s.test); assert s.random_shuffle is False
