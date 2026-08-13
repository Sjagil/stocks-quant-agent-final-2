from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from stocks.data import (
    CanonicalMetadata,
    merge_canonical_frames,
    write_canonical_parquet,
)

BASE_URL = "https://eodhd.com/api"

INTRADAY_MAX_DAYS = {
    "1m": 120,
    "5m": 600,
    "1h": 7200,
}

REQUIRED_OHLCV = (
    "open",
    "high",
    "low",
    "close",
    "volume",
)


def load_local_env(
    path: Path = Path(".env"),
) -> None:
    if not path.exists():
        return

    for raw in path.read_text(
        encoding="utf-8",
    ).splitlines():
        line = raw.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split(
            "=",
            1,
        )

        os.environ.setdefault(
            key.strip(),
            value.strip()
            .strip('"')
            .strip("'"),
        )


def ticker_for(
    symbol: str,
    exchange: str,
) -> str:
    normalized = (
        symbol
        .strip()
        .upper()
    )

    return (
        normalized
        if "." in normalized
        else f"{normalized}.{exchange.upper()}"
    )


def request_intraday_chunk(
    client: httpx.Client,
    token: str,
    ticker: str,
    interval: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    response = client.get(
        f"{BASE_URL}/intraday/{ticker}",
        params={
            "api_token": token,
            "interval": interval,
            "fmt": "json",
            "from": int(start.timestamp()),
            "to": int(end.timestamp()),
        },
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(
        payload,
        list,
    ):
        raise RuntimeError(
            f"{ticker}: unexpected EODHD payload: "
            f"{payload}"
        )

    if not payload:
        return pd.DataFrame()

    frame = pd.DataFrame(
        payload
    )

    if "timestamp" not in frame.columns:
        raise ValueError(
            f"{ticker}: timestamp missing from "
            f"intraday payload"
        )

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        unit="s",
        utc=True,
        errors="coerce",
    )

    if frame["timestamp"].isna().any():
        raise ValueError(
            f"{ticker}: invalid timestamps in "
            f"intraday payload"
        )

    return frame.set_index(
        "timestamp"
    )


def request_eod(
    client: httpx.Client,
    token: str,
    ticker: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    response = client.get(
        f"{BASE_URL}/eod/{ticker}",
        params={
            "api_token": token,
            "fmt": "json",
            "from": start.date().isoformat(),
            "to": end.date().isoformat(),
            "period": "d",
        },
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(
        payload,
        list,
    ):
        raise RuntimeError(
            f"{ticker}: unexpected EODHD payload: "
            f"{payload}"
        )

    if not payload:
        return pd.DataFrame()

    frame = pd.DataFrame(
        payload
    )

    if "date" not in frame.columns:
        raise ValueError(
            f"{ticker}: date missing "
            f"from EOD payload"
        )

    frame["timestamp"] = pd.to_datetime(
        frame["date"],
        utc=True,
        errors="coerce",
    )

    if frame["timestamp"].isna().any():
        raise ValueError(
            f"{ticker}: invalid EOD dates"
        )

    return frame.set_index(
        "timestamp"
    )


def clean_provider_chunk(
    frame: pd.DataFrame,
    *,
    ticker: str,
    interval: str,
    chunk_start: pd.Timestamp,
    chunk_end: pd.Timestamp,
    max_drop_fraction: float,
    quarantine_dir: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if frame.empty:
        return frame, {
            "ticker": ticker,
            "interval": interval,
            "rows_raw": 0,
            "rows_clean": 0,
            "rows_dropped": 0,
            "drop_fraction": 0.0,
            "missing_by_column": {},
        }

    work = frame.copy()

    work.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        for column in work.columns
    ]

    missing_columns = [
        column
        for column in REQUIRED_OHLCV
        if column not in work.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{ticker}: provider missing OHLCV columns: "
            f"{missing_columns}"
        )

    for column in REQUIRED_OHLCV:
        work[column] = pd.to_numeric(
            work[column],
            errors="coerce",
        )

    missing_by_column = {
        column: int(
            work[column]
            .isna()
            .sum()
        )
        for column in REQUIRED_OHLCV
    }

    bad_mask = (
        work[
            list(REQUIRED_OHLCV)
        ]
        .isna()
        .any(axis=1)
    )

    bad_rows = work.loc[
        bad_mask
    ].copy()

    good_rows = work.loc[
        ~bad_mask
    ].copy()

    raw_count = len(
        work
    )

    bad_count = len(
        bad_rows
    )

    drop_fraction = (
        bad_count / raw_count
        if raw_count
        else 0.0
    )

    audit = {
        "ticker": ticker,
        "interval": interval,
        "chunk_start": (
            chunk_start.isoformat()
        ),
        "chunk_end": (
            chunk_end.isoformat()
        ),
        "rows_raw": raw_count,
        "rows_clean": len(
            good_rows
        ),
        "rows_dropped": bad_count,
        "drop_fraction": (
            drop_fraction
        ),
        "missing_by_column": (
            missing_by_column
        ),
    }

    if bad_count:
        quarantine_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        start_epoch = int(
            chunk_start.timestamp()
        )

        safe_ticker = (
            ticker.replace(
                ".",
                "_",
            )
        )

        quarantine_path = (
            quarantine_dir
            / (
                f"{safe_ticker}_"
                f"{interval}_"
                f"{start_epoch}_"
                f"invalid.parquet"
            )
        )

        bad_rows.to_parquet(
            quarantine_path,
            index=True,
        )

        audit[
            "quarantine_path"
        ] = str(
            quarantine_path
        )

    print(
        "PROVIDER_QUALITY "
        f"{ticker} "
        f"{interval} "
        f"raw={raw_count} "
        f"clean={len(good_rows)} "
        f"dropped={bad_count} "
        f"fraction={drop_fraction:.6f} "
        f"missing={missing_by_column}"
    )

    if (
        drop_fraction
        >
        max_drop_fraction
    ):
        raise ValueError(
            f"{ticker}: provider quality failure: "
            f"drop_fraction={drop_fraction:.6f} "
            f"> max={max_drop_fraction:.6f}; "
            f"missing_by_column={missing_by_column}"
        )

    if good_rows.empty:
        raise ValueError(
            f"{ticker}: no valid OHLCV rows "
            f"remain after provider cleaning"
        )

    return (
        good_rows,
        audit,
    )


def download(
    token: str,
    ticker: str,
    timeframe: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    max_drop_fraction: float,
    quarantine_dir: Path,
) -> tuple[
    pd.DataFrame,
    int,
    list[dict[str, Any]],
]:
    chunks: list[
        pd.DataFrame
    ] = []

    audits: list[
        dict[str, Any]
    ] = []

    requests = 0

    with httpx.Client(
        timeout=60.0,
        follow_redirects=True,
    ) as client:
        if timeframe == "1d":
            raw = request_eod(
                client,
                token,
                ticker,
                start,
                end,
            )

            clean, audit = (
                clean_provider_chunk(
                    raw,
                    ticker=ticker,
                    interval=timeframe,
                    chunk_start=start,
                    chunk_end=end,
                    max_drop_fraction=(
                        max_drop_fraction
                    ),
                    quarantine_dir=(
                        quarantine_dir
                    ),
                )
            )

            chunks.append(
                clean
            )

            audits.append(
                audit
            )

            requests = 1

        else:
            max_days = (
                INTRADAY_MAX_DAYS[
                    timeframe
                ]
            )

            cursor = start

            while cursor < end:
                chunk_end = min(
                    cursor
                    + pd.Timedelta(
                        days=max_days
                    ),
                    end,
                )

                print(
                    f"FETCH {ticker} "
                    f"{timeframe} "
                    f"{cursor.isoformat()} "
                    f"-> "
                    f"{chunk_end.isoformat()}"
                )

                raw = (
                    request_intraday_chunk(
                        client,
                        token,
                        ticker,
                        timeframe,
                        cursor,
                        chunk_end,
                    )
                )

                if not raw.empty:
                    clean, audit = (
                        clean_provider_chunk(
                            raw,
                            ticker=ticker,
                            interval=(
                                timeframe
                            ),
                            chunk_start=cursor,
                            chunk_end=chunk_end,
                            max_drop_fraction=(
                                max_drop_fraction
                            ),
                            quarantine_dir=(
                                quarantine_dir
                            ),
                        )
                    )

                    chunks.append(
                        clean
                    )

                    audits.append(
                        audit
                    )

                requests += 1

                cursor = (
                    chunk_end
                    + pd.Timedelta(
                        seconds=1
                    )
                )

    merged = (
        merge_canonical_frames(
            chunks
        )
    )

    if merged.empty:
        raise ValueError(
            f"{ticker}: no market data returned"
        )

    return (
        merged,
        requests,
        audits,
    )


def main() -> None:
    load_local_env()

    parser = argparse.ArgumentParser(
        description=(
            "Download EODHD data into "
            "canonical OHLCV"
        )
    )

    parser.add_argument(
        "--symbols",
        nargs="+",
        required=True,
    )

    parser.add_argument(
        "--exchange",
        default="US",
    )

    parser.add_argument(
        "--timeframe",
        choices=[
            "1m",
            "5m",
            "1h",
            "1d",
        ],
        default="1h",
    )

    parser.add_argument(
        "--start",
        required=True,
    )

    parser.add_argument(
        "--end",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "data/processed"
        ),
    )

    parser.add_argument(
        "--max-drop-fraction",
        type=float,
        default=0.02,
    )

    args = parser.parse_args()

    if not (
        0.0
        <= args.max_drop_fraction
        <= 1.0
    ):
        raise SystemExit(
            "ERROR: invalid "
            "--max-drop-fraction"
        )

    token = (
        os.environ
        .get(
            "EODHD_API_KEY",
            "",
        )
        .strip()
    )

    if not token:
        raise SystemExit(
            "ERROR: EODHD_API_KEY "
            "is missing from .env"
        )

    start = pd.Timestamp(
        args.start
    )

    start = (
        start.tz_localize(
            "UTC"
        )
        if start.tzinfo is None
        else start.tz_convert(
            "UTC"
        )
    )

    end = (
        pd.Timestamp(
            args.end
        )
        if args.end
        else pd.Timestamp.now(
            tz="UTC"
        )
    )

    end = (
        end.tz_localize(
            "UTC"
        )
        if end.tzinfo is None
        else end.tz_convert(
            "UTC"
        )
    )

    if end <= start:
        raise SystemExit(
            "ERROR: --end must be "
            "after --start"
        )

    quarantine_dir = (
        args.output_dir.parent
        / "quarantine"
        / "eodhd"
    )

    failures = 0

    for symbol in args.symbols:
        ticker = ticker_for(
            symbol,
            args.exchange,
        )

        short_symbol = (
            ticker.split(
                "."
            )[0]
        )

        try:
            (
                frame,
                request_count,
                audits,
            ) = download(
                token,
                ticker,
                args.timeframe,
                start,
                end,
                max_drop_fraction=(
                    args.max_drop_fraction
                ),
                quarantine_dir=(
                    quarantine_dir
                ),
            )

            output = (
                args.output_dir
                / (
                    f"{short_symbol}_"
                    f"{args.timeframe}"
                    f".parquet"
                )
            )

            write_canonical_parquet(
                frame,
                output,
                CanonicalMetadata(
                    symbol=short_symbol,
                    exchange=(
                        args.exchange.upper()
                    ),
                    timeframe=(
                        args.timeframe
                    ),
                    source="EODHD",
                    adjustment="raw",
                    provenance={
                        "ticker": ticker,
                        "endpoint": (
                            "eod"
                            if args.timeframe
                            == "1d"
                            else "intraday"
                        ),
                        "provider_rows_are_not_filled": (
                            True
                        ),
                    },
                ),
                extra_metadata={
                    "request_count": (
                        request_count
                    ),
                    "provider_quality": (
                        audits
                    ),
                },
            )

            print(
                f"SAVED {ticker} "
                f"rows={len(frame)} "
                f"start={frame.index.min()} "
                f"end={frame.index.max()} "
                f"path={output}"
            )

        except Exception as exc:
            failures += 1

            print(
                f"FAILED {ticker}: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

    if (
        failures
        ==
        len(args.symbols)
    ):
        raise SystemExit(2)

    if failures:
        print(
            "PARTIAL_SUCCESS "
            f"failed={failures} "
            f"succeeded="
            f"{len(args.symbols)-failures}"
        )


if __name__ == "__main__":
    main()
