from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PurgedWalkForwardConfig:
    minimum_train_size: int = 500
    test_size: int = 100
    step_size: int = 100
    purge_bars: int = 20
    embargo_bars: int = 0
    maximum_splits: int | None = None

    def __post_init__(self) -> None:
        if self.minimum_train_size < 10:
            raise ValueError("minimum_train_size must be >= 10")
        if self.test_size < 1 or self.step_size < 1:
            raise ValueError("test_size and step_size must be positive")
        if self.purge_bars < 0 or self.embargo_bars < 0:
            raise ValueError("purge/embargo bars cannot be negative")
        if self.maximum_splits is not None and self.maximum_splits < 1:
            raise ValueError("maximum_splits must be positive")


def purged_walkforward_splits(
    n_observations: int,
    *,
    config: PurgedWalkForwardConfig | None = None,
) -> list[tuple[np.ndarray, np.ndarray]]:
    active = config or PurgedWalkForwardConfig()
    if n_observations <= 0:
        return []
    splits: list[tuple[np.ndarray, np.ndarray]] = []
    test_start = active.minimum_train_size + active.purge_bars
    while test_start < n_observations:
        test_end = min(test_start + active.test_size, n_observations)
        train_end = max(0, test_start - active.purge_bars)
        if train_end < active.minimum_train_size:
            test_start += active.step_size
            continue
        train = np.arange(0, train_end, dtype=int)
        test = np.arange(test_start, test_end, dtype=int)
        if len(test):
            splits.append((train, test))
        if active.maximum_splits is not None and len(splits) >= active.maximum_splits:
            break
        test_start += active.step_size + active.embargo_bars
    return splits


def assert_no_label_overlap(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    *,
    label_horizon_bars: int,
) -> None:
    if label_horizon_bars < 0:
        raise ValueError("label_horizon_bars cannot be negative")
    if len(train_indices) == 0 or len(test_indices) == 0:
        raise ValueError("train/test indices cannot be empty")
    if int(train_indices.max()) + label_horizon_bars >= int(test_indices.min()):
        raise AssertionError("training label information overlaps the test interval")
