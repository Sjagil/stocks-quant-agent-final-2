from stocks.shadow.contracts_v2_37 import ShadowDecisionV237, ShadowSide
from stocks.shadow.idempotency_v2_37 import canonical_idempotency_key

def test_idempotency_stable_and_intent_sensitive():
    a=ShadowDecisionV237("D1","S","F","AAA",ShadowSide.BUY,1000,50,"2026-08-24T10:00:00Z")
    b=ShadowDecisionV237("D2","S","F","AAA",ShadowSide.BUY,2000,60,"2026-08-24T10:00:00Z")
    assert canonical_idempotency_key(a)==canonical_idempotency_key(b)
    c=ShadowDecisionV237("D3","S","F","AAA",ShadowSide.BUY,1000,50,"2026-08-24T10:00:00Z",intent="OTHER")
    assert canonical_idempotency_key(a)!=canonical_idempotency_key(c)
