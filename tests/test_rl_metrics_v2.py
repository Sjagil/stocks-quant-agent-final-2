from datetime import timedelta
import numpy as np
import pandas as pd

from stocks.rl.metrics import (
    annualization_factor,
    summarize_returns,
)


def test_hourly_data_is_not_annualized_as_daily() -> None:
    days = pd.bdate_range(
        "2025-01-02",
        periods=252,
        tz="UTC",
    )

    timestamps = []

    for day in days:
        for hour in range(7):
            timestamps.append(
                day
                + timedelta(hours=14, minutes=30)
                + timedelta(hours=hour)
            )

    factor = annualization_factor(
        pd.DatetimeIndex(
            timestamps
        )
    )

    assert factor > 1000
    assert factor < 2500
    assert factor != 252.0


def test_return_metrics_are_finite() -> None:
    index = pd.date_range(
        "2025-01-01",
        periods=500,
        freq="h",
        tz="UTC",
    )

    returns = pd.Series(
        np.sin(
            np.arange(500) / 20
        ) * 0.001,
        index=index,
    )

    result = summarize_returns(
        returns
    )

    assert np.isfinite(
        result.sharpe
    )

    assert result.observations == 500

    assert result.periods_per_year > 252
