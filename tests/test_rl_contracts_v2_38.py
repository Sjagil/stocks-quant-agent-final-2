import pytest
from stocks.rl.control_contracts_v2_38 import PortfolioControlPolicyV238
def test_policy_cannot_grant_authority():
 with pytest.raises(ValueError): PortfolioControlPolicyV238(execution_authority="LIVE")
def test_policy_forbids_leverage():
 with pytest.raises(ValueError): PortfolioControlPolicyV238(leverage=True)
