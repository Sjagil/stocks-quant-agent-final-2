import pandas as pd
import pytest

from stocks.data.reference_15m_intake import (
    append_newer_only,
    closed_rth_15m,
    require_compatible_overlap,
)


def frame(index, close=100.0):
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=pd.DatetimeIndex(
            index,
            tz="UTC",
            name="timestamp",
        ),
    )


def test_closed_rth_excludes_extended_and_open_bar():
    source = frame(
        [
            "2026-01-05 14:15:00",
            "2026-01-05 14:30:00",
            "2026-01-05 14:45:00",
            "2026-01-05 15:00:00",
        ]
    )

    result, audit = (
        closed_rth_15m(
            source,
            as_of=(
                "2026-01-05 "
                "14:52:00+00:00"
            ),
        )
    )

    assert list(
        result.index
    ) == [
        pd.Timestamp(
            "2026-01-05 "
            "14:30:00+00:00"
        )
    ]

    assert (
        audit[
            "coverage"
        ]
        == 1.0
    )


def test_append_newer_never_overwrites_history():
    base = frame(
        [
            "2026-01-05 14:30:00",
            "2026-01-05 14:45:00",
        ],
        close=100.0,
    )

    incoming = frame(
        [
            "2026-01-05 14:30:00",
            "2026-01-05 14:45:00",
            "2026-01-05 15:00:00",
        ],
        close=101.0,
    )

    result, appended = (
        append_newer_only(
            base,
            incoming,
        )
    )

    assert len(result) == 3
    assert len(appended) == 1

    assert (
        result.loc[
            pd.Timestamp(
                "2026-01-05 "
                "14:30:00+00:00"
            ),
            "close",
        ]
        == 100.0
    )


def test_material_overlap_divergence_blocks():
    index = pd.date_range(
        "2026-01-05 14:30:00+00:00",
        periods=10,
        freq="15min",
    )

    left = frame(
        index,
        close=100.0,
    )

    right = frame(
        index,
        close=102.0,
    )

    with pytest.raises(
        ValueError,
        match=(
            "material provider divergence"
        ),
    ):
        require_compatible_overlap(
            left,
            right,
            max_median_bps=50.0,
        )


def test_prepend_older_never_overwrites_existing_history():
    from stocks.data.reference_15m_intake import (
        prepend_older_only,
    )

    base = frame(
        [
            "2026-01-05 15:00:00",
            "2026-01-05 15:15:00",
        ],
        close=100.0,
    )

    incoming = frame(
        [
            "2026-01-05 14:30:00",
            "2026-01-05 14:45:00",
            "2026-01-05 15:00:00",
        ],
        close=101.0,
    )

    result, prepended = (
        prepend_older_only(
            base,
            incoming,
        )
    )

    assert len(result) == 4
    assert len(prepended) == 2

    assert (
        result.loc[
            pd.Timestamp(
                "2026-01-05 "
                "15:00:00+00:00"
            ),
            "close",
        ]
        == 100.0
    )
