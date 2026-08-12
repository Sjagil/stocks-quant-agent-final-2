from __future__ import annotations

import numpy as np
import pandas as pd


def build_rl_features(frame: pd.DataFrame, rolling_window: int = 64) -> pd.DataFrame:
    """Build causal, scale-robust features from already closed OHLCV candles.

    No centered windows, no negative shifts and no scaler fit on future rows are used.
    The caller must exclude an in-progress candle.
    """
    required = {"open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")
    if rolling_window < 20:
        raise ValueError("rolling_window must be >= 20")

    out = pd.DataFrame(index=frame.index)
    close = frame["close"].astype(float)
    volume = frame["volume"].astype(float)

    out["log_ret_1"] = np.log(close / close.shift(1))
    out["log_ret_5"] = np.log(close / close.shift(5))
    out["log_ret_20"] = np.log(close / close.shift(20))
    out["range_pct"] = (frame["high"] - frame["low"]) / close.replace(0, np.nan)
    out["close_to_open"] = close / frame["open"].replace(0, np.nan) - 1.0
    out["ema20_dist"] = close / close.ewm(span=20, adjust=False).mean() - 1.0
    out["ema50_dist"] = close / close.ewm(span=50, adjust=False).mean() - 1.0
    out["vol_20"] = out["log_ret_1"].rolling(20).std(ddof=0)

    vol_med = volume.rolling(rolling_window, min_periods=20).median()
    vol_mad = (volume - vol_med).abs().rolling(rolling_window, min_periods=20).median()
    out["volume_robust_z"] = (volume - vol_med) / vol_mad.replace(0, np.nan)

    # Rolling z-scores use only historical/current information at each row.
    for col in ["log_ret_5", "log_ret_20", "range_pct", "ema20_dist", "ema50_dist", "vol_20"]:
        mean = out[col].rolling(rolling_window, min_periods=20).mean()
        std = out[col].rolling(rolling_window, min_periods=20).std(ddof=0)
        out[f"{col}_z"] = (out[col] - mean) / std.replace(0, np.nan)

    return out.replace([np.inf, -np.inf], np.nan)
