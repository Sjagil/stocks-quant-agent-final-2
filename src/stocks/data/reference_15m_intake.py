from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

from stocks.data.canonical import (
    CanonicalMetadata,
    canonicalize_ohlcv,
    validate_canonical,
    write_canonical_parquet,
)


def utc_timestamp(
    value: str | pd.Timestamp | None,
) -> pd.Timestamp:
    if value is None:
        return pd.Timestamp.now(
            tz="UTC"
        )

    timestamp = pd.Timestamp(
        value
    )

    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(
            "UTC"
        )
    else:
        timestamp = timestamp.tz_convert(
            "UTC"
        )

    return timestamp


def load_reference_15m(
    index_path: str | Path,
    *,
    provider: str,
    symbol: str,
) -> tuple[pd.DataFrame, Path]:
    index_path = (
        Path(index_path)
        .expanduser()
        .resolve()
    )

    payload = json.loads(
        index_path.read_text(
            encoding="utf-8"
        )
    )

    provider = provider.upper()
    symbol = symbol.upper()

    matches = [
        row
        for row in payload.get(
            "bars",
            [],
        )
        if (
            str(
                row.get(
                    "provider",
                    "",
                )
            ).upper()
            == provider
            and str(
                row.get(
                    "symbol",
                    "",
                )
            ).upper()
            == symbol
            and str(
                row.get(
                    "interval",
                    "",
                )
            ).lower()
            == "15m"
            and str(
                row.get(
                    "source_interval",
                    "",
                )
            ).lower()
            == "15m"
        )
    ]

    if len(matches) != 1:
        raise ValueError(
            f"{provider} {symbol}: "
            f"expected one native 15m "
            f"variant, found {len(matches)}"
        )

    path = (
        Path(
            str(
                matches[0][
                    "path"
                ]
            )
        )
        .expanduser()
        .resolve()
    )

    if not path.is_relative_to(
        index_path.parent
    ):
        raise ValueError(
            "reference data path escapes "
            "integration run directory"
        )

    if not path.is_file():
        raise FileNotFoundError(
            path
        )

    raw = pd.read_parquet(
        path
    )

    if "quality_status" in raw:
        raw = raw.loc[
            raw[
                "quality_status"
            ]
            .astype(str)
            .eq(
                "VALIDATED_OHLC"
            )
        ]

    if "is_partial" in raw:
        raw = raw.loc[
            ~raw[
                "is_partial"
            ]
            .fillna(True)
            .astype(bool)
        ]

    if "timestamp_utc" not in raw:
        raise ValueError(
            f"{provider} {symbol}: "
            "timestamp_utc missing"
        )

    index = pd.DatetimeIndex(
        pd.to_datetime(
            raw[
                "timestamp_utc"
            ],
            utc=True,
            errors="coerce",
        )
    )

    if index.isna().any():
        raise ValueError(
            f"{provider} {symbol}: "
            "invalid timestamps"
        )

    frame = raw[
        [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ].copy()

    frame.index = index
    frame.index.name = "timestamp"

    frame = canonicalize_ohlcv(
        frame
    )

    validate_canonical(
        frame
    )

    return frame, path


def closed_rth_15m(
    frame: pd.DataFrame,
    *,
    as_of: str | pd.Timestamp | None,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    work = canonicalize_ohlcv(
        frame
    )

    validate_canonical(
        work
    )

    as_of_timestamp = utc_timestamp(
        as_of
    )

    calendar = mcal.get_calendar(
        "NYSE"
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

    pieces = []
    expected_closed_bars = 0

    bar_size = pd.Timedelta(
        minutes=15
    )

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

        cutoff = min(
            market_close,
            as_of_timestamp,
        )

        if cutoff <= market_open:
            continue

        expected = pd.date_range(
            start=market_open,
            end=(
                market_close
                - bar_size
            ),
            freq="15min",
        )

        expected = expected[
            (
                expected
                + bar_size
            )
            <= cutoff
        ]

        expected_closed_bars += len(
            expected
        )

        if len(expected) == 0:
            continue

        day = work.loc[
            work.index.isin(
                expected
            )
        ].copy()

        if not day.empty:
            pieces.append(
                day
            )

    if not pieces:
        raise ValueError(
            "no closed exact-grid "
            "NYSE RTH 15m bars"
        )

    result = canonicalize_ohlcv(
        pd.concat(
            pieces
        ).sort_index()
    )

    validate_canonical(
        result
    )

    coverage = (
        len(result)
        / expected_closed_bars
        if expected_closed_bars
        else 0.0
    )

    return (
        result,
        {
            "session": "NYSE_RTH",
            "timeframe": "15m",
            "as_of": (
                as_of_timestamp
                .isoformat()
            ),
            "expected_closed_bars": (
                int(
                    expected_closed_bars
                )
            ),
            "actual_closed_bars": (
                int(
                    len(result)
                )
            ),
            "coverage": float(
                coverage
            ),
            "closed_bars_only": True,
            "exact_15m_grid": True,
            "extended_hours_removed": True,
            "forward_fill": False,
            "provider_averaging": False,
        },
    )


def overlap_audit(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    bad_row_threshold_bps: float = 100.0,
) -> dict[str, Any]:
    common = (
        left.index
        .intersection(
            right.index
        )
    )

    empty = {
        "overlap_rows": 0,
        "median_close_difference_bps": None,
        "p95_close_difference_bps": None,
        "p99_close_difference_bps": None,
        "max_close_difference_bps": None,
        "bad_row_threshold_bps": float(
            bad_row_threshold_bps
        ),
        "bad_rows": 0,
        "bad_fraction": 0.0,
    }

    if len(common) == 0:
        return empty

    left_close = (
        left.loc[
            common,
            "close",
        ]
        .astype(float)
    )

    right_close = (
        right.loc[
            common,
            "close",
        ]
        .astype(float)
    )

    denominator = (
        pd.concat(
            [
                left_close.abs(),
                right_close.abs(),
            ],
            axis=1,
        )
        .mean(
            axis=1
        )
        .replace(
            0.0,
            np.nan,
        )
    )

    difference = (
        (
            left_close
            - right_close
        )
        .abs()
        / denominator
        * 10000.0
    ).dropna()

    if difference.empty:
        return empty

    bad = (
        difference
        > float(
            bad_row_threshold_bps
        )
    )

    return {
        "overlap_rows": int(
            len(difference)
        ),
        "median_close_difference_bps": float(
            difference.median()
        ),
        "p95_close_difference_bps": float(
            difference.quantile(
                0.95
            )
        ),
        "p99_close_difference_bps": float(
            difference.quantile(
                0.99
            )
        ),
        "max_close_difference_bps": float(
            difference.max()
        ),
        "bad_row_threshold_bps": float(
            bad_row_threshold_bps
        ),
        "bad_rows": int(
            bad.sum()
        ),
        "bad_fraction": float(
            bad.mean()
        ),
    }


def overlap_is_compatible(
    audit: dict[str, Any],
    *,
    min_overlap_rows: int = 5,
    max_median_bps: float = 50.0,
    max_p95_bps: float | None = None,
    max_bad_fraction: float | None = None,
) -> bool:
    if (
        int(
            audit.get(
                "overlap_rows",
                0,
            )
        )
        < int(
            min_overlap_rows
        )
    ):
        return False

    median = audit.get(
        "median_close_difference_bps"
    )

    if (
        median is None
        or float(median)
        > float(
            max_median_bps
        )
    ):
        return False

    if max_p95_bps is not None:
        p95 = audit.get(
            "p95_close_difference_bps"
        )

        if (
            p95 is None
            or float(p95)
            > float(
                max_p95_bps
            )
        ):
            return False

    if max_bad_fraction is not None:
        fraction = float(
            audit.get(
                "bad_fraction",
                1.0,
            )
        )

        if (
            fraction
            > float(
                max_bad_fraction
            )
        ):
            return False

    return True


def require_compatible_overlap(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    max_median_bps: float,
    max_p95_bps: float | None = None,
    max_bad_fraction: float | None = None,
    bad_row_threshold_bps: float = 100.0,
    min_overlap_rows: int = 5,
) -> dict[str, Any]:
    audit = overlap_audit(
        left,
        right,
        bad_row_threshold_bps=(
            bad_row_threshold_bps
        ),
    )

    compatible = overlap_is_compatible(
        audit,
        min_overlap_rows=(
            min_overlap_rows
        ),
        max_median_bps=(
            max_median_bps
        ),
        max_p95_bps=(
            max_p95_bps
        ),
        max_bad_fraction=(
            max_bad_fraction
        ),
    )

    if compatible:
        return audit

    raise ValueError(
        "material provider divergence: "
        f"rows={audit['overlap_rows']} "
        f"median="
        f"{audit['median_close_difference_bps']}bps "
        f"p95="
        f"{audit['p95_close_difference_bps']}bps "
        f"p99="
        f"{audit['p99_close_difference_bps']}bps "
        f"bad_fraction="
        f"{audit['bad_fraction']:.4%}"
    )


def existing_base(
    project_root: str | Path,
    symbol: str,
) -> tuple[
    pd.DataFrame | None,
    Path | None,
]:
    root = (
        Path(project_root)
        .resolve()
    )

    symbol = symbol.upper()

    candidates = (
        root
        / "data"
        / "canonical"
        / "provider_fabric"
        / f"{symbol}_15m.parquet",
        root
        / "data"
        / "derived"
        / f"{symbol}_15m.parquet",
        root
        / "data"
        / "processed"
        / f"{symbol}_15m.parquet",
        root
        / "data"
        / "adjusted"
        / f"{symbol}_15m.parquet",
    )

    for path in candidates:
        if not path.is_file():
            continue

        frame = canonicalize_ohlcv(
            pd.read_parquet(
                path
            )
        )

        validate_canonical(
            frame
        )

        return frame, path

    return None, None


def append_newer_only(
    base: pd.DataFrame | None,
    incoming: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    if (
        base is None
        or base.empty
    ):
        result = incoming.copy()

        return (
            result,
            result.copy(),
        )

    appended = incoming.loc[
        incoming.index
        > base.index.max()
    ].copy()

    if appended.empty:
        return (
            base.copy(),
            appended,
        )

    result = canonicalize_ohlcv(
        pd.concat(
            [
                base,
                appended,
            ]
        ).sort_index()
    )

    validate_canonical(
        result
    )

    return (
        result,
        appended,
    )


def build_reference_15m(
    project_root: str | Path,
    index_path: str | Path,
    symbol: str,
    *,
    as_of: str | pd.Timestamp | None,
    min_provider_coverage: float = 0.95,
    max_overlap_median_bps: float = 50.0,
) -> dict[str, Any]:
    root = (
        Path(project_root)
        .resolve()
    )

    index_path = (
        Path(index_path)
        .expanduser()
        .resolve()
    )

    symbol = symbol.upper()

    eodhd_raw, eodhd_path = (
        load_reference_15m(
            index_path,
            provider="EODHD",
            symbol=symbol,
        )
    )

    yahoo_raw, yahoo_path = (
        load_reference_15m(
            index_path,
            provider="YFINANCE",
            symbol=symbol,
        )
    )

    eodhd, eodhd_audit = (
        closed_rth_15m(
            eodhd_raw,
            as_of=as_of,
        )
    )

    yahoo, yahoo_audit = (
        closed_rth_15m(
            yahoo_raw,
            as_of=as_of,
        )
    )

    for provider, audit in (
        (
            "EODHD",
            eodhd_audit,
        ),
        (
            "YFINANCE",
            yahoo_audit,
        ),
    ):
        if (
            audit[
                "coverage"
            ]
            < min_provider_coverage
        ):
            raise ValueError(
                f"{symbol}: {provider} "
                f"closed-RTH coverage "
                f"{audit['coverage']:.4%} "
                f"< "
                f"{min_provider_coverage:.4%}"
            )

    base, base_path = (
        existing_base(
            root,
            symbol,
        )
    )

    if base is not None:
        base, base_audit = (
            closed_rth_15m(
                base,
                as_of=as_of,
            )
        )

        base_eodhd_audit = (
            require_compatible_overlap(
                base,
                eodhd,
                max_median_bps=(
                    max_overlap_median_bps
                ),
            )
        )
    else:
        base_audit = None

        base_eodhd_audit = {
            "overlap_rows": 0,
        }

    eodhd_yahoo_audit = (
        require_compatible_overlap(
            eodhd,
            yahoo,
            max_median_bps=(
                max_overlap_median_bps
            ),
        )
    )

    combined, appended_eodhd = (
        append_newer_only(
            base,
            eodhd,
        )
    )

    combined, appended_yahoo = (
        append_newer_only(
            combined,
            yahoo,
        )
    )

    target = (
        root
        / "data"
        / "canonical"
        / "provider_fabric"
        / f"{symbol}_15m.parquet"
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    provenance = pd.DataFrame(
        {
            "source_provider": (
                "EXISTING_CANONICAL_BASE"
            ),
            "source_path": (
                str(
                    base_path
                    or ""
                )
            ),
        },
        index=(
            base.index
            if base is not None
            else pd.DatetimeIndex(
                [],
                tz="UTC",
            )
        ),
    )

    if not appended_eodhd.empty:
        provenance = pd.concat(
            [
                provenance,
                pd.DataFrame(
                    {
                        "source_provider": (
                            "EODHD"
                        ),
                        "source_path": (
                            str(
                                eodhd_path
                            )
                        ),
                    },
                    index=(
                        appended_eodhd
                        .index
                    ),
                ),
            ]
        )

    if not appended_yahoo.empty:
        provenance = pd.concat(
            [
                provenance,
                pd.DataFrame(
                    {
                        "source_provider": (
                            "YFINANCE"
                        ),
                        "source_path": (
                            str(
                                yahoo_path
                            )
                        ),
                    },
                    index=(
                        appended_yahoo
                        .index
                    ),
                ),
            ]
        )

    provenance = (
        provenance
        .loc[
            ~provenance.index
            .duplicated(
                keep="first"
            )
        ]
        .sort_index()
        .reindex(
            combined.index
        )
    )

    write_canonical_parquet(
        combined,
        target,
        CanonicalMetadata(
            symbol=symbol,
            exchange="US",
            timeframe="15m",
            source=(
                "REFERENCE_PROVIDER_FABRIC"
            ),
            adjustment=(
                "provider_compatibility_checked"
            ),
            provenance={
                "reference_index": (
                    str(
                        index_path
                    )
                ),
                "base_path": (
                    str(
                        base_path
                    )
                    if base_path
                    else None
                ),
                "provider_priority": [
                    "EXISTING_CANONICAL_BASE",
                    "EODHD",
                    "YFINANCE_FRESH_TAIL",
                ],
                "silent_provider_blending": (
                    False
                ),
                "provider_averaging": (
                    False
                ),
                "append_newer_only": (
                    True
                ),
                "closed_rth_only": (
                    True
                ),
            },
        ),
        extra_metadata={
            "base": base_audit,
            "eodhd": eodhd_audit,
            "yfinance": yahoo_audit,
            "base_vs_eodhd": (
                base_eodhd_audit
            ),
            "eodhd_vs_yfinance": (
                eodhd_yahoo_audit
            ),
            "appended_eodhd_rows": (
                int(
                    len(
                        appended_eodhd
                    )
                )
            ),
            "appended_yfinance_rows": (
                int(
                    len(
                        appended_yahoo
                    )
                )
            ),
        },
    )

    provenance_path = (
        target.with_name(
            target.stem
            + ".provenance.parquet"
        )
    )

    provenance.to_parquet(
        provenance_path
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
        "last": (
            combined.index.max()
            .isoformat()
        ),
        "base_path": (
            str(base_path)
            if base_path
            else None
        ),
        "appended_eodhd_rows": (
            int(
                len(
                    appended_eodhd
                )
            )
        ),
        "appended_yfinance_rows": (
            int(
                len(
                    appended_yahoo
                )
            )
        ),
        "eodhd_coverage": (
            eodhd_audit[
                "coverage"
            ]
        ),
        "yfinance_coverage": (
            yahoo_audit[
                "coverage"
            ]
        ),
        "eodhd_yfinance_overlap": (
            eodhd_yahoo_audit
        ),
        "output": str(
            target
        ),
        "provenance": str(
            provenance_path
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }
