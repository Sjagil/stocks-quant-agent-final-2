from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import httpx
import pandas as pd

from stocks.data.canonical import (
    CanonicalMetadata,
    SplitEvent,
    apply_split_adjustments,
    read_canonical_parquet,
    split_events_from_payload,
    write_canonical_parquet,
)
from stocks.data.reference_15m_intake import (
    overlap_audit,
    overlap_is_compatible,
)
from stocks.data.session_hourly import (
    aggregate_session_hourly,
    historical_hourly_source,
)


def utc_timestamp(
    value,
) -> pd.Timestamp:
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


def fetch_eodhd_split_events(
    *,
    token: str,
    ticker: str,
    start: str,
    end: str,
) -> tuple[SplitEvent, ...]:
    if not token.strip():
        raise ValueError(
            "EODHD token missing"
        )

    with httpx.Client(
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        response = client.get(
            (
                "https://eodhd.com/api/"
                f"splits/{ticker}"
            ),
            params={
                "api_token": token,
                "fmt": "json",
                "from": start,
                "to": end,
            },
        )

        response.raise_for_status()

        payload = response.json()

    if isinstance(
        payload,
        dict,
    ):
        payload = (
            payload.get(
                "splits"
            )
            or payload.get(
                "data"
            )
            or payload
        )

    if not isinstance(
        payload,
        list,
    ):
        raise ValueError(
            "unexpected EODHD "
            "split payload"
        )

    return split_events_from_payload(
        [
            dict(item)
            for item in payload
        ]
    )


def evaluate_split_candidates(
    raw_15m: pd.DataFrame,
    base_1h: pd.DataFrame,
    events: Sequence[SplitEvent],
    *,
    as_of,
    max_median_bps: float = 50.0,
    max_p95_bps: float = 100.0,
    max_bad_fraction: float = 0.01,
    bad_row_threshold_bps: float = 100.0,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    raw_hourly, _ = (
        aggregate_session_hourly(
            raw_15m,
            as_of=as_of,
        )
    )

    raw_audit = overlap_audit(
        base_1h,
        raw_hourly,
        bad_row_threshold_bps=(
            bad_row_threshold_bps
        ),
    )

    raw_ok = overlap_is_compatible(
        raw_audit,
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

    adjusted_15m = (
        apply_split_adjustments(
            raw_15m,
            events,
        )
    )

    adjusted_hourly, _ = (
        aggregate_session_hourly(
            adjusted_15m,
            as_of=as_of,
        )
    )

    adjusted_audit = overlap_audit(
        base_1h,
        adjusted_hourly,
        bad_row_threshold_bps=(
            bad_row_threshold_bps
        ),
    )

    adjusted_ok = overlap_is_compatible(
        adjusted_audit,
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

    if raw_ok:
        selected = "RAW_ALREADY_COMPATIBLE"
        selected_frame = raw_15m.copy()

    elif events and adjusted_ok:
        selected = "SPLIT_ADJUSTED"
        selected_frame = (
            adjusted_15m
        )

    else:
        raise ValueError(
            "no compatible corporate-action "
            "normalization candidate; "
            f"raw={raw_audit} "
            f"adjusted={adjusted_audit}"
        )

    return (
        selected_frame,
        {
            "selection": selected,
            "event_count": len(
                events
            ),
            "raw_overlap": (
                raw_audit
            ),
            "adjusted_overlap": (
                adjusted_audit
            ),
            "raw_compatible": (
                raw_ok
            ),
            "adjusted_compatible": (
                adjusted_ok
            ),
        },
    )


def reconcile_provider_splits(
    project_root: str | Path,
    *,
    symbol: str,
    ticker: str,
    token: str,
    as_of,
    max_median_bps: float = 50.0,
    max_p95_bps: float = 100.0,
    max_bad_fraction: float = 0.01,
) -> dict[str, Any]:
    root = Path(
        project_root
    ).resolve()

    symbol = symbol.upper()

    source = (
        root
        / "data"
        / "canonical"
        / "provider_fabric"
        / f"{symbol}_15m.parquet"
    )

    if not source.is_file():
        raise FileNotFoundError(
            source
        )

    raw, source_metadata = (
        read_canonical_parquet(
            source
        )
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

    as_of_timestamp = (
        utc_timestamp(
            as_of
        )
    )

    events = (
        fetch_eodhd_split_events(
            token=token,
            ticker=ticker,
            start=(
                raw.index.min()
                .date()
                .isoformat()
            ),
            end=(
                as_of_timestamp
                .date()
                .isoformat()
            ),
        )
    )

    selected_frame, audit = (
        evaluate_split_candidates(
            raw,
            base,
            events,
            as_of=as_of_timestamp,
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
    )

    if (
        audit["selection"]
        == "RAW_ALREADY_COMPATIBLE"
    ):
        output = source

    else:
        output = (
            root
            / "data"
            / "canonical"
            / "split_adjusted"
            / f"{symbol}_15m.parquet"
        )

        write_canonical_parquet(
            selected_frame,
            output,
            CanonicalMetadata(
                symbol=symbol,
                exchange=(
                    ticker.split(
                        ".",
                        1,
                    )[1]
                    if "." in ticker
                    else None
                ),
                timeframe="15m",
                source=(
                    "REFERENCE_PROVIDER_FABRIC"
                    "+EODHD_CORPORATE_ACTIONS"
                ),
                adjustment=(
                    "split_adjusted_latest_share_basis"
                ),
                provenance={
                    "source_path": str(
                        source
                    ),
                    "historical_hourly_base": str(
                        base_path
                    ),
                    "ticker": ticker,
                    "selection": (
                        audit[
                            "selection"
                        ]
                    ),
                },
            ),
            extra_metadata={
                "source_metadata": (
                    source_metadata
                ),
                "corporate_action_policy": (
                    "explicit_split_events_only"
                ),
                "split_events": [
                    {
                        "effective_at": (
                            event.effective_at
                            .isoformat()
                        ),
                        "factor": (
                            event.factor
                        ),
                        "raw": (
                            event.source_payload
                        ),
                    }
                    for event in events
                ],
                "reconciliation": audit,
            },
        )

    return {
        "symbol": symbol,
        "ticker": ticker,
        "source": str(
            source
        ),
        "historical_hourly_base": str(
            base_path
        ),
        "output": str(
            output
        ),
        "events": [
            {
                "effective_at": (
                    event.effective_at
                    .isoformat()
                ),
                "factor": (
                    event.factor
                ),
            }
            for event in events
        ],
        **audit,
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }
