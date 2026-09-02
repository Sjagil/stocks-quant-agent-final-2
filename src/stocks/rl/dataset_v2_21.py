from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stocks.data.canonical import (
    canonicalize_ohlcv,
    read_canonical_parquet,
    sha256_file,
    validate_canonical,
)

from .contracts_v2_21 import PortfolioEpisodeV221

LOCAL_FEATURE_NAMES_V221 = (
    "return_1",
    "return_5",
    "volatility_20",
    "volume_zscore_20",
    "range_to_close",
    "trend_20",
)
GLOBAL_FEATURE_NAMES_V221 = (
    "cross_sectional_return_mean",
    "cross_sectional_return_std",
    "cross_sectional_volatility_mean",
    "cross_sectional_trend_mean",
)


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class FeatureScalerV221:
    local_mean: tuple[float, ...]
    local_scale: tuple[float, ...]
    global_mean: tuple[float, ...]
    global_scale: tuple[float, ...]
    fitted_observations: int

    def __post_init__(self) -> None:
        if not self.local_mean or not self.global_mean:
            raise ValueError("feature scaler dimensions must be non-empty")
        if len(self.local_mean) != len(self.local_scale):
            raise ValueError("local scaler dimensions do not match")
        if len(self.global_mean) != len(self.global_scale):
            raise ValueError("global scaler dimensions do not match")
        if min(*self.local_scale, *self.global_scale) <= 0:
            raise ValueError("feature scales must be positive")
        if self.fitted_observations < 2:
            raise ValueError("feature scaler requires at least two observations")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PortfolioDatasetBundleV221:
    episode: PortfolioEpisodeV221
    symbols: tuple[str, ...]
    timeframe: str
    dataset_hash: str
    source_files: tuple[str, ...]
    source_hashes: tuple[str, ...]
    local_feature_names: tuple[str, ...] = LOCAL_FEATURE_NAMES_V221
    global_feature_names: tuple[str, ...] = GLOBAL_FEATURE_NAMES_V221

    def manifest(self) -> dict[str, Any]:
        timestamps = np.asarray(self.episode.timestamps)
        return {
            "version": "v2.21",
            "symbols": list(self.symbols),
            "timeframe": self.timeframe,
            "observations": int(self.episode.steps + 1),
            "return_steps": self.episode.steps,
            "local_features": list(self.local_feature_names),
            "global_features": list(self.global_feature_names),
            "start": str(timestamps[0]),
            "end": str(timestamps[-1]),
            "dataset_hash": self.dataset_hash,
            "source_files": list(self.source_files),
            "source_hashes": list(self.source_hashes),
            "point_in_time": True,
            "feature_cutoff_at_or_before_decision": True,
            "forward_filled_bars": False,
            "execution_authority": "NONE",
            "broker_calls": 0,
            "order_calls": 0,
        }


def _rolling_zscore(values: pd.Series, window: int) -> pd.Series:
    mean = values.rolling(window, min_periods=5).mean()
    std = values.rolling(window, min_periods=5).std(ddof=0).replace(0.0, np.nan)
    return (values - mean) / std


def _local_features(frame: pd.DataFrame) -> pd.DataFrame:
    close = frame["close"].astype(float)
    return_1 = close.pct_change(fill_method=None)
    return pd.DataFrame(
        {
            "return_1": return_1,
            "return_5": close.pct_change(5, fill_method=None),
            "volatility_20": return_1.rolling(20, min_periods=5).std(ddof=0),
            "volume_zscore_20": _rolling_zscore(
                np.log1p(frame["volume"].astype(float)),
                20,
            ),
            "range_to_close": (
                frame["high"].astype(float) - frame["low"].astype(float)
            )
            / close,
            "trend_20": close / close.rolling(20, min_periods=5).mean() - 1.0,
        },
        index=frame.index,
    ).replace([np.inf, -np.inf], np.nan)


