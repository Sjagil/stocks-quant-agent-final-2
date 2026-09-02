import pandas as pd
from stocks.research.gem_diversity_v2_35_1 import diversify_gem_shortlist
from stocks.research.gem_contracts_v2_35_1 import GemScreenerPolicyV2351

def test_diversity_caps_sector_and_industry():
    f=pd.DataFrame([{"symbol":f"S{i}","sector":"A" if i<5 else "B","industry":"X" if i<5 else "Y","gem_score":100-i} for i in range(8)])
    out=diversify_gem_shortlist(f,limit=6,policy=GemScreenerPolicyV2351(max_per_sector=2,max_per_industry=2))
    assert out.groupby("sector").size().max()<=2
    assert out.groupby("industry").size().max()<=2
