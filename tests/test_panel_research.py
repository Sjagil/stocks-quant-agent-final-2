import numpy as np
import pandas as pd

from stocks.research.panel import (
    build_relative_return_panel,
    center_cross_sectional_label,
    cross_sectional_rank_features,
    validate_panel_dataset,
)


def make_frame(
    open_values,
    close_values,
):
    index = pd.date_range(
        "2026-01-05 14:30:00+00:00",
        periods=len(
            open_values
        ),
        freq="1h",
    )

    return pd.DataFrame(
        {
            "open": open_values,
            "high": (
                np.maximum(
                    open_values,
                    close_values,
                )
                + 1.0
            ),
            "low": (
                np.minimum(
                    open_values,
                    close_values,
                )
                - 1.0
            ),
            "close": close_values,
            "volume": 1000.0,
        },
        index=index,
    )


def test_relative_return_panel_uses_next_open():
    asset = make_frame(
        [
            100.0,
            100.0,
            110.0,
            120.0,
        ],
        [
            100.0,
            110.0,
            120.0,
            130.0,
        ],
    )

    benchmark = make_frame(
        [
            100.0,
            100.0,
            100.0,
            100.0,
        ],
        [
            100.0,
            102.0,
            104.0,
            106.0,
        ],
    )

    panel = build_relative_return_panel(
        {
            "AAA": asset,
        },
        benchmark,
        hold_bars=1,
    )

    first = panel.iloc[0]

    expected_asset = (
        110.0 / 100.0 - 1.0
    )

    expected_benchmark = (
        102.0 / 100.0 - 1.0
    )

    assert first[
        "raw_return"
    ] == expected_asset

    assert first[
        "benchmark_return"
    ] == expected_benchmark

    assert first[
        "excess_return"
    ] == (
        expected_asset
        - expected_benchmark
    )


def test_cross_sectional_label_zero_centers():
    time = pd.Timestamp(
        "2026-01-05 15:30:00+00:00"
    )

    frame = pd.DataFrame(
        {
            "decision_time": [
                time,
                time,
                time,
            ],
            "symbol": [
                "AAA",
                "BBB",
                "CCC",
            ],
            "excess_return": [
                0.03,
                0.01,
                -0.02,
            ],
        }
    )

    result = (
        center_cross_sectional_label(
            frame,
            time_column=(
                "decision_time"
            ),
            min_assets=3,
        )
    )

    assert len(
        result
    ) == 3

    assert abs(
        result[
            "label"
        ].mean()
    ) < 1e-12


def test_cross_sectional_rank_is_same_time_only():
    first = pd.Timestamp(
        "2026-01-05 15:30:00+00:00"
    )

    second = pd.Timestamp(
        "2026-01-05 16:30:00+00:00"
    )

    frame = pd.DataFrame(
        {
            "datetime": [
                first,
                first,
                first,
                second,
                second,
                second,
            ],
            "symbol": [
                "A",
                "B",
                "C",
                "A",
                "B",
                "C",
            ],
            "feature": [
                1.0,
                2.0,
                3.0,
                300.0,
                200.0,
                100.0,
            ],
            "flag_available": [
                1,
                1,
                0,
                1,
                0,
                1,
            ],
            "label": [
                -0.1,
                0.0,
                0.1,
                0.1,
                0.0,
                -0.1,
            ],
        }
    )

    result = (
        cross_sectional_rank_features(
            frame,
            time_column="datetime",
            feature_columns=[
                "feature",
                "flag_available",
            ],
            passthrough_columns=[
                "flag_available",
            ],
        )
    )

    first_values = (
        result.loc[
            result[
                "datetime"
            ]
            == first,
            "feature",
        ]
        .tolist()
    )

    second_values = (
        result.loc[
            result[
                "datetime"
            ]
            == second,
            "feature",
        ]
        .tolist()
    )

    np.testing.assert_allclose(
        first_values,
        [
            -1.0 / 6.0,
            1.0 / 6.0,
            0.5,
        ],
        rtol=0.0,
        atol=1e-15,
    )

    np.testing.assert_allclose(
        second_values,
        [
            0.5,
            1.0 / 6.0,
            -1.0 / 6.0,
        ],
        rtol=0.0,
        atol=1e-15,
    )

    assert result[
        "flag_available"
    ].tolist() == [
        1,
        1,
        0,
        1,
        0,
        1,
    ]

    audit = (
        validate_panel_dataset(
            result,
            min_assets=3,
        )
    )

    assert (
        audit[
            "time_groups"
        ]
        == 2
    )

    assert (
        audit[
            "min_cross_section"
        ]
        == 3
    )
