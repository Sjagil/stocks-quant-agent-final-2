from stocks.research.continuous.bayesian_shrinkage_v2_39 import shrink_mean

def test_shrinkage_pulls_small_sample_to_prior():
 a=shrink_mean([100],prior_mean=0,prior_strength=20); b=shrink_mean([100]*100,prior_mean=0,prior_strength=20)
 assert 0<a.posterior_mean<b.posterior_mean<100
