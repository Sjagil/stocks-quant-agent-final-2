import numpy as np
from stocks.research.sharpe_significance_v2_33 import expected_maximum_sharpe, sample_sharpe_statistics

def test_sharpe_significance_improves_with_positive_edge():
 rng=np.random.default_rng(1); r=rng.normal(0.002,0.01,300); s=sample_sharpe_statistics(r)
 assert s['observations']==300 and s['psr_vs_zero']>0.9
 assert expected_maximum_sharpe([0.0,0.1,0.2,0.15])>=0.1
