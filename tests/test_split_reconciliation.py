import pandas as pd

from stocks.data.canonical import (
    SplitEvent,
    apply_split_adjustments,
)
from stocks.data.session_hourly import (
    aggregate_session_hourly,
)
from stocks.data.split_reconciliation import (
    evaluate_split_candidates,
)


def raw_split_frame():
    pre = pd.date_range(
        "2024-06-07 13:30:00+00:00",
        periods=26,
        freq="15min",
    )

    post = pd.date_range(
        "2024-06-10 13:30:00+00:00",
        periods=26,
        freq="15min",
    )

    index = pre.append(
        post
    )

    prices = (
        [1000.0] * len(pre)
        + [100.0] * len(post)
    )

    prices = pd.Series(
        prices,
        index=index,
    )

    return pd.DataFrame(
        {
            "open": prices,
            "high": (
                prices * 1.001
            ),
            "low": (
                prices * 0.999
            ),
            "close": prices,
            "volume": 1000.0,
        },
        index=index,
    )


def test_split_reconciliation_selects_explicit_adjustment():
    raw = raw_split_frame()

    event = SplitEvent(
        effective_at=pd.Timestamp(
            "2024-06-10 00:00:00+00:00"
        ),
        factor=10.0,
    )

    expected = (
        apply_split_adjustments(
            raw,
            (
                event,
            ),
        )
    )

    base_hourly, _ = (
        aggregate_session_hourly(
            expected,
            as_of=(
                "2024-06-10 "
                "20:00:00+00:00"
            ),
        )
    )

    selected, audit = (
        evaluate_split_candidates(
            raw,
            base_hourly,
            (
                event,
            ),
            as_of=(
                "2024-06-10 "
                "20:00:00+00:00"
            ),
        )
    )

    assert (
        audit[
            "selection"
        ]
        == "SPLIT_ADJUSTED"
    )

    assert (
        audit[
            "raw_compatible"
        ]
        is False
    )

    assert (
        audit[
            "adjusted_compatible"
        ]
        is True
    )

    pd.testing.assert_frame_equal(
        selected,
        expected,
    )
