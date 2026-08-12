from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WalkForwardSplit:
    train_start: int
    train_end: int
    validation_start: int
    validation_end: int
    test_start: int
    test_end: int


def purged_walk_forward_splits(
    n_samples: int,
    *,
    train_size: int,
    validation_size: int,
    test_size: int,
    purge: int = 5,
    embargo: int = 5,
    step_size: int | None = None,
) -> list[WalkForwardSplit]:
    """Generate chronological train/validation/test slices with explicit gaps."""
    if min(n_samples, train_size, validation_size, test_size) <= 0:
        raise ValueError("sizes must be positive")
    if purge < 0 or embargo < 0:
        raise ValueError("purge and embargo must be non-negative")
    step = step_size or test_size
    splits: list[WalkForwardSplit] = []
    train_start = 0

    while True:
        train_end = train_start + train_size
        validation_start = train_end + purge
        validation_end = validation_start + validation_size
        test_start = validation_end + embargo
        test_end = test_start + test_size
        if test_end > n_samples:
            break
        splits.append(
            WalkForwardSplit(
                train_start=train_start,
                train_end=train_end,
                validation_start=validation_start,
                validation_end=validation_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        train_start += step
    return splits
