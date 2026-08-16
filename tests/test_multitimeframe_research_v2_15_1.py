from __future__ import annotations

import numpy as np
import pandas as pd

from stocks.research.multitimeframe_strategy_factory import (
    TIMEFRAMES,
    align_multitimeframe_features,
    evaluate_multitimeframe_hypothesis,
    generate_multitimeframe_hypotheses,
)


def _frame(index: pd.DatetimeIndex, scale: float = 1.0) -> pd.DataFrame:
    n = len(index)
    close = 100.0 + np.linspace(0.0, 25.0 * scale, n)
    wave = 0.8 * np.sin(np.linspace(0.0, 35.0, n))
    close = close + wave
    return pd.DataFrame(
        {
            "open": close - 0.05,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.linspace(1_000_000, 1_500_000, n),
        },
        index=index,
    )


def _frames() -> dict[str, pd.DataFrame]:
    start = "2023-01-02 14:30"
    return {
        "15m": _frame(pd.date_range(start, periods=8000, freq="15min", tz="UTC")),
        "1h": _frame(pd.date_range(start, periods=2500, freq="1h", tz="UTC")),
        "2h": _frame(pd.date_range(start, periods=1400, freq="2h", tz="UTC")),
        "4h": _frame(pd.date_range(start, periods=900, freq="4h", tz="UTC")),
        "1d": _frame(pd.date_range("2020-01-02", periods=700, freq="1D", tz="UTC")),
        "1w": _frame(pd.date_range("2012-01-06", periods=700, freq="7D", tz="UTC")),
    }


def test_timeframe_chain_is_complete():
    assert TIMEFRAMES == ("15m", "1h", "2h", "4h", "1d", "1w")


def test_alignment_contains_all_timeframes():
    aligned = align_multitimeframe_features(_frames())
    for tf in TIMEFRAMES:
        assert any(column.startswith(f"{tf}_") for column in aligned.columns)


def test_higher_timeframe_is_lagged():
    frames = _frames()
    aligned = align_multitimeframe_features(frames)
    raw_1h = frames["1h"]["close"].ewm(span=20, adjust=False).mean()
    first_base_after_second_hour = frames["1h"].index[2]
    value = aligned.loc[first_base_after_second_hour, "1h_close"]
    # One-bar lag means at the third 1h timestamp, the joined value comes
    # from the prior completed 1h candle, not the current one.
    assert np.isclose(value, frames["1h"]["close"].iloc[1])


def test_entry_is_after_15m_decision_when_signal_exists():
    frames = _frames()
    h = next(
        item
        for item in generate_multitimeframe_hypotheses()
        if item.template == "mtf_momentum"
        and item.params["min_1h_roc20"] == 0.0
        and item.params["min_15m_roc5"] == 0.0
    )
    trades = evaluate_multitimeframe_hypothesis(h, frames)
    if not trades.empty:
        assert (
            pd.to_datetime(trades["entry_timestamp"], utc=True)
            > pd.to_datetime(trades["decision_timestamp"], utc=True)
        ).all()


def test_no_strategy_has_execution_authority():
    for item in generate_multitimeframe_hypotheses():
        assert item.as_record()["execution_authority"] == "NONE"
