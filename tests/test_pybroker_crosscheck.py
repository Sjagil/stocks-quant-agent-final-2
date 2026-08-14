from collections import Counter

import numpy as np
import pandas as pd

from stocks.research.pybroker_crosscheck import (
    build_schedule_frame,
    classify_crosscheck,
    expected_trade_keys,
    multiset_match_ratio,
    run_pybroker_replay,
)


def frame():
    dates = pd.date_range(
        "2026-01-05 14:30:00+00:00",
        periods=8,
        freq="1h",
    )

    return pd.DataFrame(
        {
            "symbol": "AAPL",
            "date": dates,
            "open": [
                100,
                101,
                102,
                103,
                104,
                105,
                106,
                107,
            ],
            "high": [
                101,
                102,
                103,
                104,
                105,
                106,
                107,
                108,
            ],
            "low": [
                99,
                100,
                101,
                102,
                103,
                104,
                105,
                106,
            ],
            "close": [
                100.5,
                101.5,
                102.5,
                103.5,
                104.5,
                105.5,
                106.5,
                107.5,
            ],
            "volume": 1000.0,
        }
    )


def trades():
    return pd.DataFrame(
        {
            "hypothesis_id": [
                "abc",
            ],
            "strategy": [
                "test",
            ],
            "family": [
                "test",
            ],
            "symbol": [
                "AAPL",
            ],
            "entry_time": (
                pd.to_datetime(
                    [
                        "2026-01-05 "
                        "16:30:00+00:00",
                    ],
                    utc=True,
                )
            ),
            "exit_time": (
                pd.to_datetime(
                    [
                        "2026-01-05 "
                        "19:30:00+00:00",
                    ],
                    utc=True,
                )
            ),
            "gross_return": [
                105.0
                / 102.0
                - 1.0,
            ],
            "score": [
                1.0,
            ],
            "duration_bars": [
                3,
            ],
            "forced": [
                False,
            ],
        }
    )


def test_schedule_uses_prior_decision_bar():
    scheduled, audit = (
        build_schedule_frame(
            {
                "AAPL": frame(),
            },
            trades(),
        )
    )

    entry = scheduled.loc[
        scheduled[
            "scheduled_entry"
        ]
        == 1
    ]

    exit_ = scheduled.loc[
        scheduled[
            "scheduled_exit"
        ]
        == 1
    ]

    assert (
        entry[
            "date"
        ].iloc[0]
        == pd.Timestamp(
            "2026-01-05 "
            "15:30:00"
        )
    )

    assert (
        exit_[
            "date"
        ].iloc[0]
        == pd.Timestamp(
            "2026-01-05 "
            "18:30:00"
        )
    )

    assert (
        audit[
            "expected_trades"
        ]
        == 1
    )


def test_multiset_trade_parity():
    expected = Counter(
        {
            (
                "AAPL",
                pd.Timestamp(
                    "2026-01-05 "
                    "16:30:00"
                ),
                pd.Timestamp(
                    "2026-01-05 "
                    "19:30:00"
                ),
            ): 1,
        }
    )

    observed = expected.copy()

    assert (
        multiset_match_ratio(
            expected,
            observed,
        )
        == 1.0
    )


def test_expected_trade_key_count():
    result = (
        expected_trade_keys(
            trades()
        )
    )

    assert (
        sum(
            result.values()
        )
        == 1
    )


def test_crosscheck_classifier():
    assert (
        classify_crosscheck(
            usable_folds=4,
            positive_fold_ratio=1.0,
            stress_positive_fold_ratio=1.0,
            worst_expectancy_bps=20.0,
            median_stress_expectancy_bps=30.0,
            min_schedule_match_ratio=1.0,
            positive_symbol_ratio=0.75,
            max_symbol_trade_share=0.30,
        )
        == "CROSS_ENGINE_VALIDATED"
    )

    assert (
        classify_crosscheck(
            usable_folds=1,
            positive_fold_ratio=1.0,
            stress_positive_fold_ratio=1.0,
            worst_expectancy_bps=100.0,
            median_stress_expectancy_bps=100.0,
            min_schedule_match_ratio=1.0,
            positive_symbol_ratio=1.0,
            max_symbol_trade_share=0.20,
        )
        == "CROSS_ENGINE_REJECT"
    )


