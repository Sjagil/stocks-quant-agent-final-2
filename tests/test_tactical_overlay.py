import pandas as pd

from stocks.research.tactical_overlay import (
    attach_predictions_to_trades,
    normalize_predictions,
    overlay_mask,
)


def predictions():
    time = pd.Timestamp(
        "2026-01-05 15:30:00+00:00"
    )

    return pd.DataFrame(
        {
            "datetime": [
                time,
                time,
                time,
                time,
                time,
            ],
            "symbol": [
                "AAPL",
                "AMD",
                "MSFT",
                "NVDA",
                "QQQ",
            ],
            "prediction": [
                0.1,
                -0.2,
                0.3,
                0.2,
                0.0,
            ],
            "fold": [
                1,
                1,
                1,
                1,
                1,
            ],
            "variant": [
                "TACTICAL_RAW",
            ] * 5,
            "hold_bars": [
                21,
            ] * 5,
        }
    )


def test_prediction_ranking():
    result = normalize_predictions(
        predictions()
    )

    msft = result.loc[
        result[
            "symbol"
        ]
        == "MSFT"
    ].iloc[0]

    assert (
        msft[
            "prediction_ordinal"
        ]
        == 1
    )

    assert (
        msft[
            "prediction_rank"
        ]
        == 1.0
    )


def test_trade_attachment_is_not_future():
    trades = pd.DataFrame(
        {
            "hypothesis_id": [
                "abc",
            ],
            "strategy": [
                "test",
            ],
            "symbol": [
                "MSFT",
            ],
            "entry_time": pd.to_datetime(
                [
                    "2026-01-05 "
                    "15:30:00+00:00",
                ],
                utc=True,
            ),
            "exit_time": pd.to_datetime(
                [
                    "2026-01-06 "
                    "15:30:00+00:00",
                ],
                utc=True,
            ),
            "gross_return": [
                0.01,
            ],
            "duration_bars": [
                7,
            ],
            "forced": [
                False,
            ],
        }
    )

    result = (
        attach_predictions_to_trades(
            trades,
            predictions(),
        )
    )

    assert len(result) == 1

    assert (
        result[
            "decision_lag_minutes"
        ].iloc[0]
        == 0.0
    )


def test_top2_filter():
    ranked = normalize_predictions(
        predictions()
    )

    mask = overlay_mask(
        ranked,
        "TOP2",
    )

    symbols = set(
        ranked.loc[
            mask,
            "symbol",
        ]
    )

    assert symbols == {
        "MSFT",
        "NVDA",
    }


def test_stale_prediction_is_not_attached():
    trades = pd.DataFrame(
        {
            "hypothesis_id": [
                "abc",
            ],
            "strategy": [
                "test",
            ],
            "symbol": [
                "MSFT",
            ],
            "entry_time": pd.to_datetime(
                [
                    "2026-01-05 "
                    "16:30:00+00:00",
                ],
                utc=True,
            ),
            "exit_time": pd.to_datetime(
                [
                    "2026-01-06 "
                    "16:30:00+00:00",
                ],
                utc=True,
            ),
            "gross_return": [
                0.01,
            ],
            "duration_bars": [
                7,
            ],
            "forced": [
                False,
            ],
        }
    )

    old_predictions = predictions()

    result = (
        attach_predictions_to_trades(
            trades,
            old_predictions,
        )
    )

    assert result.empty
