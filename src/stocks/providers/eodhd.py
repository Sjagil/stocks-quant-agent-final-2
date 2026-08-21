from __future__ import annotations

from datetime import timedelta

from dataclasses import dataclass
from typing import Any

import pandas as pd

from stocks.data.canonical import (
    canonicalize_ohlcv,
    validate_canonical,
)
from stocks.providers.http import ProviderHTTPClient


EODHD_BASE_URL = "https://eodhd.com/api"
EODHD_INTRADAY_MAX_DAYS = 600


@dataclass(frozen=True)
class EODHDIntradayResult:
    frame: pd.DataFrame
    provider_symbol: str
    request_count: int
    start: str
    end_exclusive: str
    source_quality: dict[str, Any]


def utc_timestamp(
    value: str | pd.Timestamp,
) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)

    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")

    return timestamp.tz_convert("UTC")


def provider_symbol(
    symbol: str,
) -> str:
    value = str(symbol).strip().upper()

    if not value:
        raise ValueError("symbol is required")

    if "." in value:
        return value

    return f"{value}.US"


def chunk_windows(
    start: str | pd.Timestamp,
    end_exclusive: str | pd.Timestamp,
    *,
    chunk_days: int = 590,
) -> tuple[
    tuple[pd.Timestamp, pd.Timestamp],
    ...,
]:
    if not (
        1
        <= int(chunk_days)
        <= EODHD_INTRADAY_MAX_DAYS
    ):
        raise ValueError(
            "chunk_days must be between 1 and 600"
        )

    start_ts = utc_timestamp(start)
    end_ts = utc_timestamp(end_exclusive)

    if start_ts >= end_ts:
        raise ValueError(
            "start must be before end_exclusive"
        )

    step = timedelta(days=int(chunk_days))

    windows: list[
        tuple[pd.Timestamp, pd.Timestamp]
    ] = []

    cursor = start_ts

    while cursor < end_ts:
        stop = min(
            cursor + step,
            end_ts,
        )

        windows.append(
            (
                cursor,
                stop,
            )
        )

        cursor = stop

    return tuple(windows)


def _payload_rows(
    payload: Any,
) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [
            row
            for row in payload
            if isinstance(row, dict)
        ]

    if isinstance(payload, dict):
        data = payload.get("data")

        if isinstance(data, list):
            return [
                row
                for row in data
                if isinstance(row, dict)
            ]

        if (
            payload.get("message")
            or payload.get("error")
        ):
            raise ValueError(
                "EODHD intraday response "
                "reported an error"
            )

    return []


