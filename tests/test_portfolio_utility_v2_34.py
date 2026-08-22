from stocks.portfolio.portfolio_diagnostics_v2_34 import PortfolioDiagnosticsV234
from stocks.portfolio.portfolio_utility_v2_34 import portfolio_utility

def d(es,turn,hhi): return PortfolioDiagnosticsV234(.02,.0001,.01,0,es,turn,hhi,2,1,0,0,{}, {}, {})
def test_utility_penalizes_tail_turnover_and_concentration(): assert portfolio_utility(d(.01,.02,.3)).score>portfolio_utility(d(.03,.2,.8)).score
