from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from stocks.data.canonical import (
    OHLCV_COLUMNS,
    canonicalize_ohlcv,
    validate_canonical,
)


@dataclass(frozen=True)
class ProviderFrame:
    source: str
    priority: int
    frame: pd.DataFrame


@dataclass(frozen=True)
class ProviderMuxResult:
    frame: pd.DataFrame
    provenance: pd.DataFrame
    disagreement: pd.DataFrame


def _valid_rows(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    work = canonicalize_ohlcv(
        frame,
        drop_duplicate_timestamps=True,
        drop_missing_required=False,
    )

    required = list(
        OHLCV_COLUMNS
    )

    finite = np.isfinite(
        work[
            required
        ].to_numpy(
            dtype=float,
        )
    ).all(
        axis=1
    )

    complete = (
        work[
            required
        ]
        .notna()
        .all(
            axis=1
        )
    )

    positive_prices = (
        work[
            [
                "open",
                "high",
                "low",
                "close",
            ]
        ]
        .gt(0)
        .all(
            axis=1
        )
    )

    valid_volume = (
        work[
            "volume"
        ]
        >= 0
    )

    return work.loc[
        finite
        & complete
        & positive_prices
        & valid_volume
    ].copy()


def merge_provider_frames(
    providers: list[ProviderFrame],
) -> ProviderMuxResult:
    if not providers:
        raise ValueError(
            "at least one provider frame is required"
        )

    candidates = []

    for provider in providers:
        frame = _valid_rows(
            provider.frame
        )

        if frame.empty:
            continue

        frame = frame.copy()

        frame[
            "__source"
        ] = provider.source

        frame[
            "__priority"
        ] = int(
            provider.priority
        )

        candidates.append(
            frame
        )

    if not candidates:
        raise ValueError(
            "all provider frames are empty or invalid"
        )

    combined = pd.concat(
        candidates,
        axis=0,
    )

    combined[
        "__timestamp"
    ] = combined.index

    combined = (
        combined
        .sort_values(
            [
                "__timestamp",
                "__priority",
                "__source",
            ],
            kind="stable",
        )
    )

    selected = (
        combined
        .drop_duplicates(
            subset=[
                "__timestamp"
            ],
            keep="first",
        )
        .set_index(
            "__timestamp"
        )
        .sort_index()
    )

    selected.index.name = (
        "timestamp"
    )

    provenance = selected[
        [
            "__source",
            "__priority",
        ]
    ].rename(
        columns={
            "__source": (
                "source"
            ),
            "__priority": (
                "priority"
            ),
        }
    )

    frame = selected[
        list(
            OHLCV_COLUMNS
        )
    ].copy()

    frame = canonicalize_ohlcv(
        frame
    )

    validate_canonical(
        frame
    )

    close_matrix = (
        combined
        .pivot_table(
            index="__timestamp",
            columns="__source",
            values="close",
            aggfunc="last",
        )
        .sort_index()
    )

    if (
        close_matrix.shape[1]
        >= 2
    ):
        row_max = (
            close_matrix.max(
                axis=1
            )
        )

        row_min = (
            close_matrix.min(
                axis=1
            )
        )

        midpoint = (
            (
                row_max
                +
                row_min
            )
            / 2.0
        )

        disagreement_bps = (
            (row_max - row_min)
            / midpoint.replace(
                0,
                np.nan,
            )
            * 10_000
        )

        disagreement = (
            pd.DataFrame(
                {
                    "providers": (
                        close_matrix
                        .notna()
                        .sum(
                            axis=1
                        )
                    ),
                    "close_disagreement_bps": (
                        disagreement_bps
                    ),
                }
            )
        )

    else:
        disagreement = (
            pd.DataFrame(
                {
                    "providers": (
                        close_matrix
                        .notna()
                        .sum(
                            axis=1
                        )
                    ),
                    "close_disagreement_bps": (
                        0.0
                    ),
                }
            )
        )

    return ProviderMuxResult(
        frame=frame,
        provenance=provenance,
        disagreement=disagreement,
    )
