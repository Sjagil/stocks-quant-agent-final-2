from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pandas_market_calendars as mcal

from stocks.data.canonical import (
    CanonicalMetadata,
    canonicalize_ohlcv,
    read_canonical_parquet,
    validate_canonical,
    write_canonical_parquet,
)
from stocks.data.reference_15m_intake import (
    require_compatible_overlap,
)


def _utc_timestamp(
    value: str | pd.Timestamp | None,
) -> pd.Timestamp:
    if value is None:
        return pd.Timestamp.now(
            tz="UTC"
        )

    result = pd.Timestamp(
        value
    )

    if result.tzinfo is None:
        return result.tz_localize(
            "UTC"
        )

    return result.tz_convert(
        "UTC"
    )


def aggregate_session_hourly(
    frame: pd.DataFrame,
    *,
    as_of: str | pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    work = canonicalize_ohlcv(
        frame
    )

    validate_canonical(
        work
    )

    as_of_timestamp = (
        _utc_timestamp(
            as_of
        )
    )

    calendar = mcal.get_calendar(
        "NYSE"
    )

    schedule = calendar.schedule(
        start_date=(
            work.index.min().date()
        ),
        end_date=(
            work.index.max().date()
        ),
    )

    source_delta = pd.Timedelta(
        minutes=15
    )

    target_delta = pd.Timedelta(
        hours=1
    )

    output = []

    expected_buckets = 0
    incomplete_buckets = 0

    for _, session in (
        schedule.iterrows()
    ):
        market_open = pd.Timestamp(
            session["market_open"]
        ).tz_convert(
            "UTC"
        )

        market_close = pd.Timestamp(
            session["market_close"]
        ).tz_convert(
            "UTC"
        )

        cutoff = min(
            market_close,
            as_of_timestamp,
        )

        bucket_start = market_open

        while (
            bucket_start
            < market_close
        ):
            bucket_end = min(
                bucket_start
                + target_delta,
                market_close,
            )

            if (
                bucket_end
                > cutoff
            ):
                bucket_start = (
                    bucket_start
                    + target_delta
                )
                continue

            expected = (
                pd.date_range(
                    start=bucket_start,
                    end=(
                        bucket_end
                        - source_delta
                    ),
                    freq="15min",
                )
            )

            expected_buckets += 1

            group = work.reindex(
                expected
            )

            if (
                len(group)
                != len(expected)
                or group[
                    [
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                    ]
                ].isna().any().any()
            ):
                incomplete_buckets += 1

                bucket_start = (
                    bucket_start
                    + target_delta
                )

                continue

            output.append(
                pd.DataFrame(
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
                        [
                            bucket_start
                        ],
                        name="timestamp",
                    ),
                )
            )

            bucket_start = (
                bucket_start
                + target_delta
            )

    if not output:
        raise ValueError(
            "no complete session-aligned "
            "hourly buckets"
        )

    result = canonicalize_ohlcv(
        pd.concat(
            output
        ).sort_index()
    )

    validate_canonical(
        result
    )

    coverage = (
        len(result)
        / expected_buckets
        if expected_buckets
        else 0.0
    )

    return (
        result,
        {
            "source_timeframe": "15m",
            "target_timeframe": "1h",
            "session": "NYSE_RTH",
            "expected_buckets": int(
                expected_buckets
            ),
            "actual_buckets": int(
                len(result)
            ),
            "incomplete_buckets": int(
                incomplete_buckets
            ),
            "coverage": float(
                coverage
            ),
            "final_partial_session_bucket": (
                True
            ),
            "forward_fill": False,
            "fabricated_volume": False,
            "as_of": (
                as_of_timestamp
                .isoformat()
            ),
        },
    )


def historical_hourly_source(
    root: Path,
    symbol: str,
) -> Path:
    candidates = (
        root
        / "data"
        / "adjusted"
        / f"{symbol}_1h.parquet",
        root
        / "data"
        / "derived"
        / f"{symbol}_1h.parquet",
        root
        / "data"
        / "processed"
        / f"{symbol}_1h.parquet",
    )

    for path in candidates:
        if path.is_file():
            return path

    raise FileNotFoundError(
        f"{symbol}: historical 1h "
        "base missing"
    )


def synchronize_hourly(
    project_root: str | Path,
    symbol: str,
    *,
    as_of: str | pd.Timestamp | None,
    min_coverage: float = 0.95,
    max_overlap_median_bps: float = 50.0,
) -> dict[str, Any]:
    root = (
        Path(project_root)
        .resolve()
    )

    symbol = symbol.upper()

    source_15m = (
        root
        / "data"
        / "canonical"
        / "provider_fabric"
        / f"{symbol}_15m.parquet"
    )

    if not source_15m.is_file():
        raise FileNotFoundError(
            source_15m
        )

    fifteen, _ = (
        read_canonical_parquet(
            source_15m
        )
    )

    derived, audit = (
        aggregate_session_hourly(
            fifteen,
            as_of=as_of,
        )
    )

    if (
        audit["coverage"]
        < min_coverage
    ):
        raise ValueError(
            f"{symbol}: synchronized 1h "
            f"coverage {audit['coverage']:.4%} "
            f"< {min_coverage:.4%}"
        )

    base_path = (
        historical_hourly_source(
            root,
            symbol,
        )
    )

    base, _ = (
        read_canonical_parquet(
            base_path
        )
    )

    overlap = (
        require_compatible_overlap(
            base,
            derived,
            max_median_bps=(
                max_overlap_median_bps
            ),
        )
    )

    switch_time = (
        derived.index.min()
    )

    historical_prefix = (
        base.loc[
            base.index
            < switch_time
        ].copy()
    )

    combined = (
        canonicalize_ohlcv(
            pd.concat(
                [
                    historical_prefix,
                    derived,
                ]
            ).sort_index()
        )
    )

    validate_canonical(
        combined
    )

    target = (
        root
        / "data"
        / "canonical"
        / "provider_fabric"
        / f"{symbol}_1h.parquet"
    )

    write_canonical_parquet(
        combined,
        target,
        CanonicalMetadata(
            symbol=symbol,
            exchange="US",
            timeframe="1h",
            source=(
                "SESSION_ALIGNED_15M_FABRIC"
            ),
            adjustment=(
                "historical_base_then_"
                "synchronized_15m_tail"
            ),
            provenance={
                "historical_base": (
                    str(
                        base_path
                    )
                ),
                "recent_15m_source": (
                    str(
                        source_15m
                    )
                ),
                "switch_time": (
                    switch_time
                    .isoformat()
                ),
                "recent_tail_replaces_overlap": (
                    True
                ),
                "session_aligned": True,
                "final_partial_bucket": (
                    True
                ),
                "provider_averaging": (
                    False
                ),
            },
        ),
        extra_metadata={
            "aggregation": audit,
            "overlap": overlap,
            "historical_prefix_rows": (
                int(
                    len(
                        historical_prefix
                    )
                )
            ),
            "derived_tail_rows": (
                int(
                    len(
                        derived
                    )
                )
            ),
        },
    )

    return {
        "symbol": symbol,
        "rows": int(
            len(combined)
        ),
        "first": (
            combined.index.min()
            .isoformat()
        ),
        "last_bar": (
            combined.index.max()
            .isoformat()
        ),
        "switch_time": (
            switch_time
            .isoformat()
        ),
        "derived_tail_rows": int(
            len(derived)
        ),
        "coverage": (
            audit["coverage"]
        ),
        "overlap": overlap,
        "output": str(
            target
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }
