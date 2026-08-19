from __future__ import annotations

import numpy as np
import pandas as pd


def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    avg_up = up.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_down = down.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_up / avg_down.replace(0.0, np.nan)
    value = 100.0 - 100.0 / (1.0 + rs)
    value = value.where(avg_down > 0.0, 100.0)
    value = value.where(avg_up > 0.0, 0.0)
    value = value.where((avg_up > 0.0) | (avg_down > 0.0), 50.0)
    return value


def _atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    previous = frame["close"].shift(1)
    tr = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous).abs(),
            (frame["low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast = close.ewm(span=12, adjust=False).mean()
    slow = close.ewm(span=26, adjust=False).mean()
    line = fast - slow
    signal = line.ewm(span=9, adjust=False).mean()
    return line, signal, line - signal


def _adx(frame: pd.DataFrame, period: int = 14) -> tuple[pd.Series, pd.Series, pd.Series]:
    high = frame["high"].astype(float)
    low = frame["low"].astype(float)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0.0), up_move, 0.0),
        index=frame.index,
        dtype=float,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0.0), down_move, 0.0),
        index=frame.index,
        dtype=float,
    )
    atr = _atr(frame, period)
    plus = plus_dm.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    minus = minus_dm.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    plus_di = 100.0 * plus / atr.replace(0.0, np.nan)
    minus_di = 100.0 * minus / atr.replace(0.0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    adx = dx.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    return adx, plus_di, minus_di


def _obv(frame: pd.DataFrame) -> pd.Series:
    direction = np.sign(frame["close"].diff()).fillna(0.0)
    return (direction * frame["volume"].fillna(0.0)).cumsum()


def _mfi(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    raw = typical * frame["volume"]
    direction = typical.diff()
    positive = raw.where(direction > 0.0, 0.0)
    negative = raw.where(direction < 0.0, 0.0).abs()
    pos = positive.rolling(period, min_periods=period).sum()
    neg = negative.rolling(period, min_periods=period).sum()
    ratio = pos / neg.replace(0.0, np.nan)
    value = 100.0 - 100.0 / (1.0 + ratio)
    value = value.where(neg > 0.0, 100.0)
    value = value.where(pos > 0.0, 0.0)
    value = value.where((pos > 0.0) | (neg > 0.0), 50.0)
    return value


def _cmf(frame: pd.DataFrame, period: int = 20) -> pd.Series:
    spread = (frame["high"] - frame["low"]).replace(0.0, np.nan)
    multiplier = (2.0 * frame["close"] - frame["high"] - frame["low"]) / spread
    mfv = multiplier * frame["volume"]
    return mfv.rolling(period, min_periods=period).sum() / frame["volume"].rolling(
        period,
        min_periods=period,
    ).sum().replace(0.0, np.nan)


def _cci(frame: pd.DataFrame, period: int = 20) -> pd.Series:
    typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    mean = typical.rolling(period, min_periods=period).mean()
    deviation = typical.rolling(period, min_periods=period).apply(
        lambda values: float(np.mean(np.abs(values - np.mean(values)))),
        raw=True,
    )
    return (typical - mean) / (0.015 * deviation.replace(0.0, np.nan))


def build_rl_features(frame: pd.DataFrame, rolling_window: int = 64) -> pd.DataFrame:
    """Broad causal feature bank from closed OHLCV candles only."""
    required = {"open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")
    if rolling_window < 20:
        raise ValueError("rolling_window must be >= 20")

    work = frame.copy()
    for column in required:
        work[column] = pd.to_numeric(work[column], errors="coerce")

    out = pd.DataFrame(index=work.index)
    close = work["close"].astype(float)
    open_ = work["open"].astype(float)
    high = work["high"].astype(float)
    low = work["low"].astype(float)
    volume = work["volume"].astype(float)

    out["log_ret_1"] = np.log(close / close.shift(1))
    out["log_ret_5"] = np.log(close / close.shift(5))
    out["log_ret_20"] = np.log(close / close.shift(20))
    out["gap_ret"] = np.log(open_ / close.shift(1))
    out["range_pct"] = (high - low) / close.replace(0.0, np.nan)
    out["body_pct"] = (close - open_) / open_.replace(0.0, np.nan)
    out["upper_wick_pct"] = (
        high - pd.concat([open_, close], axis=1).max(axis=1)
    ) / close.replace(0.0, np.nan)
    out["lower_wick_pct"] = (
        pd.concat([open_, close], axis=1).min(axis=1) - low
    ) / close.replace(0.0, np.nan)
    out["close_location"] = (2.0 * close - high - low) / (high - low).replace(0.0, np.nan)

    for length in (10, 20, 50, 100, 200):
        ema = close.ewm(span=length, adjust=False).mean()
        out[f"ema{length}_dist"] = close / ema.replace(0.0, np.nan) - 1.0

    sma20 = close.rolling(20, min_periods=20).mean()
    sma50 = close.rolling(50, min_periods=50).mean()
    out["sma20_dist"] = close / sma20.replace(0.0, np.nan) - 1.0
    out["sma50_dist"] = close / sma50.replace(0.0, np.nan) - 1.0

    out["rsi_2"] = _rsi(close, 2)
    out["rsi_14"] = _rsi(close, 14)
    macd, signal, hist = _macd(close)
    out["macd"] = macd
    out["macd_signal"] = signal
    out["macd_hist"] = hist
    out["macd_hist_pct"] = hist / close.replace(0.0, np.nan)

    atr14 = _atr(work, 14)
    out["atr_14"] = atr14
    out["atr_pct"] = atr14 / close.replace(0.0, np.nan)
    adx, plus_di, minus_di = _adx(work, 14)
    out["adx_14"] = adx
    out["plus_di_14"] = plus_di
    out["minus_di_14"] = minus_di
    out["di_spread"] = (plus_di - minus_di) / 100.0

    std20 = close.rolling(20, min_periods=20).std(ddof=0)
    out["bb_width_20"] = 4.0 * std20 / sma20.replace(0.0, np.nan)
    out["bb_z_20"] = (close - sma20) / std20.replace(0.0, np.nan)
    out["realized_vol_10"] = out["log_ret_1"].rolling(10, min_periods=10).std(ddof=0)
    out["realized_vol_20"] = out["log_ret_1"].rolling(20, min_periods=20).std(ddof=0)
    out["vol_of_vol_20"] = out["realized_vol_10"].rolling(20, min_periods=20).std(ddof=0)
    out["roc_5"] = close.pct_change(5)
    out["roc_20"] = close.pct_change(20)

    low14 = low.rolling(14, min_periods=14).min()
    high14 = high.rolling(14, min_periods=14).max()
    stoch_k = 100.0 * (close - low14) / (high14 - low14).replace(0.0, np.nan)
    out["stoch_k_14"] = stoch_k
    out["stoch_d_3"] = stoch_k.rolling(3, min_periods=3).mean()
    out["cci_20"] = _cci(work, 20)
    out["mfi_14"] = _mfi(work, 14)
    out["williams_r_14"] = -100.0 * (high14 - close) / (high14 - low14).replace(0.0, np.nan)

    prior_high = high.rolling(20, min_periods=20).max().shift(1)
    prior_low = low.rolling(20, min_periods=20).min().shift(1)
    out["donchian_high_dist_20"] = close / prior_high.replace(0.0, np.nan) - 1.0
    out["donchian_low_dist_20"] = close / prior_low.replace(0.0, np.nan) - 1.0

    volume_median = volume.rolling(rolling_window, min_periods=20).median()
    volume_mad = (volume - volume_median).abs().rolling(
        rolling_window,
        min_periods=20,
    ).median()
    out["volume_robust_z"] = (volume - volume_median) / volume_mad.replace(0.0, np.nan)
    out["volume_change_5"] = volume / volume.shift(5).replace(0.0, np.nan) - 1.0
    obv = _obv(work)
    out["obv_slope_10"] = obv.diff(10) / volume.rolling(10, min_periods=10).sum().replace(0.0, np.nan)
    out["cmf_20"] = _cmf(work, 20)

    typical = (high + low + close) / 3.0
    rolling_vwap = (typical * volume).rolling(20, min_periods=20).sum() / volume.rolling(
        20,
        min_periods=20,
    ).sum().replace(0.0, np.nan)
    out["rolling_vwap20_dist"] = close / rolling_vwap.replace(0.0, np.nan) - 1.0

    for column in (
        "log_ret_5",
        "log_ret_20",
        "range_pct",
        "body_pct",
        "ema20_dist",
        "ema50_dist",
        "atr_pct",
        "macd_hist_pct",
        "roc_20",
        "obv_slope_10",
        "cmf_20",
    ):
        mean = out[column].rolling(rolling_window, min_periods=20).mean()
        std = out[column].rolling(rolling_window, min_periods=20).std(ddof=0)
        out[f"{column}_z"] = (out[column] - mean) / std.replace(0.0, np.nan)

    return out.replace([np.inf, -np.inf], np.nan)
