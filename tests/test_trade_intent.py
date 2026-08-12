from datetime import datetime, timezone

import pytest

from stocks.contracts import IntentAction, TradeIntent


def test_trade_intent_cannot_gain_authority():
    with pytest.raises(ValueError):
        TradeIntent(
            created_at=datetime.now(timezone.utc),
            symbol="NVDA",
            action=IntentAction.INCREASE,
            target_weight=0.10,
            target_notional_eur=187.0,
            confidence=0.7,
            execution_authority="LIVE",
        )
