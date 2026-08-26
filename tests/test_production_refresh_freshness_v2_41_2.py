from types import SimpleNamespace

import pandas as pd

from stocks.production.current_session_data_v2_41_2 import cross_provider_close_check
import stocks.production.data_refresh_v2_41_2 as bridge


def _f(times, px=100.0):
    return pd.DataFrame(
        {
            "open": [px] * len(times),
            "high": [px + 1] * len(times),
            "low": [px - 1] * len(times),
            "close": [px] * len(times),
            "volume": [100] * len(times),
        },
        index=pd.to_datetime(times, utc=True),
    )


def test_no_overlap_is_fail_closed():
    a = _f(["2026-08-25 13:30:00+00:00"])
    b = _f(["2026-08-26 13:30:00+00:00"])
    out = cross_provider_close_check(
        a, b, minimum_overlap_bars=3, maximum_close_disagreement_bps=50
    )
    assert not out.passed
    assert out.reason == "CROSS_PROVIDER_OVERLAP_INSUFFICIENT"


class _Cross:
    passed = True
    overlap_bars = 4
    max_close_disagreement_bps = 1.0
    def to_dict(self): return {"passed": True, "overlap_bars": 4}


class _Session:
    def to_dict(self): return {"market_open_now": True}


class _Broker:
    write_calls = 0
    def __init__(self, cfg, readonly=True): self.readonly = readonly
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def historical_bars(self, *args, **kwargs):
        return _f([
            "2026-08-25 13:30:00+00:00",
            "2026-08-25 14:30:00+00:00",
            "2026-08-25 15:30:00+00:00",
            "2026-08-25 16:30:00+00:00",
        ])


def _cfg(tmp_path):
    return {
        "data": {
            "symbols": ["SPY"],
            "exchange": "US",
            "timeframe": "1h",
            "provider_root": "final",
            "finalized_history_root": "history",
            "bar_close_lag_seconds": 120,
            "ibkr_history_duration": "5 D",
            "ibkr_history_bar_size": "1 hour",
            "ibkr_history_what_to_show": "TRADES",
            "ibkr_history_use_rth": True,
            "minimum_cross_provider_overlap_bars": 3,
            "maximum_cross_provider_close_disagreement_bps": 50.0,
            "freshness_tolerance_minutes": 150,
            "market_calendar": "NYSE",
        },
        "broker": {},
    }


def _patch_refresh_dependencies(monkeypatch, passed):
    hist = _f([
        "2026-08-25 13:30:00+00:00",
        "2026-08-25 14:30:00+00:00",
        "2026-08-25 15:30:00+00:00",
        "2026-08-25 16:30:00+00:00",
    ])
    monkeypatch.setattr(bridge, "_seed_finalized_history_once", lambda *a, **k: [])
    monkeypatch.setattr(bridge, "refresh_finalized_history_v241", lambda *a, **k: {"status": "SUCCEEDED"})
    monkeypatch.setattr(bridge, "read_canonical_parquet", lambda *a, **k: (hist, {"source": "EODHD"}))
    monkeypatch.setattr(bridge, "IBKRBrokerV241", _Broker)
    monkeypatch.setattr(bridge, "cross_provider_close_check", lambda *a, **k: _Cross())
    monkeypatch.setattr(bridge, "closed_latest_session_bars", lambda *a, **k: (hist.tail(1), _Session()))
    monkeypatch.setattr(bridge, "merge_overlay", lambda historical, overlay: historical)
    monkeypatch.setattr(bridge, "write_canonical_parquet", lambda *a, **k: None)
    monkeypatch.setattr(
        bridge,
        "check_file_freshness",
        lambda *a, **k: SimpleNamespace(
            passed=passed,
            reason="FRESH" if passed else "STALE_DURING_SESSION",
            to_dict=lambda: {"passed": passed, "reason": "FRESH" if passed else "STALE_DURING_SESSION"},
        ),
    )


def test_top_level_refresh_fails_when_final_dataset_stale(tmp_path, monkeypatch):
    _patch_refresh_dependencies(monkeypatch, passed=False)
    out = bridge.refresh_provider_fabric(tmp_path, _cfg(tmp_path))
    assert out["status"] == "FAILED"
    assert out["failures"] == 1
    assert out["symbols"][0]["status"] == "FAILED"
    assert "PRODUCTION_DATA_STALE" in out["symbols"][0]["reason"]


def test_readonly_bridge_requires_zero_write_calls(tmp_path, monkeypatch):
    _patch_refresh_dependencies(monkeypatch, passed=True)

    class BadBroker(_Broker):
        write_calls = 1

    monkeypatch.setattr(bridge, "IBKRBrokerV241", BadBroker)
    out = bridge.refresh_provider_fabric(tmp_path, _cfg(tmp_path))
    assert out["status"] == "FAILED"
    assert out["reason"] == "READONLY_IBKR_DATA_BRIDGE_RECORDED_WRITE_CALLS"
