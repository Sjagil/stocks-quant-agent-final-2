from __future__ import annotations

import math

import numpy as np
import pandas as pd

from stocks.research.strategy_factory_1h import (
    trade_metrics,
)


def normalize_predictions(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "datetime",
        "symbol",
        "prediction",
        "fold",
        "variant",
        "hold_bars",
    }

    missing = (
        required
        - set(
            frame.columns
        )
    )

    if missing:
        raise ValueError(
            "prediction frame missing "
            f"{sorted(missing)}"
        )

    result = frame.copy()

    result[
        "datetime"
    ] = pd.to_datetime(
        result[
            "datetime"
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
        "prediction"
    ] = pd.to_numeric(
        result[
            "prediction"
        ],
        errors="coerce",
    )

    result = result.dropna(
        subset=[
            "datetime",
            "symbol",
            "prediction",
        ]
    )

    if result.duplicated(
        subset=[
            "datetime",
            "symbol",
            "variant",
            "hold_bars",
        ]
    ).any():
        raise ValueError(
            "duplicate tactical "
            "prediction"
        )

    result[
        "prediction_rank"
    ] = (
        result.groupby(
            [
                "datetime",
                "variant",
                "hold_bars",
            ],
            sort=False,
        )[
            "prediction"
        ]
        .rank(
            method="average",
            pct=True,
        )
    )

    result[
        "prediction_ordinal"
    ] = (
        result.groupby(
            [
                "datetime",
                "variant",
                "hold_bars",
            ],
            sort=False,
        )[
            "prediction"
        ]
        .rank(
            method="first",
            ascending=False,
        )
        .astype(int)
    )

    result[
        "cross_section_size"
    ] = (
        result.groupby(
            [
                "datetime",
                "variant",
                "hold_bars",
            ],
            sort=False,
        )[
            "symbol"
        ]
        .transform(
            "nunique"
        )
        .astype(int)
    )

    return result


def attach_predictions_to_trades(
    trades: pd.DataFrame,
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "symbol",
        "entry_time",
        "gross_return",
    }

    missing = (
        required
        - set(
            trades.columns
        )
    )

    if missing:
        raise ValueError(
            "trade frame missing "
            f"{sorted(missing)}"
        )

    left = trades.copy()

    left[
        "symbol"
    ] = (
        left[
            "symbol"
        ]
        .astype(str)
        .str.upper()
    )

    left[
        "entry_time"
    ] = pd.to_datetime(
        left[
            "entry_time"
        ],
        utc=True,
        errors="coerce",
    )

    left = left.dropna(
        subset=[
            "entry_time",
            "symbol",
        ]
    )

    right = normalize_predictions(
        predictions
    )

    if right.duplicated(
        subset=[
            "datetime",
            "symbol",
        ]
    ).any():
        duplicates = (
            right.loc[
                right.duplicated(
                    subset=[
                        "datetime",
                        "symbol",
                    ],
                    keep=False,
                ),
                [
                    "datetime",
                    "symbol",
                    "fold",
                    "variant",
                    "hold_bars",
                ],
            ]
            .sort_values(
                [
                    "datetime",
                    "symbol",
                    "fold",
                ]
            )
        )

        raise ValueError(
            "OOS tactical predictions "
            "are not unique by "
            "datetime/symbol:\n"
            + duplicates.head(
                20
            ).to_string(
                index=False
            )
        )

    right = right.rename(
        columns={
            "datetime": (
                "tactical_decision_time"
            )
        }
    )

    result = left.merge(
        right,
        left_on=[
            "entry_time",
            "symbol",
        ],
        right_on=[
            "tactical_decision_time",
            "symbol",
        ],
        how="inner",
        validate="many_to_one",
    )

    if result.empty:
        return result

    result[
        "decision_lag_minutes"
    ] = (
        (
            result[
                "entry_time"
            ]
            - result[
                "tactical_decision_time"
            ]
        )
        .dt.total_seconds()
        / 60.0
    )

    if not (
        result[
            "decision_lag_minutes"
        ]
        == 0.0
    ).all():
        raise ValueError(
            "tactical overlay requires "
            "exact causal decision-time "
            "parity with 1h entry"
        )

    return (
        result.sort_values(
            [
                "entry_time",
                "symbol",
                "hypothesis_id",
            ]
        )
        .reset_index(
            drop=True
        )
    )

def overlay_mask(
    frame: pd.DataFrame,
    name: str,
) -> pd.Series:
    if name == "ALL":
        return pd.Series(
            True,
            index=frame.index,
        )

    if name == "PRED_POSITIVE":
        return (
            frame[
                "prediction"
            ]
            > 0.0
        )

    if name == "TOP_HALF":
        return (
            frame[
                "prediction_rank"
            ]
            >= 0.60
        )

    if name == "TOP2":
        return (
            frame[
                "prediction_ordinal"
            ]
            <= 2
        )

    if name == "TOP1":
        return (
            frame[
                "prediction_ordinal"
            ]
            == 1
        )

    if name == "POSITIVE_TOP2":
        return (
            (
                frame[
                    "prediction"
                ]
                > 0.0
            )
            & (
                frame[
                    "prediction_ordinal"
                ]
                <= 2
            )
        )

    raise ValueError(
        f"unknown overlay {name}"
    )


def fold_overlay_metrics(
    frame: pd.DataFrame,
    *,
    overlay: str,
    cost_bps_per_side: float,
) -> dict:
    selected = frame.loc[
        overlay_mask(
            frame,
            overlay,
        )
    ]

    metrics = trade_metrics(
        selected,
        cost_bps_per_side=(
            cost_bps_per_side
        ),
    )

    return {
        "overlay": overlay,
        "retained_trades": int(
            len(
                selected
            )
        ),
        "retention_ratio": (
            float(
                len(
                    selected
                )
                / len(
                    frame
                )
            )
            if len(
                frame
            )
            else 0.0
        ),
        **metrics,
    }


def summarize_overlay_folds(
    rows: list[dict],
) -> dict:
    usable = [
        row
        for row in rows
        if int(
            row[
                "retained_trades"
            ]
        ) >= 8
    ]

    if not usable:
        return {
            "usable_folds": 0,
            "positive_fold_ratio": 0.0,
            "median_expectancy_bps": (
                math.nan
            ),
            "worst_expectancy_bps": (
                math.nan
            ),
            "median_profit_factor": (
                math.nan
            ),
            "median_retention_ratio": (
                math.nan
            ),
        }

    expectancy = np.asarray(
        [
            float(
                row[
                    "net_expectancy_bps"
                ]
            )
            for row in usable
        ],
        dtype=float,
    )

    profit_factor = np.asarray(
        [
            float(
                row[
                    "profit_factor"
                ]
            )
            for row in usable
        ],
        dtype=float,
    )

    retention = np.asarray(
        [
            float(
                row[
                    "retention_ratio"
                ]
            )
            for row in usable
        ],
        dtype=float,
    )

    return {
        "usable_folds": int(
            len(
                usable
            )
        ),
        "positive_fold_ratio": float(
            np.mean(
                expectancy
                > 0.0
            )
        ),
        "median_expectancy_bps": float(
            np.median(
                expectancy
            )
        ),
        "worst_expectancy_bps": float(
            np.min(
                expectancy
            )
        ),
        "median_profit_factor": float(
            np.median(
                profit_factor
            )
        ),
        "median_retention_ratio": float(
            np.median(
                retention
            )
        ),
    }