def build_portfolio_episode_from_frames_v221(
    frames: Mapping[str, pd.DataFrame],
    *,
    timeframe: str,
    benchmark_symbol: str | None = None,
    source_files: Sequence[str] = (),
    source_hashes: Sequence[str] = (),
) -> PortfolioDatasetBundleV221:
    """Build a strictly aligned point-in-time episode from canonical OHLCV.

    Only timestamps present for every configured symbol are retained. Bars are
    never forward-filled. Features at row ``t`` use rows up to and including
    ``t``; returns are realized from ``t`` to ``t + 1``.
    """

    if not frames:
        raise ValueError("at least one market frame is required")
    symbols = tuple(str(symbol).strip().upper() for symbol in frames)
    if any(not symbol for symbol in symbols) or len(set(symbols)) != len(symbols):
        raise ValueError("symbols must be non-empty and unique")
    if not str(timeframe).strip():
        raise ValueError("timeframe is required")
    if benchmark_symbol and benchmark_symbol.upper() not in symbols:
        raise ValueError("benchmark_symbol must be part of the configured symbols")
    if source_files and len(source_files) != len(symbols):
        raise ValueError("source_files must match the symbol count")
    if source_hashes and len(source_hashes) != len(symbols):
        raise ValueError("source_hashes must match the symbol count")

    canonical: dict[str, pd.DataFrame] = {}
    common_index: pd.DatetimeIndex | None = None
    for symbol, raw in zip(symbols, frames.values(), strict=True):
        frame = canonicalize_ohlcv(raw)
        validate_canonical(frame)
        canonical[symbol] = frame
        common_index = (
            frame.index
            if common_index is None
            else common_index.intersection(frame.index, sort=False)
        )
    assert common_index is not None
    common_index = common_index.sort_values()
    if len(common_index) < 8:
        raise ValueError("aligned market data needs at least eight observations")

    features = {
        symbol: _local_features(canonical[symbol].loc[common_index])
        for symbol in symbols
    }
    feature_cube = np.stack(
        [features[symbol].to_numpy(dtype=np.float64) for symbol in symbols],
        axis=1,
    )
    close_matrix = np.column_stack(
        [canonical[symbol].loc[common_index, "close"].to_numpy(float) for symbol in symbols]
    )
    finite_rows = np.isfinite(feature_cube).all(axis=(1, 2))
    first_valid = int(np.flatnonzero(finite_rows)[0]) if finite_rows.any() else len(common_index)
    feature_cube = feature_cube[first_valid:]
    close_matrix = close_matrix[first_valid:]
    episode_index = common_index[first_valid:]
    finite_rows = np.isfinite(feature_cube).all(axis=(1, 2))
    if not finite_rows.all():
        raise ValueError("feature panel contains non-finite values after warmup")
    if len(episode_index) < 3:
        raise ValueError("feature warmup leaves fewer than three observations")

    asset_returns = close_matrix[1:] / close_matrix[:-1] - 1.0
    global_observations = np.column_stack(
        [
            feature_cube[:, :, 0].mean(axis=1),
            feature_cube[:, :, 0].std(axis=1),
            feature_cube[:, :, 2].mean(axis=1),
            feature_cube[:, :, 5].mean(axis=1),
        ]
    )
    benchmark = (
        asset_returns[:, symbols.index(benchmark_symbol.upper())]
        if benchmark_symbol and benchmark_symbol.upper() in symbols
        else asset_returns.mean(axis=1)
    )
    timestamps = episode_index.to_numpy(dtype="datetime64[ns]")
    episode = PortfolioEpisodeV221(
        local_observations=feature_cube.astype(np.float32),
        global_observations=global_observations.astype(np.float32),
        asset_returns=asset_returns,
        benchmark_returns=benchmark,
        tradable_mask=np.ones(close_matrix.shape, dtype=bool),
        timestamps=timestamps,
        feature_cutoffs=timestamps.copy(),
    )
    hashes = tuple(str(value).lower() for value in source_hashes)
    payload = {
        "symbols": symbols,
        "timeframe": timeframe,
        "timestamps": [str(value) for value in timestamps],
        "close_sha256": hashlib.sha256(close_matrix.tobytes()).hexdigest(),
        "source_hashes": hashes,
        "local_features": LOCAL_FEATURE_NAMES_V221,
        "global_features": GLOBAL_FEATURE_NAMES_V221,
    }
    return PortfolioDatasetBundleV221(
        episode=episode,
        symbols=symbols,
        timeframe=str(timeframe),
        dataset_hash=_canonical_hash(payload),
        source_files=tuple(str(value) for value in source_files),
        source_hashes=hashes,
    )


