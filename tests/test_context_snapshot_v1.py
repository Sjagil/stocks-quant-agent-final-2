import pandas as pd

from stocks.research.context_snapshot import (
    _series_summary,
)


def test_macro_series_summary_is_causal() -> None:
    series = pd.Series(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        index=pd.date_range(
            "2026-01-01",
            periods=6,
            tz="UTC",
        ),
    )

    result = _series_summary(
        series
    )

    assert result["value"] == 6.0
    assert result["change_1"] == 1.0
    assert result["change_5"] == 5.0
