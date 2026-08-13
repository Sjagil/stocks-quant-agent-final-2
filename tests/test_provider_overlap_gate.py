import pandas as pd
import pytest

from stocks.data.reference_15m_intake import (
    overlap_audit,
    require_compatible_overlap,
)


def make_frame(
    closes,
):
    index = pd.date_range(
        "2026-01-05 14:30:00+00:00",
        periods=len(closes),
        freq="15min",
    )

    closes = pd.Series(
        closes,
        index=index,
        dtype=float,
    )

    return pd.DataFrame(
        {
            "open": closes,
            "high": closes + 1.0,
            "low": closes - 1.0,
            "close": closes,
            "volume": 1000.0,
        },
        index=index,
    )


def test_overlap_gate_blocks_minor_fraction_of_catastrophic_rows():
    base = make_frame(
        [100.0] * 100
    )

    candidate_values = (
        [1000.0] * 5
        + [100.0] * 95
    )

    candidate = make_frame(
        candidate_values
    )

    audit = overlap_audit(
        base,
        candidate,
    )

    assert (
        audit[
            "median_close_difference_bps"
        ]
        == 0.0
    )

    assert (
        audit[
            "bad_fraction"
        ]
        == pytest.approx(
            0.05
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "material provider divergence"
        ),
    ):
        require_compatible_overlap(
            base,
            candidate,
            max_median_bps=50.0,
            max_p95_bps=100.0,
            max_bad_fraction=0.01,
        )


def test_overlap_gate_allows_isolated_small_difference():
    base = make_frame(
        [100.0] * 100
    )

    values = (
        [100.5]
        + [100.0] * 99
    )

    candidate = make_frame(
        values
    )

    result = require_compatible_overlap(
        base,
        candidate,
        max_median_bps=50.0,
        max_p95_bps=100.0,
        max_bad_fraction=0.01,
    )

    assert (
        result[
            "bad_fraction"
        ]
        == 0.0
    )
