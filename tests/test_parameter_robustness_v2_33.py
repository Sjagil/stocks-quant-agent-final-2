from stocks.research.parameter_robustness_v2_33 import parameter_neighborhood_robustness

def test_stable_neighborhood_scores_high():
 good=parameter_neighborhood_robustness(1,[.9,.85,.95,.8]); bad=parameter_neighborhood_robustness(1,[.1,.05,.2,.15])
 assert good.robustness_score>bad.robustness_score and good.cliff_fraction==0
