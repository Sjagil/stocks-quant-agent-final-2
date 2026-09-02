from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from stocks.data.canonical import canonicalize_ohlcv
from stocks.rl.config import EnvironmentConfig, RewardConfig
from stocks.rl.environment import LongOnlySwingEnv
from stocks.rl.features import build_rl_features


@dataclass(frozen=True)
class DatasetWindowsV240:
    features: pd.DataFrame
    close: pd.Series
    train_slice: tuple[int, int]
    validation_slice: tuple[int, int]
    test_slice: tuple[int, int]
    latest_data_time: str | None

    @property
    def rows(self) -> int:
        return len(self.features)


def load_dataset_v240(path: str | Path) -> tuple[pd.DataFrame, pd.Series]:
    frame = pd.read_parquet(path).sort_index()
    market = canonicalize_ohlcv(frame)
    features = build_rl_features(market)
    joined = features.join(market["close"].astype(float).rename("__close__"))
    joined = joined.replace([float("inf"), float("-inf")], float("nan")).dropna()
    if joined.empty:
        raise ValueError("no fully observed RL rows")
    return joined.drop(columns=["__close__"]), joined["__close__"].astype(float)


def build_windows_v240(
    features: pd.DataFrame,
    close: pd.Series,
    *,
    validation_fraction: float = 0.15,
    test_fraction: float = 0.15,
    purge_bars: int = 64,
    minimum_rows: int = 800,
) -> DatasetWindowsV240:
    if not features.index.equals(close.index):
        raise ValueError("features and close must align")
    n = len(features)
    if n < int(minimum_rows):
        raise ValueError(f"at least {minimum_rows} rows required")
    if validation_fraction <= 0 or test_fraction <= 0 or validation_fraction + test_fraction >= 0.5:
        raise ValueError("invalid validation/test fractions")
    p = max(1, int(purge_bars))
    test_n = max(2 * p, int(n * test_fraction))
    val_n = max(2 * p, int(n * validation_fraction))
    test_start = n - test_n
    val_end = test_start - p
    val_start = val_end - val_n
    train_end = val_start - p
    if train_end <= 2 * p or val_start < 0:
        raise ValueError("purge leaves insufficient train/validation/test windows")
    latest = features.index[-1]
    latest_text = latest.isoformat() if hasattr(latest, "isoformat") else str(latest)
    return DatasetWindowsV240(
        features=features,
        close=close,
        train_slice=(0, train_end),
        validation_slice=(val_start, val_end),
        test_slice=(test_start, n),
        latest_data_time=latest_text,
    )


def make_env_v240(windows: DatasetWindowsV240, which: str, *, env_cfg: EnvironmentConfig, reward_cfg: RewardConfig):
    mapping = {
        "train": windows.train_slice,
        "validation": windows.validation_slice,
        "test": windows.test_slice,
    }
    if which not in mapping:
        raise ValueError(which)
    start, end = mapping[which]
    return LongOnlySwingEnv(
        windows.features.iloc[start:end].copy(),
        windows.close.iloc[start:end].copy(),
        env_cfg=env_cfg,
        reward_cfg=reward_cfg,
    )


__all__ = ["DatasetWindowsV240", "load_dataset_v240", "build_windows_v240", "make_env_v240"]