def _deduplicate_identical(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    if (
        frame.empty
        or not frame.index
        .duplicated(
            keep=False
        )
        .any()
    ):
        return frame

    duplicated = frame.loc[
        frame.index.duplicated(
            keep=False
        )
    ]

    columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for timestamp, group in (
        duplicated.groupby(
            level=0,
            sort=True,
        )
    ):
        if (
            group[columns]
            .nunique(
                dropna=False
            )
            .max()
            > 1
        ):
            raise ValueError(
                "conflicting duplicate "
                "EODHD bar at "
                f"{timestamp}"
            )

    return frame.loc[
        ~frame.index.duplicated(
            keep="last"
        )
    ]


def normalize_intraday_5m(
    payload: Any,
) -> pd.DataFrame:
    rows = _payload_rows(payload)

    if not rows:
        return pd.DataFrame(
            columns=[
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
            index=pd.DatetimeIndex(
                [],
                tz="UTC",
                name="timestamp",
            ),
        )

    raw = pd.DataFrame(rows)

    required = {
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    missing = sorted(
        required
        - set(raw.columns)
    )

    if missing:
        raise ValueError(
            "EODHD intraday payload "
            "missing fields: "
            f"{missing}"
        )

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for column in numeric_columns:
        raw[column] = pd.to_numeric(
            raw[column],
            errors="coerce",
        )

    missing_by_column = {
        column: int(
            raw[column]
            .isna()
            .sum()
        )
        for column
        in numeric_columns
    }

    missing_required = (
        raw[
            numeric_columns
        ]
        .isna()
        .any(
            axis=1
        )
    )

    dropped_missing_rows = int(
        missing_required.sum()
    )

    raw_row_count = int(
        len(raw)
    )

    if dropped_missing_rows:
        raw = (
            raw.loc[
                ~missing_required
            ]
            .copy()
        )

    if raw.empty:
        result = pd.DataFrame(
            columns=[
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
            index=pd.DatetimeIndex(
                [],
                tz="UTC",
                name="timestamp",
            ),
        )

        result.attrs[
            "eodhd_quality"
        ] = {
            "raw_rows": (
                raw_row_count
            ),
            "accepted_rows": 0,
            "dropped_missing_required_rows": (
                dropped_missing_rows
            ),
            "missing_by_column": (
                missing_by_column
            ),
            "missing_values_fabricated": (
                False
            ),
        }

        return result

    epoch = pd.to_numeric(
        raw["timestamp"],
        errors="coerce",
    )

    if epoch.isna().any():
        raise ValueError(
            "EODHD intraday payload "
            "contains invalid epoch timestamps"
        )

    timestamps = pd.to_datetime(
        epoch.astype("int64"),
        unit="s",
        utc=True,
        errors="coerce",
    )

    if timestamps.isna().any():
        raise ValueError(
            "EODHD intraday epoch "
            "conversion failed"
        )

    frame = pd.DataFrame(
        {
            "open": raw[
                "open"
            ].to_numpy(),
            "high": raw[
                "high"
            ].to_numpy(),
            "low": raw[
                "low"
            ].to_numpy(),
            "close": raw[
                "close"
            ].to_numpy(),
            "volume": raw[
                "volume"
            ].to_numpy(),
        },
        index=pd.DatetimeIndex(
            timestamps,
            name="timestamp",
        ),
    )

    frame = canonicalize_ohlcv(
        frame
    )

    frame = _deduplicate_identical(
        frame
    )

    frame = canonicalize_ohlcv(
        frame
    )

    validate_canonical(
        frame
    )

    frame.attrs[
        "eodhd_quality"
    ] = {
        "raw_rows": (
            raw_row_count
        ),
        "accepted_rows": int(
            len(frame)
        ),
        "dropped_missing_required_rows": (
            dropped_missing_rows
        ),
        "missing_by_column": (
            missing_by_column
        ),
        "missing_values_fabricated": (
            False
        ),
    }

    return frame


def fetch_intraday_5m(
    symbol: str,
    *,
    start: str | pd.Timestamp,
    end_exclusive: str | pd.Timestamp,
    api_key: str,
    chunk_days: int = 590,
    client: ProviderHTTPClient | None = None,
) -> EODHDIntradayResult:
    if not str(api_key).strip():
        raise ValueError(
            "EODHD API key is required"
        )

    start_ts = utc_timestamp(start)
    end_ts = utc_timestamp(
        end_exclusive
    )

    windows = chunk_windows(
        start_ts,
        end_ts,
        chunk_days=chunk_days,
    )

    ticker = provider_symbol(
        symbol
    )

    own_client = client is None

    http = (
        client
        or ProviderHTTPClient(
            user_agent=(
                "stocks-quant-agent/"
                "eodhd-5m-research"
            )
        )
    )

    frames: list[pd.DataFrame] = []

    source_quality = {
        "raw_rows": 0,
        "accepted_rows": 0,
        "dropped_missing_required_rows": 0,
        "missing_by_column": {
            "open": 0,
            "high": 0,
            "low": 0,
            "close": 0,
            "volume": 0,
        },
        "missing_values_fabricated": False,
    }

    try:
        for (
            chunk_start,
            chunk_end,
        ) in windows:
            payload = http.get_json(
                (
                    f"{EODHD_BASE_URL}/"
                    f"intraday/{ticker}"
                ),
                params={
                    "api_token": api_key,
                    "fmt": "json",
                    "interval": "5m",
                    "from": int(
                        chunk_start.timestamp()
                    ),
                    "to": (
                        int(
                            chunk_end.timestamp()
                        )
                        - 1
                    ),
                },
            )

            frame = normalize_intraday_5m(
                payload
            )

            chunk_quality = (
                frame.attrs.get(
                    "eodhd_quality",
                    {},
                )
            )

            source_quality[
                "raw_rows"
            ] += int(
                chunk_quality.get(
                    "raw_rows",
                    0,
                )
            )

            source_quality[
                "accepted_rows"
            ] += int(
                chunk_quality.get(
                    "accepted_rows",
                    0,
                )
            )

            source_quality[
                "dropped_missing_required_rows"
            ] += int(
                chunk_quality.get(
                    "dropped_missing_required_rows",
                    0,
                )
            )

            for column in (
                "open",
                "high",
                "low",
                "close",
                "volume",
            ):
                source_quality[
                    "missing_by_column"
                ][column] += int(
                    chunk_quality.get(
                        "missing_by_column",
                        {},
                    ).get(
                        column,
                        0,
                    )
                )

            if frame.empty:
                continue

            frame = frame.loc[
                (
                    frame.index
                    >= chunk_start
                )
                & (
                    frame.index
                    < chunk_end
                )
            ].copy()

            if not frame.empty:
                frames.append(frame)

    finally:
        if own_client:
            http.close()

    if frames:
        frame = pd.concat(
            frames
        ).sort_index()

        frame = _deduplicate_identical(
            frame
        )

        frame = canonicalize_ohlcv(
            frame
        )

        validate_canonical(
            frame
        )

        frame = frame.loc[
            (
                frame.index
                >= start_ts
            )
            & (
                frame.index
                < end_ts
            )
        ].copy()

    else:
        frame = pd.DataFrame(
            columns=[
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
            index=pd.DatetimeIndex(
                [],
                tz="UTC",
                name="timestamp",
            ),
        )

    return EODHDIntradayResult(
        frame=frame,
        provider_symbol=ticker,
        request_count=len(windows),
        start=start_ts.isoformat(),
        end_exclusive=(
            end_ts.isoformat()
        ),
        source_quality={
            **source_quality,
            "drop_fraction": (
                float(
                    source_quality[
                        "dropped_missing_required_rows"
                    ]
                    / source_quality[
                        "raw_rows"
                    ]
                )
                if source_quality[
                    "raw_rows"
                ]
                else 0.0
            ),
        },
    )
