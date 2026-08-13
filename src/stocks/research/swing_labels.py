from __future__ import annotations

import pandas as pd


def forward_hold_return(
    close: pd.Series,
    *,
    hold_bars: int,
) -> pd.Series:
    if hold_bars < 1:
        raise ValueError(
            "hold_bars must be >= 1"
        )

    close = pd.to_numeric(
        close,
        errors="coerce",
    ).astype(float)

    entry = close.shift(-1)

    exit_price = close.shift(
        -(hold_bars + 1)
    )

    return (
        exit_price
        / entry
        - 1.0
    )


def purged_periods(
    index: pd.DatetimeIndex,
    *,
    lookahead_bars: int,
) -> dict[str, list[str]]:
    index = (
        pd.DatetimeIndex(index)
        .dropna()
        .sort_values()
        .unique()
    )

    if len(index) < 500:
        raise ValueError(
            "at least 500 timestamps required"
        )

    if lookahead_bars < 1:
        raise ValueError(
            "lookahead_bars must be >= 1"
        )

    train_boundary = int(
        len(index) * 0.60
    )

    valid_boundary = int(
        len(index) * 0.80
    )

    train_end = (
        train_boundary
        - lookahead_bars
        - 1
    )

    valid_end = (
        valid_boundary
        - lookahead_bars
        - 1
    )

    if train_end <= 0:
        raise ValueError(
            "training segment too short"
        )

    if valid_end <= train_boundary:
        raise ValueError(
            "validation segment too short"
        )

    return {
        "train": [
            str(index[0]),
            str(index[train_end]),
        ],
        "valid": [
            str(index[train_boundary]),
            str(index[valid_end]),
        ],
        "test": [
            str(index[valid_boundary]),
            str(index[-1]),
        ],
    }
