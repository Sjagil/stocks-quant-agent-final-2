from __future__ import annotations

from datetime import timedelta

import json
from dataclasses import (
    asdict,
    dataclass,
)
from datetime import (
    date,
    timedelta,
)
from pathlib import Path
from uuid import uuid4

import pandas as pd

from stocks.data.canonical import (
    canonicalize_ohlcv,
    validate_canonical,
)
from stocks.data.reference_15m_intake import (
    closed_rth_15m,
)
from stocks.providers.eodhd import (
    fetch_intraday_5m,
    utc_timestamp,
)
from stocks.providers.env import (
    load_project_env,
    secret,
)


@dataclass(frozen=True)
class AggregationAudit:
    source_interval: str
    target_interval: str
    source_rows: int
    complete_target_rows: int
    incomplete_bucket_count: int
    exact_5m_grid: bool
    forward_fill: bool
    provider_averaging: bool

    def to_dict(
        self,
    ) -> dict:
        return asdict(self)


def cli_date_window(
    start: str,
    end: str,
) -> tuple[
    pd.Timestamp,
    pd.Timestamp,
]:
    start_date = date.fromisoformat(
        str(start)
    )

    end_date = date.fromisoformat(
        str(end)
    )

    if start_date > end_date:
        raise ValueError(
            "start must be on or before end"
        )

    return (
        pd.Timestamp(
            start_date,
            tz="UTC",
        ),
        pd.Timestamp(
            (
                end_date
                + timedelta(days=1)
            ),
            tz="UTC",
        ),
    )


def _exact_5m_grid(
    index: pd.DatetimeIndex,
) -> bool:
    if len(index) == 0:
        return True

    return bool(
        (
            index.second
            == 0
        ).all()
        and (
            index.microsecond
            == 0
        ).all()
        and (
            (
                index.minute
                % 5
            )
            == 0
        ).all()
    )


def aggregate_5m_to_15m(
    frame: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    AggregationAudit,
]:
    work = canonicalize_ohlcv(
        frame
    )

    validate_canonical(
        work
    )

    exact_grid = _exact_5m_grid(
        work.index
    )

    if not exact_grid:
        raise ValueError(
            "EODHD source contains "
            "off-grid 5m timestamps"
        )

    rows: list[dict] = []
    incomplete = 0

    for bucket_start, group in (
        work.groupby(
            work.index.floor(
                "15min"
            ),
            sort=True,
        )
    ):
        group = group.sort_index()

        expected = pd.DatetimeIndex(
            [
                bucket_start,
                (
                    bucket_start
                    + timedelta(minutes=5)
                ),
                (
                    bucket_start
                    + timedelta(minutes=10)
                ),
            ],
            name="timestamp",
        )

        if (
            len(group) != 3
            or not group.index.equals(
                expected
            )
        ):
            incomplete += 1
            continue

        rows.append(
            {
                "timestamp": (
                    bucket_start
                ),
                "open": float(
                    group[
                        "open"
                    ].iloc[0]
                ),
                "high": float(
                    group[
                        "high"
                    ].max()
                ),
                "low": float(
                    group[
                        "low"
                    ].min()
                ),
                "close": float(
                    group[
                        "close"
                    ].iloc[-1]
                ),
                "volume": float(
                    group[
                        "volume"
                    ].sum()
                ),
            }
        )

    if rows:
        result = (
            pd.DataFrame(rows)
            .set_index(
                "timestamp"
            )
        )

        result.index = (
            pd.DatetimeIndex(
                pd.to_datetime(
                    result.index,
                    utc=True,
                ),
                name="timestamp",
            )
        )

        result = canonicalize_ohlcv(
            result
        )

        validate_canonical(
            result
        )

    else:
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

    return (
        result,
        AggregationAudit(
            source_interval="5m",
            target_interval="15m",
            source_rows=int(
                len(work)
            ),
            complete_target_rows=int(
                len(result)
            ),
            incomplete_bucket_count=int(
                incomplete
            ),
            exact_5m_grid=(
                exact_grid
            ),
            forward_fill=False,
            provider_averaging=False,
        ),
    )


def _storage_frame(
    frame: pd.DataFrame,
    *,
    symbol: str,
) -> pd.DataFrame:
    work = canonicalize_ohlcv(
        frame
    )

    validate_canonical(
        work
    )

    output = (
        work.reset_index()
        .rename(
            columns={
                "timestamp": (
                    "timestamp_utc"
                )
            }
        )
    )

    output["symbol"] = (
        symbol.upper()
    )

    output["provider"] = (
        "EODHD"
    )

    output["source_provider"] = (
        "EODHD"
    )

    output["interval"] = (
        "15m"
    )

    output["target_interval"] = (
        "15m"
    )

    output["source_interval"] = (
        "5m"
    )

    output["derivation"] = (
        "AGGREGATED_5M_TO_15M"
    )

    output["bar_origin"] = (
        "DERIVED"
    )

    output["aggregation_rule"] = (
        "EXACT_3X5M_SESSION_GRID"
    )

    output["quality_status"] = (
        "VALIDATED_OHLC"
    )

    output["is_partial"] = False
    output["partial_bucket"] = False

    return output


