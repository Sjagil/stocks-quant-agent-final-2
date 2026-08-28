from datetime import datetime, timezone
from types import SimpleNamespace

from stocks.production.ibkr_adapter_v2_41 import IBKRBrokerV241


class FakeIB:
    def __init__(self):
        self.market_type = None
        self.kwargs = None

    def reqMarketDataType(self, value):
        self.market_type = value

    def reqHistoricalData(self, contract, **kwargs):
        self.kwargs = kwargs
        return [
            SimpleNamespace(
                date=datetime(2026, 8, 26, 13, 30, tzinfo=timezone.utc),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1234,
            ),
            SimpleNamespace(
                date=datetime(2026, 8, 26, 14, 30, tzinfo=timezone.utc),
                open=100.5,
                high=102.0,
                low=100.0,
                close=101.5,
                volume=1500,
            ),
        ]


def test_historical_bars_is_read_only_and_uses_rth():
    broker = object.__new__(IBKRBrokerV241)
    broker.cfg = {
        "broker": {"market_data_type": 1},
        "runtime": {"broker_snapshot_timeout_seconds": 8},
    }
    broker.readonly = True
    broker.write_calls = 0
    broker.ib = FakeIB()
    broker.stock_contract = lambda symbol: f"CONTRACT:{symbol}"

    out = broker.historical_bars(
        "SPY", duration="5 D", bar_size="1 hour", what_to_show="TRADES", use_rth=True
    )
    assert len(out) == 2
    assert list(out.columns) == ["open", "high", "low", "close", "volume"]
    assert str(out.index.tz) == "UTC"
    assert broker.ib.kwargs["useRTH"] is True
    assert broker.ib.kwargs["formatDate"] == 2
    assert broker.write_calls == 0
