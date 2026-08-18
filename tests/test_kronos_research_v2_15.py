from __future__ import annotations

import numpy as np
import pandas as pd

from stocks.research.kronos_strategy_factory import (
    evaluate_kronos_hypothesis,
    generate_kronos_hypotheses,
    trade_metrics,
)


def bars(rows: int = 1200) -> pd.DataFrame:
    index = pd.date_range(
        "2024-01-02 14:30",
        periods=rows,
        freq="h",
        tz="UTC",
    )
    trend = np.linspace(100.0, 150.0, rows)
    wave = 2.0 * np.sin(
        np.linspace(0.0, 50.0, rows)
    )
    close = trend + wave
    return pd.DataFrame(
        {
            "open": close - 0.1,
            "high": close + 0.8,
            "low": close - 0.7,
            "close": close,
            "volume": np.linspace(
                1_000_000,
                2_000_000,
                rows,
            ),
        },
        index=index,
    )


def forecasts(frame: pd.DataFrame) -> pd.DataFrame:
    decisions = np.arange(
        300,
        len(frame) - 8,
        8,
    )
    return pd.DataFrame(
        {
            "decision_index": decisions,
            "decision_timestamp": frame.index[
                decisions
            ],
            "decision_close": frame[
                "close"
            ].iloc[decisions].to_numpy(),
            "forecast_end_timestamp": frame.index[
                decisions + 4
            ],
            "lookback": 256,
            "pred_len": 4,
            "kronos_terminal_return": 0.01,
            "kronos_mean_return": 0.008,
            "kronos_max_upside": 0.02,
            "kronos_min_downside": -0.005,
            "kronos_forecast_vol": 0.003,
        }
    )


def test_hypothesis_factory_has_multiple_families():
    hypotheses = generate_kronos_hypotheses()
    families = {
        item.family
        for item in hypotheses
    }
    assert len(hypotheses) >= 25
    assert {
        "KRONOS_DIRECTION",
        "KRONOS_TREND",
        "KRONOS_PULLBACK",
        "KRONOS_BREAKOUT",
        "KRONOS_ASYMMETRY",
    }.issubset(families)


def test_entry_is_strictly_after_decision():
    frame = bars()
    fc = forecasts(frame)
    hypothesis = next(
        item
        for item in generate_kronos_hypotheses()
        if item.template == "kronos_directional"
        and item.params[
            "min_terminal_return"
        ]
        == 0.005
    )
    trades = evaluate_kronos_hypothesis(
        hypothesis,
        frame,
        fc,
    )
    assert not trades.empty
    assert (
        pd.to_datetime(
            trades["entry_timestamp"],
            utc=True,
        )
        > pd.to_datetime(
            trades["decision_timestamp"],
            utc=True,
        )
    ).all()


def test_cost_stress_never_improves_expectancy():
    frame = bars()
    fc = forecasts(frame)
    hypothesis = next(
        item
        for item in generate_kronos_hypotheses()
        if item.template
        == "kronos_directional"
    )
    trades = evaluate_kronos_hypothesis(
        hypothesis,
        frame,
        fc,
    )
    base = trade_metrics(
        trades,
        frame.index[300],
        frame.index[-10],
        cost_bps_per_side=5.0,
    )
    stress = trade_metrics(
        trades,
        frame.index[300],
        frame.index[-10],
        cost_bps_per_side=10.0,
    )
    assert (
        stress["net_expectancy"]
        <= base["net_expectancy"]
    )


def test_no_execution_authority():
    for item in generate_kronos_hypotheses():
        assert (
            item.as_record()[
                "execution_authority"
            ]
            == "NONE"
        )