def _market_path(data_root: Path, symbol: str, timeframe: str) -> Path:
    names = (f"{symbol}_{timeframe}.parquet", f"{symbol.lower()}_{timeframe}.parquet")
    for directory in ("derived", "adjusted", "processed", ""):
        for name in names:
            candidate = data_root / directory / name if directory else data_root / name
            if candidate.is_file():
                return candidate
    raise FileNotFoundError(f"no canonical {timeframe} dataset found for {symbol}")


def load_portfolio_dataset_v221(
    data_root: str | Path,
    *,
    symbols: Sequence[str],
    timeframe: str,
    benchmark_symbol: str | None = None,
    verify_hash: bool = True,
) -> PortfolioDatasetBundleV221:
    root = Path(data_root)
    frames: dict[str, pd.DataFrame] = {}
    paths: list[str] = []
    hashes: list[str] = []
    for raw_symbol in symbols:
        symbol = str(raw_symbol).strip().upper()
        path = _market_path(root, symbol, timeframe)
        frame, metadata = read_canonical_parquet(path, verify_hash=verify_hash)
        frames[symbol] = frame
        paths.append(str(path.resolve()))
        hashes.append(
            str(metadata.get("sha256"))
            if metadata and metadata.get("sha256")
            else sha256_file(path)
        )
    return build_portfolio_episode_from_frames_v221(
        frames,
        timeframe=timeframe,
        benchmark_symbol=benchmark_symbol,
        source_files=paths,
        source_hashes=hashes,
    )


def slice_portfolio_episode_v221(
    episode: PortfolioEpisodeV221,
    start: int,
    stop: int,
) -> PortfolioEpisodeV221:
    if not 0 <= start < stop <= episode.steps:
        raise ValueError("episode slice must be inside the return axis")
    observation_slice = slice(start, stop + 1)
    return PortfolioEpisodeV221(
        local_observations=episode.local_observations[observation_slice],
        global_observations=episode.global_observations[observation_slice],
        asset_returns=episode.asset_returns[start:stop],
        benchmark_returns=episode.benchmark_returns[start:stop],
        tradable_mask=episode.tradable_mask[observation_slice],
        timestamps=(
            None
            if episode.timestamps is None
            else np.asarray(episode.timestamps)[observation_slice]
        ),
        feature_cutoffs=(
            None
            if episode.feature_cutoffs is None
            else np.asarray(episode.feature_cutoffs)[observation_slice]
        ),
    )


def fit_feature_scaler_v221(episode: PortfolioEpisodeV221) -> FeatureScalerV221:
    local = episode.local_observations.reshape(
        -1, episode.local_observations.shape[-1]
    ).astype(np.float64)
    global_obs = episode.global_observations.astype(np.float64)
    local_scale = np.maximum(local.std(axis=0), 1e-6)
    global_scale = np.maximum(global_obs.std(axis=0), 1e-6)
    return FeatureScalerV221(
        local_mean=tuple(local.mean(axis=0)),
        local_scale=tuple(local_scale),
        global_mean=tuple(global_obs.mean(axis=0)),
        global_scale=tuple(global_scale),
        fitted_observations=episode.steps + 1,
    )


def transform_portfolio_episode_v221(
    episode: PortfolioEpisodeV221,
    scaler: FeatureScalerV221,
) -> PortfolioEpisodeV221:
    local_mean = np.asarray(scaler.local_mean, dtype=np.float64)
    local_scale = np.asarray(scaler.local_scale, dtype=np.float64)
    global_mean = np.asarray(scaler.global_mean, dtype=np.float64)
    global_scale = np.asarray(scaler.global_scale, dtype=np.float64)
    if episode.local_observations.shape[-1] != len(local_mean):
        raise ValueError("local feature dimension does not match scaler")
    if episode.global_observations.shape[-1] != len(global_mean):
        raise ValueError("global feature dimension does not match scaler")
    return PortfolioEpisodeV221(
        local_observations=(
            (episode.local_observations - local_mean) / local_scale
        ).astype(np.float32),
        global_observations=(
            (episode.global_observations - global_mean) / global_scale
        ).astype(np.float32),
        asset_returns=episode.asset_returns.copy(),
        benchmark_returns=episode.benchmark_returns.copy(),
        tradable_mask=episode.tradable_mask.copy(),
        timestamps=None if episode.timestamps is None else np.asarray(episode.timestamps).copy(),
        feature_cutoffs=(
            None
            if episode.feature_cutoffs is None
            else np.asarray(episode.feature_cutoffs).copy()
        ),
    )
