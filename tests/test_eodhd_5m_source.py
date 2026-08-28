from datetime import timedelta
import json

import pandas as pd

from stocks.data.eodhd_5m_source import (
    aggregate_5m_to_15m,
)
from stocks.data.reference_15m_intake import (
    load_reference_15m,
)
from stocks.providers.eodhd import (
    chunk_windows,
    normalize_intraday_5m,
)


def test_eodhd_epoch_is_timestamp_source_of_truth():
    payload = [
        {
            "timestamp": 1704205800,
            "datetime": (
                "2099-01-01 00:00:00"
            ),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000,
        }
    ]

    result = normalize_intraday_5m(
        payload
    )

    assert list(
        result.index
    ) == [
        pd.Timestamp(
            "2024-01-02 "
            "14:30:00+00:00"
        )
    ]


def test_three_exact_5m_bars_aggregate_to_15m():
    frame = pd.DataFrame(
        {
            "open": [
                100.0,
                100.5,
                101.0,
            ],
            "high": [
                101.0,
                102.0,
                103.0,
            ],
            "low": [
                99.0,
                100.0,
                100.5,
            ],
            "close": [
                100.5,
                101.0,
                102.5,
            ],
            "volume": [
                100.0,
                200.0,
                300.0,
            ],
        },
        index=pd.DatetimeIndex(
            [
                (
                    "2024-01-02 "
                    "14:30:00+00:00"
                ),
                (
                    "2024-01-02 "
                    "14:35:00+00:00"
                ),
                (
                    "2024-01-02 "
                    "14:40:00+00:00"
                ),
            ],
            name="timestamp",
        ),
    )

    result, audit = (
        aggregate_5m_to_15m(
            frame
        )
    )

    row = result.iloc[0]

    assert len(result) == 1
    assert row["open"] == 100.0
    assert row["high"] == 103.0
    assert row["low"] == 99.0
    assert row["close"] == 102.5
    assert row["volume"] == 600.0

    assert (
        audit.complete_target_rows
        == 1
    )

    assert (
        audit.incomplete_bucket_count
        == 0
    )


def test_incomplete_5m_bucket_is_not_fabricated():
    frame = pd.DataFrame(
        {
            "open": [
                100.0,
                101.0,
            ],
            "high": [
                101.0,
                102.0,
            ],
            "low": [
                99.0,
                100.0,
            ],
            "close": [
                100.5,
                101.5,
            ],
            "volume": [
                100.0,
                200.0,
            ],
        },
        index=pd.DatetimeIndex(
            [
                (
                    "2024-01-02 "
                    "14:30:00+00:00"
                ),
                (
                    "2024-01-02 "
                    "14:40:00+00:00"
                ),
            ],
            name="timestamp",
        ),
    )

    result, audit = (
        aggregate_5m_to_15m(
            frame
        )
    )

    assert result.empty

    assert (
        audit.incomplete_bucket_count
        == 1
    )

    assert (
        audit.forward_fill
        is False
    )


def test_eodhd_chunks_stay_within_600_day_limit():
    windows = chunk_windows(
        "2020-10-01T00:00:00+00:00",
        "2024-01-13T00:00:00+00:00",
        chunk_days=590,
    )

    assert len(windows) == 3

    assert all(
        (
            stop
            - start
        )
        <= timedelta(days=600)
        for start, stop
        in windows
    )


def test_reference_loader_accepts_5m_derived_15m(
    tmp_path,
):
    data_path = (
        tmp_path
        / "AAPL_15m.parquet"
    )

    pd.DataFrame(
        {
            "timestamp_utc": (
                pd.to_datetime(
                    [
                        (
                            "2024-01-02 "
                            "14:30:00+00:00"
                        )
                    ],
                    utc=True,
                )
            ),
            "open": [
                100.0,
            ],
            "high": [
                101.0,
            ],
            "low": [
                99.0,
            ],
            "close": [
                100.5,
            ],
            "volume": [
                1000.0,
            ],
            "quality_status": [
                "VALIDATED_OHLC",
            ],
            "is_partial": [
                False,
            ],
        }
    ).to_parquet(
        data_path,
        index=False,
    )

    index_path = (
        tmp_path
        / "index.json"
    )

    index_path.write_text(
        json.dumps(
            {
                "bars": [
                    {
                        "provider": (
                            "EODHD"
                        ),
                        "symbol": (
                            "AAPL"
                        ),
                        "interval": (
                            "15m"
                        ),
                        "source_interval": (
                            "5m"
                        ),
                        "derivation": (
                            "AGGREGATED_5M_TO_15M"
                        ),
                        "path": str(
                            data_path
                        ),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    frame, source = (
        load_reference_15m(
            index_path,
            provider="EODHD",
            symbol="AAPL",
        )
    )

    assert len(frame) == 1
    assert source == data_path


def test_missing_provider_values_are_dropped_not_fabricated():
    payload = [
        {
            "timestamp": 1704205800,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": None,
        },
        {
            "timestamp": 1704206100,
            "open": 100.5,
            "high": 101.5,
            "low": 100.0,
            "close": 101.0,
            "volume": 1500,
        },
    ]

    result = normalize_intraday_5m(
        payload
    )

    assert len(result) == 1

    assert list(
        result.index
    ) == [
        pd.Timestamp(
            "2024-01-02 "
            "14:35:00+00:00"
        )
    ]

    audit = result.attrs[
        "eodhd_quality"
    ]

    assert (
        audit[
            "raw_rows"
        ]
        == 2
    )

    assert (
        audit[
            "accepted_rows"
        ]
        == 1
    )

    assert (
        audit[
            "dropped_missing_required_rows"
        ]
        == 1
    )

    assert (
        audit[
            "missing_by_column"
        ][
            "volume"
        ]
        == 1
    )

    assert (
        audit[
            "missing_values_fabricated"
        ]
        is False
    )


def test_eodhd_native_15m_artifact_is_rejected(
    tmp_path,
):
    data_path = (
        tmp_path
        / "AAPL_15m.parquet"
    )

    pd.DataFrame(
        {
            "timestamp_utc": (
                pd.to_datetime(
                    [
                        (
                            "2024-01-02 "
                            "14:30:00+00:00"
                        )
                    ],
                    utc=True,
                )
            ),
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.5],
            "volume": [1000.0],
            "quality_status": [
                "VALIDATED_OHLC"
            ],
            "is_partial": [
                False
            ],
        }
    ).to_parquet(
        data_path,
        index=False,
    )

    index_path = (
        tmp_path
        / "bad_index.json"
    )

    index_path.write_text(
        json.dumps(
            {
                "bars": [
                    {
                        "provider": (
                            "EODHD"
                        ),
                        "symbol": (
                            "AAPL"
                        ),
                        "interval": (
                            "15m"
                        ),
                        "source_interval": (
                            "15m"
                        ),
                        "path": str(
                            data_path
                        ),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    import pytest

    with pytest.raises(
        ValueError
    ):
        load_reference_15m(
            index_path,
            provider="EODHD",
            symbol="AAPL",
        )
