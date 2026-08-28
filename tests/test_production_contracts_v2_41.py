import pytest
from stocks.production.contracts_v2_41 import ProductionIntent, ExecutionMode


def test_modes_are_explicit():
    assert {m.value for m in ExecutionMode} == {"OBSERVE", "PAPER", "LIVE_CANARY"}


def test_production_intent_is_whole_share_only():
    x = ProductionIntent("a"*64, "spy", "BUY", 2, 100.0, 95.0, "test")
    assert x.symbol == "SPY" and x.quantity == 2
    with pytest.raises(ValueError):
        ProductionIntent("b"*64, "SPY", "BUY", 0.5, 100.0, 95.0, "test")
    with pytest.raises(ValueError):
        ProductionIntent("c"*64, "SPY", "SHORT", 1, 100.0, None, "test")


def test_production_intent_requires_sha256_id():
    with pytest.raises(ValueError):
        ProductionIntent("not-a-hash", "SPY", "BUY", 1, 100.0, 95.0, "test")
