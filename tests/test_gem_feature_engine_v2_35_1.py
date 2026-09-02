import pandas as pd
from stocks.research.gem_feature_engine_v2_35_1 import sector_relative_rank, component_score

def test_sector_relative_rank_and_component():
    f=pd.DataFrame({"sector":["A"]*3+["B"]*3,"x":[1,2,3,10,20,30],"y":[3,2,1,30,20,10]})
    r=sector_relative_rank(f,"x")
    assert r.iloc[2]>r.iloc[0] and r.iloc[5]>r.iloc[3]
    s,c=component_score(f,{"x":True,"y":False})
    assert c.eq(1).all() and s.iloc[2]>s.iloc[0]