def collect_eodhd_5m_15m(
    project_root: str | Path,
    *,
    symbols: list[str],
    start: str,
    end: str,
    as_of: str | pd.Timestamp,
    chunk_days: int = 590,
) -> dict:
    root = Path(
        project_root
    ).resolve()

    load_project_env(
        root
    )

    api_key = secret(
        "EODHD_API_KEY",
        "EOD_API_KEY",
        "EODHISTORICALDATA_API_KEY",
    )

    if not api_key:
        raise ValueError(
            "EODHD API key is not configured"
        )

    selected = sorted(
        {
            str(symbol)
            .strip()
            .upper()
            for symbol in symbols
            if str(symbol).strip()
        }
    )

    if not selected:
        raise ValueError(
            "at least one symbol is required"
        )

    (
        start_ts,
        end_exclusive,
    ) = cli_date_window(
        start,
        end,
    )

    as_of_ts = utc_timestamp(
        as_of
    )

    run_id = uuid4().hex

    output_root = (
        root
        / "artifacts"
        / "research_runtime"
        / "eodhd_5m_15m"
        / run_id
    )

    output_root.mkdir(
        parents=True,
        exist_ok=False,
    )

    bars: list[dict] = []
    audits: list[dict] = []
    provider_calls = 0

    for symbol in selected:
        fetched = fetch_intraday_5m(
            symbol,
            start=start_ts,
            end_exclusive=(
                end_exclusive
            ),
            api_key=api_key,
            chunk_days=chunk_days,
        )

        provider_calls += (
            fetched.request_count
        )

        if fetched.frame.empty:
            raise ValueError(
                f"{symbol}: EODHD "
                "returned no 5m bars"
            )

        (
            aggregated,
            aggregation_audit,
        ) = aggregate_5m_to_15m(
            fetched.frame
        )

        if aggregated.empty:
            raise ValueError(
                f"{symbol}: no complete "
                "15m buckets derived from 5m"
            )

        (
            rth,
            rth_audit,
        ) = closed_rth_15m(
            aggregated,
            as_of=as_of_ts,
        )

        path = (
            output_root
            / f"{symbol}_15m.parquet"
        )

        _storage_frame(
            rth,
            symbol=symbol,
        ).to_parquet(
            path,
            index=False,
        )

        bars.append(
            {
                "provider": "EODHD",
                "symbol": symbol,
                "interval": "15m",
                "source_interval": "5m",
                "derivation": (
                    "AGGREGATED_5M_TO_15M"
                ),
                "path": str(
                    path.resolve()
                ),
                "rows": int(
                    len(rth)
                ),
                "first_timestamp": (
                    rth.index.min()
                    .isoformat()
                ),
                "last_timestamp": (
                    rth.index.max()
                    .isoformat()
                ),
                "quality_status": (
                    "VALIDATED_OHLC"
                ),
            }
        )

        audits.append(
            {
                "symbol": symbol,
                "provider_symbol": (
                    fetched.provider_symbol
                ),
                "provider_requests": (
                    fetched.request_count
                ),
                "source_quality": (
                    fetched.source_quality
                ),
                "aggregation": (
                    aggregation_audit
                    .to_dict()
                ),
                "rth": rth_audit,
                "execution_authority": (
                    "NONE"
                ),
                "broker_calls": 0,
            }
        )

    payload = {
        "schema": (
            "eodhd_5m_to_15m_"
            "historical_source_v1"
        ),
        "run_id": run_id,
        "provider": "EODHD",
        "source_interval": "5m",
        "target_interval": "15m",
        "start": start_ts.isoformat(),
        "end_exclusive": (
            end_exclusive.isoformat()
        ),
        "as_of": (
            as_of_ts.isoformat()
        ),
        "bars": bars,
        "symbol_audits": audits,
        "provider_calls": int(
            provider_calls
        ),
        "timestamp_source": (
            "EODHD_EPOCH_UTC"
        ),
        "datetime_field_used": False,
        "forward_fill": False,
        "provider_averaging": False,
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }

    index_path = (
        output_root
        / "eodhd_5m_15m_index.json"
    )

    index_path.write_text(
        json.dumps(
            payload,
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return (
        payload
        | {
            "index_path": str(
                index_path.resolve()
            )
        }
    )
