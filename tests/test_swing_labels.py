import pandas as pd

from stocks.research.swing_labels import (
    forward_hold_return,
    purged_periods,
)


def test_forward_hold_return_uses_next_bar_entry():
    close = pd.Series(
        [
            100.0,
            101.0,
            102.0,
            103.0,
            104.0,
        ]
    )

    result = forward_hold_return(
        close,
        hold_bars=2,
    )

    expected = (
        103.0 / 101.0 - 1.0
    )

    assert abs(
        result.iloc[0]
        - expected
    ) < 1e-12


def test_purged_periods_leave_boundary_gap():
    index = pd.date_range(
        "2020-01-01",
        periods=2000,
        freq="h",
        tz="UTC",
    )

    periods = purged_periods(
        index,
        lookahead_bars=42,
    )

    train_end = pd.Timestamp(
        periods["train"][1]
    )

    valid_start = pd.Timestamp(
        periods["valid"][0]
    )

    assert (
        valid_start
        > train_end
    )
