import pandas as pd

from stocks.research.walkforward_splits import (
    rolling_periods,
)


def test_common_sample_keeps_500_row_validation_and_test_blocks():
    index = pd.date_range(
        "2024-01-02 14:30:00+00:00",
        periods=4529,
        freq="h",
    )

    folds = rolling_periods(
        index,
        hold_bars=21,
        requested_folds=4,
    )

    assert len(folds) >= 3

    for fold in folds:
        valid_start = pd.Timestamp(
            fold["valid"][0]
        )

        valid_end = pd.Timestamp(
            fold["valid"][1]
        )

        test_start = pd.Timestamp(
            fold["test"][0]
        )

        test_end = pd.Timestamp(
            fold["test"][1]
        )

        valid_rows = (
            index.get_loc(
                valid_end
            )
            -
            index.get_loc(
                valid_start
            )
            + 1
        )

        test_rows = (
            index.get_loc(
                test_end
            )
            -
            index.get_loc(
                test_start
            )
            + 1
        )

        assert valid_rows == 500
        assert test_rows == 500


def test_walkforward_purges_label_overlap_between_segments():
    index = pd.date_range(
        "2024-01-02 14:30:00+00:00",
        periods=6000,
        freq="h",
    )

    hold_bars = 42

    folds = rolling_periods(
        index,
        hold_bars=hold_bars,
        requested_folds=3,
    )

    gap = hold_bars + 1

    for fold in folds:
        train_end = index.get_loc(
            pd.Timestamp(
                fold["train"][1]
            )
        )

        valid_start = index.get_loc(
            pd.Timestamp(
                fold["valid"][0]
            )
        )

        valid_end = index.get_loc(
            pd.Timestamp(
                fold["valid"][1]
            )
        )

        test_start = index.get_loc(
            pd.Timestamp(
                fold["test"][0]
            )
        )

        assert (
            valid_start
            - train_end
            - 1
        ) == gap

        assert (
            test_start
            - valid_end
            - 1
        ) == gap
