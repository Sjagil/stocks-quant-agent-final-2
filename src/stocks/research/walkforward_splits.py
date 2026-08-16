from __future__ import annotations

import pandas as pd


def rolling_periods(
    index: pd.DatetimeIndex,
    *,
    hold_bars: int,
    requested_folds: int,
) -> list[
    dict[str, list[str]]
]:
    index = pd.DatetimeIndex(
        index
    ).sort_values()

    if index.has_duplicates:
        raise ValueError(
            "walk-forward index contains "
            "duplicate timestamps"
        )

    n = len(index)

    if n < 4000:
        raise ValueError(
            "at least 4000 rows required"
        )

    gap = (
        hold_bars
        + 1
    )

    valid_len = max(
        500,
        int(
            n
            * 0.10
        ),
    )

    test_len = max(
        500,
        int(
            n
            * 0.10
        ),
    )

    initial_train_end = (
        int(
            n
            * 0.45
        )
        - 1
    )

    folds = []

    for fold_number in range(
        requested_folds
    ):
        train_end = (
            initial_train_end
            + fold_number
            * test_len
        )

        valid_start = (
            train_end
            + gap
            + 1
        )

        valid_end = (
            valid_start
            + valid_len
            - 1
        )

        test_start = (
            valid_end
            + gap
            + 1
        )

        test_end = (
            test_start
            + test_len
            - 1
        )

        if test_end >= n:
            break

        folds.append(
            {
                "train": [
                    str(
                        index[0]
                    ),
                    str(
                        index[
                            train_end
                        ]
                    ),
                ],
                "valid": [
                    str(
                        index[
                            valid_start
                        ]
                    ),
                    str(
                        index[
                            valid_end
                        ]
                    ),
                ],
                "test": [
                    str(
                        index[
                            test_start
                        ]
                    ),
                    str(
                        index[
                            test_end
                        ]
                    ),
                ],
            }
        )

    if len(folds) < 2:
        raise ValueError(
            "fewer than three "
            "walk-forward folds"
        )

    return folds
