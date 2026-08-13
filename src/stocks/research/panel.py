from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from stocks.research.swing_labels import (
    forward_open_to_close_return,
)


def _canonical_frame(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = frame.copy()

    result.index = pd.to_datetime(
        result.index,
        utc=True,
        errors="coerce",
    )

    result = (
        result.loc[
            ~result.index.isna()
        ]
        .sort_index()
    )

    if result.index.has_duplicates:
        raise ValueError(
            "panel source contains "
            "duplicate timestamps"
        )

    missing = [
        column
        for column in (
            "open",
            "close",
        )
        if column not in result
    ]

    if missing:
        raise ValueError(
            f"panel source missing {missing}"
        )

    return result


def build_relative_return_panel(
    asset_frames: Mapping[
        str,
        pd.DataFrame,
    ],
    benchmark_frame: pd.DataFrame,
    *,
    hold_bars: int,
) -> pd.DataFrame:
    if hold_bars < 1:
        raise ValueError(
            "hold_bars must be >= 1"
        )

    benchmark = _canonical_frame(
        benchmark_frame
    )

    benchmark_return = (
        forward_open_to_close_return(
            benchmark["open"],
            benchmark["close"],
            hold_bars=hold_bars,
        )
        .rename(
            "benchmark_return"
        )
    )

    rows = []

    for raw_symbol, raw_frame in (
        asset_frames.items()
    ):
        symbol = str(
            raw_symbol
        ).upper()

        asset = _canonical_frame(
            raw_frame
        )

        raw_return = (
            forward_open_to_close_return(
                asset["open"],
                asset["close"],
                hold_bars=hold_bars,
            )
            .rename(
                "raw_return"
            )
        )

        joined = (
            pd.concat(
                [
                    raw_return,
                    benchmark_return,
                ],
                axis=1,
                join="inner",
            )
            .dropna(
                subset=[
                    "raw_return",
                    "benchmark_return",
                ]
            )
        )

        joined[
            "excess_return"
        ] = (
            joined[
                "raw_return"
            ]
            - joined[
                "benchmark_return"
            ]
        )

        joined[
            "symbol"
        ] = symbol

        joined.index.name = (
            "decision_bar_time"
        )

        rows.append(
            joined.reset_index()
        )

    if not rows:
        raise ValueError(
            "asset_frames is empty"
        )

    panel = pd.concat(
        rows,
        ignore_index=True,
    )

    panel[
        "decision_bar_time"
    ] = pd.to_datetime(
        panel[
            "decision_bar_time"
        ],
        utc=True,
    )

    if panel.duplicated(
        subset=[
            "decision_bar_time",
            "symbol",
        ]
    ).any():
        raise ValueError(
            "duplicate panel asset/time row"
        )

    return (
        panel.sort_values(
            [
                "decision_bar_time",
                "symbol",
            ]
        )
        .reset_index(
            drop=True
        )
    )


def center_cross_sectional_label(
    frame: pd.DataFrame,
    *,
    time_column: str,
    min_assets: int,
) -> pd.DataFrame:
    if min_assets < 2:
        raise ValueError(
            "min_assets must be >= 2"
        )

    required = {
        time_column,
        "symbol",
        "excess_return",
    }

    missing = (
        required
        - set(
            frame.columns
        )
    )

    if missing:
        raise ValueError(
            "panel label input missing "
            f"{sorted(missing)}"
        )

    result = frame.copy()

    result[
        time_column
    ] = pd.to_datetime(
        result[
            time_column
        ],
        utc=True,
        errors="coerce",
    )

    result[
        "symbol"
    ] = (
        result[
            "symbol"
        ]
        .astype(str)
        .str.upper()
    )

    result[
        "excess_return"
    ] = pd.to_numeric(
        result[
            "excess_return"
        ],
        errors="coerce",
    )

    result = result.dropna(
        subset=[
            time_column,
            "symbol",
            "excess_return",
        ]
    )

    if result.duplicated(
        subset=[
            time_column,
            "symbol",
        ]
    ).any():
        raise ValueError(
            "duplicate panel decision row"
        )

    counts = (
        result.groupby(
            time_column,
            sort=False,
        )[
            "symbol"
        ]
        .nunique()
    )

    valid_times = counts.loc[
        counts
        >= min_assets
    ].index

    result = result.loc[
        result[
            time_column
        ].isin(
            valid_times
        )
    ].copy()

    group_mean = (
        result.groupby(
            time_column,
            sort=False,
        )[
            "excess_return"
        ]
        .transform(
            "mean"
        )
    )

    result[
        "label"
    ] = (
        result[
            "excess_return"
        ]
        - group_mean
    )

    result[
        "cross_section_size"
    ] = (
        result.groupby(
            time_column,
            sort=False,
        )[
            "symbol"
        ]
        .transform(
            "nunique"
        )
        .astype(int)
    )

    residual_mean = (
        result.groupby(
            time_column
        )[
            "label"
        ]
        .mean()
        .abs()
        .max()
    )

    if (
        pd.notna(
            residual_mean
        )
        and float(
            residual_mean
        )
        > 1e-12
    ):
        raise ValueError(
            "cross-sectional label "
            "is not zero centered"
        )

    return (
        result.sort_values(
            [
                time_column,
                "symbol",
            ]
        )
        .reset_index(
            drop=True
        )
    )


def cross_sectional_rank_features(
    frame: pd.DataFrame,
    *,
    time_column: str,
    feature_columns: Sequence[str],
    passthrough_columns: Sequence[
        str
    ] = (),
) -> pd.DataFrame:
    result = frame.copy()

    passthrough = set(
        passthrough_columns
    )

    rank_columns = [
        column
        for column in feature_columns
        if column not in passthrough
    ]

    for column in feature_columns:
        result[
            column
        ] = pd.to_numeric(
            result[
                column
            ],
            errors="coerce",
        )

    if rank_columns:
        ranked = (
            result.groupby(
                time_column,
                sort=False,
            )[
                rank_columns
            ]
            .rank(
                method="average",
                pct=True,
            )
            - 0.5
        )

        result.loc[
            :,
            rank_columns,
        ] = ranked

    return result


def validate_panel_dataset(
    frame: pd.DataFrame,
    *,
    time_column: str = "datetime",
    min_assets: int = 2,
) -> dict:
    required = {
        time_column,
        "symbol",
        "label",
    }

    missing = (
        required
        - set(
            frame.columns
        )
    )

    if missing:
        raise ValueError(
            "panel dataset missing "
            f"{sorted(missing)}"
        )

    work = frame.copy()

    work[
        time_column
    ] = pd.to_datetime(
        work[
            time_column
        ],
        utc=True,
        errors="coerce",
    )

    if work[
        time_column
    ].isna().any():
        raise ValueError(
            "invalid panel timestamps"
        )

    if work.duplicated(
        subset=[
            time_column,
            "symbol",
        ]
    ).any():
        raise ValueError(
            "duplicate datetime/symbol"
        )

    sizes = (
        work.groupby(
            time_column
        )[
            "symbol"
        ]
        .nunique()
    )

    if (
        sizes.min()
        < min_assets
    ):
        raise ValueError(
            "panel contains undersized "
            "cross-section"
        )

    labels = pd.to_numeric(
        work[
            "label"
        ],
        errors="coerce",
    )

    if labels.isna().any():
        raise ValueError(
            "panel label contains NaN"
        )

    centered = (
        work.assign(
            _label=labels
        )
        .groupby(
            time_column
        )[
            "_label"
        ]
        .mean()
        .abs()
        .max()
    )

    return {
        "rows": int(
            len(work)
        ),
        "time_groups": int(
            sizes.size
        ),
        "min_cross_section": int(
            sizes.min()
        ),
        "max_cross_section": int(
            sizes.max()
        ),
        "label_center_max_abs": float(
            centered
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }
