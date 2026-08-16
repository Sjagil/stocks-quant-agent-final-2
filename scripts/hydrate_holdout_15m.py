
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from stocks.data.canonical import (
    CanonicalMetadata,
    canonicalize_ohlcv,
    write_canonical_parquet,
)
from stocks.data.eodhd_5m_source import (
    collect_eodhd_5m_15m,
)
from stocks.providers.env import (
    load_project_env,
    secret,
)
from stocks.providers.http import (
    ProviderHTTPClient,
)
from stocks.research.eodhd_holdout_hydration import (
    apply_split_adjustments,
    fetch_split_history,
)


ROOT = Path(__file__).resolve().parents[1]


def _canonical_from_storage(
    path: Path,
) -> pd.DataFrame:
    raw = pd.read_parquet(path)

    time_col = (
        "timestamp_utc"
        if "timestamp_utc" in raw.columns
        else (
            "timestamp"
            if "timestamp" in raw.columns
            else None
        )
    )

    if time_col is None:
        raise ValueError(
            f"{path}: timestamp column missing"
        )

    frame = raw[
        [
            time_col,
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ].copy()

    frame[time_col] = (
        pd.to_datetime(
            frame[time_col],
            utc=True,
        )
    )

    frame = frame.set_index(
        time_col
    )
    frame.index.name = "timestamp"

    return canonicalize_ohlcv(
        frame
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--as-of",
        required=True,
    )
    parser.add_argument(
        "--start",
        default="2020-10-01",
    )
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=24,
    )
    parser.add_argument(
        "--chunk-days",
        type=int,
        default=590,
    )
    args = parser.parse_args()

    holdout = json.loads(
        (
            ROOT
            / "config/generalization_holdout_v1.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    selected: list[str] = []

    for symbol_raw in holdout["symbols"]:
        symbol = str(
            symbol_raw
        ).upper()

        existing = (
            ROOT
            / "data/canonical/provider_fabric"
            / f"{symbol}_15m.parquet"
        )

        if existing.is_file():
            continue

        selected.append(symbol)

        if (
            len(selected)
            >= int(
                args.max_symbols
            )
        ):
            break

    if not selected:
        print(
            "HOLDOUT_15M_HYDRATION "
            "NOTHING_TO_DO"
        )
        return 0

    load_project_env(ROOT)

    api_key = secret(
        "EODHD_API_KEY",
        "EOD_API_KEY",
        "EODHISTORICALDATA_API_KEY",
    )

    if not api_key:
        raise ValueError(
            "EODHD API key missing"
        )

    rows: list[dict] = []

    with ProviderHTTPClient(
        user_agent=(
            "stocks-quant-agent/"
            "holdout-15m-hydration-v2.7"
        )
    ) as client:
        for symbol in selected:
            try:
                # Isolate each symbol so one data failure does not abort the
                # complete holdout hydration round.
                result = collect_eodhd_5m_15m(
                    ROOT,
                    symbols=[symbol],
                    start=args.start,
                    end=args.as_of,
                    as_of=(
                        f"{args.as_of}"
                        "T23:59:59Z"
                    ),
                    chunk_days=int(
                        args.chunk_days
                    ),
                )

                item = result["bars"][0]
                source = Path(
                    item["path"]
                )

                frame = (
                    _canonical_from_storage(
                        source
                    )
                )

                splits = fetch_split_history(
                    symbol,
                    start=args.start,
                    end=args.as_of,
                    api_key=api_key,
                    client=client,
                )

                adjusted = (
                    apply_split_adjustments(
                        frame,
                        splits,
                    )
                )

                target = (
                    ROOT
                    / "data/canonical/provider_fabric"
                    / f"{symbol}_15m.parquet"
                )

                write_canonical_parquet(
                    adjusted,
                    target,
                    CanonicalMetadata(
                        symbol=symbol,
                        exchange="US",
                        timeframe="15m",
                        source=(
                            "EODHD_NATIVE_5M_"
                            "DERIVED_15M_HOLDOUT"
                        ),
                        adjustment=(
                            "SPLIT_ADJUSTED_ONLY"
                        ),
                        provenance={
                            "provider": "EODHD",
                            "source_interval": "5m",
                            "target_interval": "15m",
                            "derivation": (
                                "EXACT_3X5M_"
                                "SESSION_GRID"
                            ),
                            "split_source": (
                                "EODHD_"
                                "HISTORICAL_SPLITS"
                            ),
                            "split_count": (
                                len(splits)
                            ),
                            "current_selection_used": (
                                False
                            ),
                            "execution_authority": (
                                "NONE"
                            ),
                        },
                    ),
                )

                row = {
                    "symbol": symbol,
                    "status": "HYDRATED",
                    "rows": int(
                        len(adjusted)
                    ),
                    "split_count": int(
                        len(splits)
                    ),
                    "provider_calls_5m": int(
                        result[
                            "provider_calls"
                        ]
                    ),
                    "output": str(target),
                    "reason": None,
                }

                print(
                    "HYDRATE_15M",
                    symbol,
                    "ROWS",
                    len(adjusted),
                    "SPLITS",
                    len(splits),
                )

            except Exception as exc:
                row = {
                    "symbol": symbol,
                    "status": "FAILED",
                    "rows": 0,
                    "split_count": 0,
                    "provider_calls_5m": 0,
                    "output": None,
                    "reason": (
                        f"{type(exc).__name__}:"
                        f"{exc}"
                    ),
                }

                print(
                    "HYDRATE_15M",
                    symbol,
                    "FAILED",
                    row["reason"],
                )

            rows.append(row)

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "holdout_15m_hydration"
    )
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame = pd.DataFrame(rows)
    frame.to_csv(
        output / "results.csv",
        index=False,
    )

    hydrated = int(
        (
            frame["status"]
            == "HYDRATED"
        ).sum()
    )

    audit = {
        "schema": (
            "holdout_15m_hydration_v2_7"
        ),
        "requested": int(
            len(selected)
        ),
        "hydrated": hydrated,
        "failed": int(
            len(frame)
            - hydrated
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
        "order_calls": 0,
    }

    (
        output / "audit.json"
    ).write_text(
        json.dumps(
            audit,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "HOLDOUT_15M_HYDRATION_V2_7",
        "REQUESTED",
        audit["requested"],
        "HYDRATED",
        audit["hydrated"],
        "FAILED",
        audit["failed"],
    )
    print(
        "ARTIFACT_ROOT",
        output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
