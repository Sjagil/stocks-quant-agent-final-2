from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

from stocks.data.canonical import (
    CanonicalMetadata,
    canonicalize_ohlcv,
    read_canonical_parquet,
    validate_canonical,
    write_canonical_parquet,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def aggregate_rth(
    frame: pd.DataFrame,
    *,
    source_minutes: int,
    target_minutes: int = 15,
) -> tuple[pd.DataFrame, dict]:
    if (
        target_minutes
        % source_minutes
        != 0
    ):
        raise ValueError(
            "target timeframe must be "
            "divisible by source timeframe"
        )

    work = canonicalize_ohlcv(
        frame
    )

    validate_canonical(
        work
    )

    calendar = (
        mcal.get_calendar(
            "NYSE"
        )
    )

    schedule = calendar.schedule(
        start_date=(
            work.index.min()
            .date()
        ),
        end_date=(
            work.index.max()
            .date()
        ),
    )

    required_subbars = (
        target_minutes
        // source_minutes
    )

    output: list[
        pd.DataFrame
    ] = []

    expected_bars = 0
    incomplete_bars = 0

    for _, session in (
        schedule.iterrows()
    ):
        market_open = pd.Timestamp(
            session[
                "market_open"
            ]
        ).tz_convert(
            "UTC"
        )

        market_close = pd.Timestamp(
            session[
                "market_close"
            ]
        ).tz_convert(
            "UTC"
        )

        duration_minutes = int(
            (
                market_close
                -
                market_open
            ).total_seconds()
            // 60
        )

        expected_bars += (
            duration_minutes
            // target_minutes
        )

        day = work.loc[
            (work.index >= market_open)
            &
            (work.index < market_close)
        ].copy()

        if day.empty:
            continue

        offset_minutes = (
            (
                day.index
                -
                market_open
            )
            .total_seconds()
            / 60.0
        )

        source_alignment = (
            np.mod(
                offset_minutes,
                source_minutes,
            )
            < 1e-9
        )

        day = day.loc[
            source_alignment
        ].copy()

        offset_minutes = (
            (
                day.index
                -
                market_open
            )
            .total_seconds()
            / 60.0
        )

        day[
            "__bucket"
        ] = (
            offset_minutes
            // target_minutes
        ).astype(int)

        for bucket, group in (
            day.groupby(
                "__bucket",
                sort=True,
            )
        ):
            group = (
                group.sort_index()
            )

            if (
                len(group)
                != required_subbars
            ):
                incomplete_bars += 1
                continue

            timestamp = (
                market_open
                + pd.Timedelta(
                    minutes=(
                        int(bucket)
                        * target_minutes
                    )
                )
            )

            bar = pd.DataFrame(
                {
                    "open": [
                        float(
                            group[
                                "open"
                            ].iloc[0]
                        )
                    ],
                    "high": [
                        float(
                            group[
                                "high"
                            ].max()
                        )
                    ],
                    "low": [
                        float(
                            group[
                                "low"
                            ].min()
                        )
                    ],
                    "close": [
                        float(
                            group[
                                "close"
                            ].iloc[-1]
                        )
                    ],
                    "volume": [
                        float(
                            group[
                                "volume"
                            ].sum()
                        )
                    ],
                },
                index=pd.DatetimeIndex(
                    [timestamp],
                    name="timestamp",
                ),
            )

            output.append(
                bar
            )

    if not output:
        raise ValueError(
            "no complete RTH 15m bars "
            "could be constructed"
        )

    result = pd.concat(
        output
    ).sort_index()

    result = canonicalize_ohlcv(
        result
    )

    validate_canonical(
        result
    )

    coverage = (
        len(result)
        / expected_bars
        if expected_bars
        else 0.0
    )

    audit = {
        "source_minutes": (
            source_minutes
        ),
        "target_minutes": (
            target_minutes
        ),
        "session": "NYSE_RTH",
        "required_subbars": (
            required_subbars
        ),
        "expected_15m_bars": (
            expected_bars
        ),
        "actual_15m_bars": (
            len(result)
        ),
        "coverage": (
            coverage
        ),
        "incomplete_bars_dropped": (
            incomplete_bars
        ),
        "forward_fill": False,
        "fabricated_volume": False,
    }

    return (
        result,
        audit,
    )


def source_for(
    symbol: str,
) -> tuple[
    Path,
    int,
]:
    candidates = (
        (
            ROOT
            / "data"
            / "processed"
            / f"{symbol}_5m.parquet",
            5,
        ),
        (
            ROOT
            / "data"
            / "processed"
            / f"{symbol}_1m.parquet",
            1,
        ),
    )

    for path, minutes in candidates:
        if path.is_file():
            return (
                path,
                minutes,
            )

    raise FileNotFoundError(
        f"{symbol}: neither 5m nor "
        f"1m canonical data exists"
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        nargs="+",
        required=True,
    )

    parser.add_argument(
        "--min-coverage",
        type=float,
        default=0.95,
    )

    args = parser.parse_args()

    failures = 0

    for raw_symbol in args.symbols:
        symbol = (
            raw_symbol
            .strip()
            .upper()
        )

        try:
            source_path, minutes = (
                source_for(
                    symbol
                )
            )

            frame, metadata = (
                read_canonical_parquet(
                    source_path
                )
            )

            result, audit = (
                aggregate_rth(
                    frame,
                    source_minutes=(
                        minutes
                    ),
                )
            )

            if (
                audit[
                    "coverage"
                ]
                <
                args.min_coverage
            ):
                raise ValueError(
                    f"{symbol}: RTH 15m "
                    f"coverage too low: "
                    f"{audit['coverage']:.4%}"
                )

            output = (
                ROOT
                / "data"
                / "derived"
                / f"{symbol}_15m.parquet"
            )

            write_canonical_parquet(
                result,
                output,
                CanonicalMetadata(
                    symbol=symbol,
                    exchange="US",
                    timeframe="15m",
                    source="DERIVED",
                    adjustment=(
                        str(
                            (
                                metadata
                                or {}
                            ).get(
                                "adjustment",
                                "raw",
                            )
                        )
                    ),
                    provenance={
                        "source_path": (
                            str(
                                source_path
                            )
                        ),
                        "source_timeframe": (
                            f"{minutes}m"
                        ),
                        "session": (
                            "NYSE_RTH"
                        ),
                        "complete_subbars_only": (
                            True
                        ),
                    },
                ),
                extra_metadata={
                    "aggregation": (
                        audit
                    )
                },
            )

            print(
                json.dumps(
                    {
                        "symbol": symbol,
                        "source": (
                            str(
                                source_path
                            )
                        ),
                        "source_minutes": (
                            minutes
                        ),
                        "rows": (
                            len(result)
                        ),
                        **audit,
                        "output": (
                            str(output)
                        ),
                    },
                    indent=2,
                )
            )

        except Exception as exc:
            failures += 1

            print(
                f"FAILED {symbol}: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

    return (
        0
        if failures == 0
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
