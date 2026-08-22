import json
from pathlib import Path
from stocks.portfolio.portfolio_constraints_v2_34 import PortfolioConstraintPolicyV234

def test_safety_and_compliance_deferred():
 cfg=json.loads(Path('config/portfolio_intelligence_v2_34.json').read_text()); assert cfg['execution_authority']=='NONE'; assert cfg['research_compliance_gate_applied'] is False; assert cfg['broker_submission_enabled'] is False; assert cfg['automatic_live_promotion'] is False; p=PortfolioConstraintPolicyV234(); assert p.execution_authority=='NONE' and p.research_compliance_gate_applied is False
