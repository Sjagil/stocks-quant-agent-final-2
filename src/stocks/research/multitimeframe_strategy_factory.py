from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd

TIMEFRAMES = ("15m", "1h", "2h", "4h", "1d", "1w")


@dataclass(frozen=True)
class MTFHypothesis:
    hypothesis_id: str
    template: str
    family: str
    params: dict[str, Any]

    @property
    def params_json(self) -> str:
        return json.dumps(self.params, sort_keys=True, separators=(",", ":"))

    def as_record(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "template": self.template,
            "family": self.family,
            "params_json": self.params_json,
            "primary_timeframe": "1h",
            "execution_timeframe": "15m",
            "execution_contract": "NEXT_15M_OPEN_FIXED_HORIZON",
            "source_engine": "multitimeframe_strategy_factory_v2_15_1",
            "research_stage": "PURGED_WALK_FORWARD",
            "execution_authority": "NONE",
        }


def _hypothesis_id(template: str, params: dict[str, Any]) -> str:
    text = json.dumps(
        {"template": template, "params": params},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


def generate_multitimeframe_hypotheses() -> list[MTFHypothesis]:
    specs: list[tuple[str, str, dict[str, Any]]] = []

    for rsi_max in (40.0, 45.0, 50.0):
        for volume_z in (-0.5, 0.0, 0.5):
            specs.append(
                (
                    "mtf_trend_pullback",
                    "MTF_TREND_PULLBACK",
                    {
                        "rsi_1h_max": rsi_max,
                        "min_15m_volume_z": volume_z,
                        "horizon_15m_bars": 16,
                    },
                )
            )

    for distance in (0.0025, 0.005, 0.01):
        for volume_z in (0.0, 0.5, 1.0):
            specs.append(
                (
                    "mtf_breakout",
                    "MTF_BREAKOUT",
                    {
                        "max_1h_donchian_distance": distance,
                        "min_15m_volume_z": volume_z,
                        "horizon_15m_bars": 24,
                    },
                )
            )

    for roc_1h in (0.0, 0.005, 0.01):
        for roc_15m in (0.0, 0.0025, 0.005):
            specs.append(
                (
                    "mtf_momentum",
                    "MTF_MOMENTUM",
                    {
                        "min_1h_roc20": roc_1h,
                        "min_15m_roc5": roc_15m,
                        "horizon_15m_bars": 32,
                    },
                )
            )

    for rsi_max in (30.0, 35.0, 40.0):
        for reversal_roc in (0.0, 0.0025):
            specs.append(
                (
                    "mtf_mean_reversion",
                    "MTF_MEAN_REVERSION",
                    {
                        "rsi_1h_max": rsi_max,
                        "min_15m_roc5": reversal_roc,
                        "horizon_15m_bars": 16,
                    },
                )
            )

    return [
        MTFHypothesis(
            hypothesis_id=_hypothesis_id(template, params),
            template=template,
            family=family,
            params=params,
        )
        for template, family, params in specs
    ]


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    diff = close.diff()
    gain = diff.clip(lower=0.0)
    loss = (-diff.clip(upper=0.0))
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - 100.0 / (1.0 + rs)


def _features(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy().sort_index()
    work.index = pd.to_datetime(work.index, utc=True)
    close = pd.to_numeric(work["close"], errors="coerce")
    high = pd.to_numeric(work["high"], errors="coerce")
    low = pd.to_numeric(work["low"], errors="coerce")
    volume = pd.to_numeric(work["volume"], errors="coerce")

    out = pd.DataFrame(index=work.index)
    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()

    out["close"] = close
    out["ema20_gt_ema50"] = ema20 > ema50
    out["ema50_gt_ema200"] = ema50 > ema200
    out["close_gt_ema20"] = close > ema20
    out["close_gt_ema50"] = close > ema50
    out["rsi14"] = _rsi(close, 14)
    out["roc5"] = close.pct_change(5)
    out["roc20"] = close.pct_change(20)

    prior_high = high.shift(1).rolling(20, min_periods=20).max()
    out["donchian_high_distance"] = close / prior_high - 1.0

    vol_mean = volume.rolling(40, min_periods=20).mean()
    vol_std = volume.rolling(40, min_periods=20).std(ddof=0)
    out["volume_z"] = (volume - vol_mean) / vol_std.replace(0.0, np.nan)

    true_range = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr14_pct"] = (
        true_range.ewm(alpha=1.0 / 14.0, adjust=False).mean()
        / close.replace(0.0, np.nan)
    )
    return out.replace([np.inf, -np.inf], np.nan)


def align_multitimeframe_features(
    frames: Mapping[str, pd.DataFrame],
    *,
    higher_timeframe_one_bar_lag: bool = True,
) -> pd.DataFrame:
    missing = [tf for tf in TIMEFRAMES if tf not in frames]
    if missing:
        raise ValueError(f"missing required timeframes: {missing}")

    base = _features(frames["15m"])
    aligned = base.add_prefix("15m_")

    for timeframe in TIMEFRAMES[1:]:
        features = _features(frames[timeframe])
        # Higher-timeframe bars in the current data plane can be timestamped
        # at their first source bar. Lagging one complete HTF bar prevents a
        # 15m decision from observing an overlapping/incomplete HTF candle.
        if higher_timeframe_one_bar_lag:
            features = features.shift(1)
        features = features.add_prefix(f"{timeframe}_")
        features = features.reindex(aligned.index, method="ffill")
        aligned = aligned.join(features, how="left")

    return aligned


def _higher_trend(row: pd.Series) -> bool:
    return (
        bool(row["1w_ema20_gt_ema50"])
        and bool(row["1d_ema20_gt_ema50"])
        and bool(row["4h_ema20_gt_ema50"])
        and bool(row["2h_ema20_gt_ema50"])
    )


def _signal(row: pd.Series, hypothesis: MTFHypothesis) -> bool:
    p = hypothesis.params
    if hypothesis.template == "mtf_trend_pullback":
        return (
            _higher_trend(row)
            and bool(row["1h_close_gt_ema50"])
            and float(row["1h_rsi14"]) <= float(p["rsi_1h_max"])
            and bool(row["15m_close_gt_ema20"])
            and float(row["15m_roc5"]) > 0.0
            and float(row["15m_volume_z"]) >= float(p["min_15m_volume_z"])
        )

    if hypothesis.template == "mtf_breakout":
        return (
            _higher_trend(row)
            and bool(row["1h_close_gt_ema20"])
            and abs(float(row["1h_donchian_high_distance"]))
            <= float(p["max_1h_donchian_distance"])
            and float(row["15m_roc5"]) > 0.0
            and float(row["15m_volume_z"]) >= float(p["min_15m_volume_z"])
        )

    if hypothesis.template == "mtf_momentum":
        return (
            bool(row["1w_ema20_gt_ema50"])
            and bool(row["1d_ema20_gt_ema50"])
            and bool(row["4h_ema20_gt_ema50"])
            and float(row["1h_roc20"]) >= float(p["min_1h_roc20"])
            and float(row["15m_roc5"]) >= float(p["min_15m_roc5"])
            and bool(row["15m_close_gt_ema20"])
        )

    if hypothesis.template == "mtf_mean_reversion":
        return (
            bool(row["1d_ema20_gt_ema50"])
            and bool(row["4h_close_gt_ema50"])
            and float(row["1h_rsi14"]) <= float(p["rsi_1h_max"])
            and float(row["15m_roc5"]) >= float(p["min_15m_roc5"])
            and bool(row["15m_close_gt_ema20"])
        )

    raise ValueError(f"unsupported MTF template: {hypothesis.template}")


def evaluate_multitimeframe_hypothesis(
    hypothesis: MTFHypothesis,
    frames: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    base = frames["15m"].copy().sort_index()
    base.index = pd.to_datetime(base.index, utc=True)
    features = align_multitimeframe_features(frames)

    required = [
        "15m_close_gt_ema20",
        "15m_roc5",
        "15m_volume_z",
        "1h_rsi14",
        "1h_roc20",
        "1h_donchian_high_distance",
        "2h_ema20_gt_ema50",
        "4h_ema20_gt_ema50",
        "1d_ema20_gt_ema50",
        "1w_ema20_gt_ema50",
    ]
    features = features.dropna(subset=required)

    horizon = int(hypothesis.params["horizon_15m_bars"])
    rows: list[dict[str, Any]] = []

    for timestamp, row in features.iterrows():
        if not _signal(row, hypothesis):
            continue

        decision_pos = base.index.searchsorted(timestamp, side="left")
        entry_pos = decision_pos + 1
        exit_pos = entry_pos + horizon - 1
        if entry_pos >= len(base) or exit_pos >= len(base):
            continue

        entry_price = float(base["open"].iloc[entry_pos])
        exit_price = float(base["close"].iloc[exit_pos])
        if not (
            math.isfinite(entry_price)
            and math.isfinite(exit_price)
            and entry_price > 0.0
        ):
            continue

        rows.append(
            {
                "hypothesis_id": hypothesis.hypothesis_id,
                "strategy": hypothesis.template,
                "family": hypothesis.family,
                "decision_timestamp": timestamp,
                "entry_timestamp": base.index[entry_pos],
                "exit_timestamp": base.index[exit_pos],
                "entry_price": entry_price,
                "exit_price": exit_price,
                "gross_return": exit_price / entry_price - 1.0,
                "horizon_15m_bars": horizon,
                "execution_contract": "NEXT_15M_OPEN_FIXED_HORIZON",
                "execution_authority": "NONE",
            }
        )

    return pd.DataFrame(rows)


def trade_metrics(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    cost_bps_per_side: float,
) -> dict[str, float | int]:
    if trades.empty:
        return {
            "trades": 0,
            "net_expectancy": math.nan,
            "net_expectancy_bps": math.nan,
            "profit_factor": math.nan,
            "total_return": 0.0,
        }

    timestamps = pd.to_datetime(trades["decision_timestamp"], utc=True)
    subset = trades.loc[
        timestamps.between(start, end, inclusive="both")
    ].copy()
    if subset.empty:
        return {
            "trades": 0,
            "net_expectancy": math.nan,
            "net_expectancy_bps": math.nan,
            "profit_factor": math.nan,
            "total_return": 0.0,
        }

    cost = 2.0 * float(cost_bps_per_side) / 10_000.0
    net = subset["gross_return"].astype(float) - cost
    wins = float(net.loc[net > 0.0].sum())
    losses = float(-net.loc[net < 0.0].sum())
    pf = (
        wins / losses
        if losses > 0.0
        else math.inf if wins > 0.0 else math.nan
    )
    expectancy = float(net.mean())
    return {
        "trades": int(len(net)),
        "net_expectancy": expectancy,
        "net_expectancy_bps": expectancy * 10_000.0,
        "profit_factor": pf,
        "total_return": float((1.0 + net).prod() - 1.0),
    }
