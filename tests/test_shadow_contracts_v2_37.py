import pytest
from stocks.shadow.contracts_v2_37 import ShadowDecisionV237, ShadowSide

def test_decision_requires_aware_time_and_none_authority():
    d=ShadowDecisionV237("D","S","F","abc",ShadowSide.BUY,1000,50,"2026-08-24T10:00:00Z")
    assert d.symbol=="ABC" and d.execution_authority=="NONE"
    with pytest.raises(ValueError):
        ShadowDecisionV237("D","S","F","ABC",ShadowSide.BUY,1000,50,"2026-08-24T10:00:00")
