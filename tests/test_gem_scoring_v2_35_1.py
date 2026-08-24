import pandas as pd
from stocks.research.gem_contracts_v2_35_1 import GemScreenerPolicyV2351
from stocks.research.gem_scoring_v2_35_1 import weighted_geometric_components, portfolio_fit_score

def test_geometric_balance_penalizes_one_weak_dimension():
    c=pd.DataFrame([{"quality":0.9,"quality_coverage":1,"growth":0.9,"growth_coverage":1,"revisions":0.9,"revisions_coverage":1,
      "value":0.9,"value_coverage":1,"momentum":0.9,"momentum_coverage":1,"forecast":0.9,"forecast_coverage":1,"catalyst":0.9,"catalyst_coverage":1},
      {"quality":0.9,"quality_coverage":1,"growth":0.05,"growth_coverage":1,"revisions":0.9,"revisions_coverage":1,
      "value":0.9,"value_coverage":1,"momentum":0.9,"momentum_coverage":1,"forecast":0.9,"forecast_coverage":1,"catalyst":0.9,"catalyst_coverage":1}])
    s=weighted_geometric_components(c,GemScreenerPolicyV2351())
    assert s.iloc[0]>s.iloc[1]

def test_portfolio_fit_rewards_headroom():
    f=pd.DataFrame({"sector":["TECH","HEALTH"],"industry":["SW","BIO"]})
    s=portfolio_fit_score(f,current_sector_exposure={"TECH":0.34,"HEALTH":0.05},current_industry_exposure={"SW":0.24,"BIO":0.02})
    assert s.iloc[1]>s.iloc[0]
