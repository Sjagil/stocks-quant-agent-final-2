import numpy as np
import pandas as pd

from stocks.research.strategy_factory_1h import (
    BLOCKED_1H_V1,
    contained_trades,
    eligible_1h_specs,
    generate_hypotheses,
    net_returns_from_gross,
    prepare_one_hour_frame,
    trade_metrics,
)


def test_eligible_1h_registry_is_long_only():
    specs = (
        eligible_1h_specs()
    )

    assert len(specs) >= 20

    names = {
        spec.name
        for spec in specs
    }

    assert not (
        names
        & BLOCKED_1H_V1
    )

    assert all(
        spec.policy_status
        == "LONG_ONLY_GO"
        for spec in specs
    )


def test_hypothesis_generation_is_unique():
    hypotheses = (
        generate_hypotheses(
            max_variants_per_strategy=3,
            seed=123,
        )
    )

    ids = [
        item.hypothesis_id
        for item in hypotheses
    ]

    assert len(ids) == len(
        set(ids)
    )

    assert all(
        item.primary_timeframe
        == "1h"
        for item in hypotheses
    )

    assert all(
        item.parameter_basis
        == "BAR_NATIVE_1H"
        for item in hypotheses
    )

    assert all(
        item.execution_authority
        == "NONE"
        for item in hypotheses
    )


def test_round_trip_cost_is_applied():
    gross = np.asarray(
        [
            0.01,
            -0.01,
        ]
    )

    result = (
        net_returns_from_gross(
            gross,
            cost_bps_per_side=10.0,
        )
    )

    assert (
        result[0]
        < gross[0]
    )

    assert (
        result[1]
        < gross[1]
    )

    expected = (
        (
            1.0
            + gross
        )
        * 0.999
        / 1.001
        - 1.0
    )

    np.testing.assert_allclose(
        result,
        expected,
        rtol=0.0,
        atol=1e-15,
    )


def test_contained_trades_prevents_boundary_leakage():
    frame = pd.DataFrame(
        {
            "entry_time": (
                pd.to_datetime(
                    [
                        "2026-01-05 15:30:00Z",
                        "2026-01-05 16:30:00Z",
                        "2026-01-05 17:30:00Z",
                    ],
                    utc=True,
                )
            ),
            "exit_time": (
                pd.to_datetime(
                    [
                        "2026-01-05 16:30:00Z",
                        "2026-01-05 19:30:00Z",
                        "2026-01-05 18:30:00Z",
                    ],
                    utc=True,
                )
            ),
            "gross_return": [
                0.01,
                0.02,
                0.03,
            ],
        }
    )

    result = contained_trades(
        frame,
        [
            "2026-01-05 15:00:00+00:00",
            "2026-01-05 18:45:00+00:00",
        ],
    )

    assert len(result) == 2

    assert (
        pd.Timestamp(
            "2026-01-05 16:30:00Z"
        )
        not in set(
            result[
                "entry_time"
            ]
        )
    )


def test_trade_metrics_positive_edge():
    trades = pd.DataFrame(
        {
            "gross_return": [
                0.02,
                0.01,
                -0.005,
                0.015,
            ],
            "duration_bars": [
                5,
                7,
                4,
                8,
            ],
            "forced": [
                False,
                False,
                True,
                False,
            ],
        }
    )

    metrics = trade_metrics(
        trades,
        cost_bps_per_side=3.0,
    )

    assert (
        metrics[
            "trades"
        ]
        == 4
    )

    assert (
        metrics[
            "net_expectancy"
        ]
        > 0
    )

    assert (
        metrics[
            "profit_factor"
        ]
        > 1
    )

    assert (
        metrics[
            "forced_ratio"
        ]
        == 0.25
    )


def test_prepare_one_hour_frame():
    index = pd.date_range(
        "2026-01-05 14:30:00+00:00",
        periods=10,
        freq="1h",
    )

    raw = pd.DataFrame(
        {
            "open": np.arange(
                10,
                dtype=float,
            )
            + 100.0,
            "high": np.arange(
                10,
                dtype=float,
            )
            + 101.0,
            "low": np.arange(
                10,
                dtype=float,
            )
            + 99.0,
            "close": np.arange(
                10,
                dtype=float,
            )
            + 100.5,
            "volume": np.full(
                10,
                1000.0,
            ),
        },
        index=index,
    )

    raw.index.name = (
        "timestamp"
    )

    result = (
        prepare_one_hour_frame(
            raw,
            "AAPL",
        )
    )

    assert len(result) == 10

    assert (
        result[
            "symbol"
        ]
        .eq(
            "AAPL"
        )
        .all()
    )

    assert (
        str(
            result[
                "date"
            ].dtype
        )
        .endswith(
            "UTC]"
        )
    )
