import numpy as np
from stocks.research.multiple_testing_v2_33 import bonferroni,holm,benjamini_hochberg,effective_independent_trials

def test_corrections_are_bounded_and_conservative():
 p=[0.001,0.01,0.2]
 for x in (bonferroni(p),holm(p),benjamini_hochberg(p)):
  assert np.all((x>=0)&(x<=1))
 corr=np.array([[1,.9,0],[.9,1,0],[0,0,1]],float)
 assert 1<effective_independent_trials(corr)<3