def test_actual_pybroker_schedule_replay():
    pytest = __import__(
        "pytest"
    )

    pytest.importorskip(
        "pybroker"
    )

    result = (
        run_pybroker_replay(
            {
                "AAPL": frame(),
            },
            trades(),
            cost_bps_per_side=0.0,
            target_weight=0.25,
        )
    )

    assert (
        result[
            "expected_trade_count"
        ]
        == 1
    )

    assert (
        result[
            "pybroker_trade_count"
        ]
        == 1
    )

    assert (
        result[
            "schedule_match_ratio"
        ]
        == 1.0
    )


def rollover_trades():
    return pd.DataFrame(
        {
            "hypothesis_id": [
                "abc",
                "abc",
            ],
            "strategy": [
                "test",
                "test",
            ],
            "family": [
                "test",
                "test",
            ],
            "symbol": [
                "AAPL",
                "AAPL",
            ],
            "entry_time": pd.to_datetime(
                [
                    "2026-01-05 "
                    "16:30:00+00:00",
                    "2026-01-05 "
                    "19:30:00+00:00",
                ],
                utc=True,
            ),
            "exit_time": pd.to_datetime(
                [
                    "2026-01-05 "
                    "19:30:00+00:00",
                    "2026-01-05 "
                    "21:30:00+00:00",
                ],
                utc=True,
            ),
            "gross_return": [
                105.0
                / 102.0
                - 1.0,
                107.0
                / 105.0
                - 1.0,
            ],
            "score": [
                1.0,
                1.0,
            ],
            "duration_bars": [
                3,
                2,
            ],
            "forced": [
                False,
                False,
            ],
        }
    )


def test_same_open_rollover_uses_separate_replay_lanes():
    from stocks.research.pybroker_crosscheck import (
        assign_replay_lanes,
    )

    laned, audit = (
        assign_replay_lanes(
            rollover_trades()
        )
    )

    assert (
        audit[
            "rollover_count"
        ]
        == 1
    )

    assert (
        audit[
            "max_replay_lanes_per_symbol"
        ]
        == 2
    )

    assert (
        laned[
            "_replay_symbol"
        ]
        .nunique()
        == 2
    )


def test_actual_pybroker_same_open_rollover_replay():
    pytest = __import__(
        "pytest"
    )

    pytest.importorskip(
        "pybroker"
    )

    result = (
        run_pybroker_replay(
            {
                "AAPL": frame(),
            },
            rollover_trades(),
            cost_bps_per_side=0.0,
            target_weight=0.25,
        )
    )

    assert (
        result[
            "expected_trade_count"
        ]
        == 2
    )

    assert (
        result[
            "pybroker_trade_count"
        ]
        == 2
    )

    assert (
        result[
            "schedule_match_ratio"
        ]
        == 1.0
    )

    assert (
        result[
            "exact_schedule_match"
        ]
        is True
    )

    assert (
        result[
            "rollover_count"
        ]
        == 1
    )


def test_market_structure_routes_to_15m_execution():
    from stocks.research.pybroker_crosscheck import (
        replay_contract_audit,
    )

    frame = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                [
                    "2026-01-05 "
                    "16:30:00+00:00",
                ],
                utc=True,
            ),
            "exit_time": pd.to_datetime(
                [
                    "2026-01-05 "
                    "16:30:00+00:00",
                ],
                utc=True,
            ),
            "duration_bars": [
                0,
            ],
        }
    )

    audit = replay_contract_audit(
        frame,
        strategy=(
            "market_structure_"
            "atr_pullback"
        ),
    )

    assert (
        audit[
            "compatible"
        ]
        is False
    )

    assert (
        audit[
            "execution_contract"
        ]
        == (
            "1H_SETUP_"
            "INTRABAR_EXECUTION"
        )
    )

    assert (
        audit[
            "route"
        ]
        == (
            "1H_SETUP_15M_"
            "EXECUTION_VALIDATION"
        )
    )

    assert (
        audit[
            "same_bar_trades"
        ]
        == 1
    )


def test_next_open_trade_contract_remains_compatible():
    from stocks.research.pybroker_crosscheck import (
        replay_contract_audit,
    )

    audit = replay_contract_audit(
        trades(),
        strategy="rsi_threshold_exit",
    )

    assert (
        audit[
            "compatible"
        ]
        is True
    )

    assert (
        audit[
            "execution_contract"
        ]
        == "NEXT_OPEN_REPLAY"
    )

    assert (
        audit[
            "same_bar_trades"
        ]
        == 0
    )
