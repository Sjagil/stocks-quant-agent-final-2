import numpy as np,pandas as pd,pytest
from stocks.portfolio.portfolio_intelligence_v2_34 import build_portfolio_intelligence

def test_intelligence_builds_feasible_research_portfolio_without_cvxpy():
 rng=np.random.default_rng(9); base=rng.normal(.0002,.008,180); r=pd.DataFrame({'a':base+rng.normal(.0002,.004,180),'b':.2*base+rng.normal(.0003,.006,180),'c':rng.normal(.00025,.006,180)}); meta=pd.DataFrame({'family':['trend','factor','news'],'cluster':['m','r','e'],'validation_score':[.9,.95,.8],'stability_score':[.9,.9,.8],'liquidity_score':[.9,.9,.8],'stop_loss_fraction':[.04,.05,.04]},index=r.columns); out=build_portfolio_intelligence(r,r.mean(),meta,validated_ids=list(r.columns),include_convex=False); assert out.status=='RESEARCH_PORTFOLIO_READY'; assert out.selected_method in {'HRP','ROBUST_EDGE_WEIGHTED'}; assert sum(out.selected_weights.values())<=.75+1e-12; assert out.execution_authority=='NONE'


def test_v233_validation_ids_are_mandatory():
 r=pd.DataFrame({'a':[.01]*30}); meta=pd.DataFrame({'family':['f'],'cluster':['c'],'validation_score':[1.0],'stability_score':[1.0],'liquidity_score':[1.0],'stop_loss_fraction':[.04]},index=['a'])
 with pytest.raises(ValueError,match='validated_ids'):
  build_portfolio_intelligence(r,pd.Series({'a':.01}),meta,validated_ids=[],include_convex=False)
