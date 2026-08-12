from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    avg_up = up.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_down = down.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_up / avg_down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = frame["close"].shift(1)
    tr = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - prev_close).abs(),
            (frame["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast_ema = close.ewm(span=fast, adjust=False).mean()
    slow_ema = close.ewm(span=slow, adjust=False).mean()
    line = fast_ema - slow_ema
    signal_line = line.ewm(span=signal, adjust=False).mean()
    return line, signal_line, line - signal_line


def bollinger_width(close: pd.Series, period: int = 20, stdev: float = 2.0) -> pd.Series:
    mid = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)
    return ((mid + stdev * std) - (mid - stdev * std)) / mid.replace(0, np.nan)


def obv(frame: pd.DataFrame) -> pd.Series:
    direction = np.sign(frame["close"].diff()).fillna(0.0)
    return (direction * frame["volume"].fillna(0.0)).cumsum()


def technical_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create causal features from already-closed candles only.

    Caller is responsible for excluding the currently forming candle before
    passing data here. No future shifts are used.
    """
    required = {"open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")

    out = pd.DataFrame(index=frame.index)
    c = frame["close"].astype(float)
    out["ret_1"] = c.pct_change()
    out["ret_5"] = c.pct_change(5)
    out["ret_20"] = c.pct_change(20)
    out["rsi_14"] = rsi(c, 14)
    line, sig, hist = macd(c)
    out["macd"] = line
    out["macd_signal"] = sig
    out["macd_hist"] = hist
    out["atr_14"] = atr(frame, 14)
    out["atr_pct"] = out["atr_14"] / c.replace(0, np.nan)
    out["bb_width_20"] = bollinger_width(c, 20)
    out["realized_vol_20"] = out["ret_1"].rolling(20).std(ddof=0) * np.sqrt(252)
    out["ema_20_dist"] = c / c.ewm(span=20, adjust=False).mean() - 1
    out["ema_50_dist"] = c / c.ewm(span=50, adjust=False).mean() - 1
    out["ema_200_dist"] = c / c.ewm(span=200, adjust=False).mean() - 1
    out["donchian_20"] = c / frame["high"].rolling(20).max().shift(1) - 1
    obv_series = obv(frame)
    out["obv_slope_10"] = obv_series.diff(10) / frame["volume"].rolling(10).sum().replace(0, np.nan)
    return out.replace([np.inf, -np.inf], np.nan)


def score_latest(features: pd.DataFrame) -> float:
    row = features.iloc[-1]
    score = 0.0
    score += 0.18 * np.tanh(float(row.get("ret_20", 0.0)) * 8)
    score += 0.16 * np.tanh(float(row.get("ret_5", 0.0)) * 15)
    score += 0.16 * np.tanh(float(row.get("macd_hist", 0.0)) * 20)
    score += 0.18 * np.tanh(float(row.get("ema_50_dist", 0.0)) * 8)
    score += 0.16 * np.tanh(float(row.get("ema_200_dist", 0.0)) * 6)
    rsi_value = float(row.get("rsi_14", 50.0))
    score += 0.10 * np.tanh((rsi_value - 50.0) / 15.0)
    score += 0.06 * np.tanh(float(row.get("obv_slope_10", 0.0)) * 3)
    return float(np.clip(score, -1.0, 1.0))
