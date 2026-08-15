from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from dataclasses import asdict, dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd

from stocks.intelligence_agent.strategy_combo_research_lab import (
    FeatureCache,
    TradeBatch,
    trades_from_signals,
)


SOURCE_ENGINE = "indicator_discovery_v1"
PRIMARY_TIMEFRAME = "1h"
PARAMETER_BASIS = "BAR_NATIVE_1H_CAUSAL"


@dataclass(frozen=True)
class IndicatorTemplate:
    name: str
    family: str
    default_params: dict[str, Any]
    choices: dict[str, tuple[Any, ...]]
    execution_contract: str = "NEXT_OPEN_REPLAY"


@dataclass(frozen=True)
class IndicatorHypothesis:
    hypothesis_id: str
    template: str
    family: str
    params: dict[str, Any]
    primary_timeframe: str = PRIMARY_TIMEFRAME
    execution_timeframe: str = PRIMARY_TIMEFRAME
    execution_contract: str = "NEXT_OPEN_REPLAY"
    source_engine: str = SOURCE_ENGINE
    research_stage: str = "EXPERIMENTAL"
    execution_authority: str = "NONE"

    def as_record(self) -> dict[str, Any]:
        result = asdict(self)
        result["params_json"] = json.dumps(
            self.params,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        result.pop("params", None)
        return result


def template_registry() -> tuple[IndicatorTemplate, ...]:
    return (
        IndicatorTemplate(
            "rsi_trend_reversion",
            "oscillator_mean_reversion",
            {"rsi_period": 5, "entry": 20, "exit": 65, "trend_ema": 200, "max_hold": 30},
            {"rsi_period": (3, 5, 7, 10, 14), "entry": (10, 15, 20, 25, 30), "exit": (55, 65, 75, 85), "trend_ema": (100, 150, 200), "max_hold": (10, 20, 30, 50)},
        ),
        IndicatorTemplate(
            "stoch_trend_reversion",
            "oscillator_mean_reversion",
            {"period": 14, "smooth": 3, "entry": 15, "exit": 70, "trend_ema": 150, "max_hold": 30},
            {"period": (7, 10, 14, 21), "smooth": (2, 3, 5), "entry": (10, 15, 20, 25), "exit": (60, 70, 80, 90), "trend_ema": (100, 150, 200), "max_hold": (10, 20, 30, 50)},
        ),
        IndicatorTemplate(
            "cci_trend_reversion",
            "oscillator_mean_reversion",
            {"period": 20, "entry": -150.0, "exit": 50.0, "trend_ema": 150, "max_hold": 30},
            {"period": (10, 14, 20, 30, 40), "entry": (-100.0, -150.0, -200.0), "exit": (0.0, 50.0, 100.0), "trend_ema": (100, 150, 200), "max_hold": (10, 20, 30, 50)},
        ),
        IndicatorTemplate(
            "mfi_trend_reversion",
            "volume_oscillator_reversion",
            {"period": 14, "entry": 20.0, "exit": 65.0, "trend_ema": 150, "max_hold": 30},
            {"period": (7, 10, 14, 21), "entry": (10.0, 15.0, 20.0, 25.0), "exit": (55.0, 65.0, 75.0, 85.0), "trend_ema": (100, 150, 200), "max_hold": (10, 20, 30, 50)},
        ),
        IndicatorTemplate(
            "macd_adx_reentry",
            "trend_momentum",
            {"fast": 8, "slow": 21, "signal": 5, "adx_period": 14, "adx_min": 18.0, "trend_ema": 100, "max_hold": 50},
            {"fast": (5, 8, 12), "slow": (18, 21, 26, 34), "signal": (4, 5, 9), "adx_period": (10, 14, 20), "adx_min": (15.0, 18.0, 22.0, 25.0), "trend_ema": (50, 100, 150, 200), "max_hold": (20, 35, 50, 80)},
        ),
        IndicatorTemplate(
            "roc_volume_momentum",
            "momentum_breakout",
            {"roc_period": 20, "roc_entry": 0.04, "rvol_period": 20, "rvol_min": 1.2, "trend_ema": 100, "max_hold": 50},
            {"roc_period": (10, 20, 40, 63), "roc_entry": (0.02, 0.04, 0.06, 0.10), "rvol_period": (10, 20, 30), "rvol_min": (1.0, 1.2, 1.5, 2.0), "trend_ema": (50, 100, 150, 200), "max_hold": (20, 35, 50, 80)},
        ),
        IndicatorTemplate(
            "bollinger_z_reversion",
            "volatility_mean_reversion",
            {"period": 20, "entry_z": -2.0, "exit_z": 0.0, "trend_ema": 200, "max_hold": 30},
            {"period": (10, 14, 20, 30, 40), "entry_z": (-1.5, -2.0, -2.5, -3.0), "exit_z": (-0.5, 0.0, 0.5, 1.0), "trend_ema": (100, 150, 200), "max_hold": (10, 20, 30, 50)},
        ),
        IndicatorTemplate(
            "squeeze_breakout",
            "volatility_breakout",
            {"compression_period": 20, "compression_max": 0.9, "breakout_lookback": 20, "rvol_period": 20, "rvol_min": 1.1, "exit_ema": 20, "max_hold": 50},
            {"compression_period": (10, 20, 30), "compression_max": (0.65, 0.75, 0.9, 1.05), "breakout_lookback": (10, 20, 40, 63), "rvol_period": (10, 20, 30), "rvol_min": (1.0, 1.1, 1.3, 1.5), "exit_ema": (10, 20, 30, 50), "max_hold": (20, 35, 50, 80)},
        ),
        IndicatorTemplate(
            "adx_rsi_pullback",
            "trend_pullback",
            {"fast_ema": 20, "slow_ema": 100, "adx_period": 14, "adx_min": 20.0, "rsi_period": 7, "rsi_entry": 35.0, "rsi_exit": 65.0, "max_hold": 40},
            {"fast_ema": (10, 20, 30, 50), "slow_ema": (75, 100, 150, 200), "adx_period": (10, 14, 20), "adx_min": (18.0, 20.0, 25.0, 30.0), "rsi_period": (5, 7, 10, 14), "rsi_entry": (25.0, 30.0, 35.0, 40.0), "rsi_exit": (55.0, 65.0, 75.0), "max_hold": (20, 40, 60)},
        ),
        IndicatorTemplate(
            "williams_trend_reversion",
            "oscillator_mean_reversion",
            {"period": 14, "entry": -90.0, "exit": -30.0, "trend_ema": 150, "max_hold": 30},
            {"period": (7, 10, 14, 21, 28), "entry": (-95.0, -90.0, -85.0, -80.0), "exit": (-50.0, -30.0, -20.0, -10.0), "trend_ema": (100, 150, 200), "max_hold": (10, 20, 30, 50)},
        ),
        IndicatorTemplate(
            "obv_breakout",
            "volume_breakout",
            {"lookback": 20, "obv_ema": 20, "rvol_period": 20, "rvol_min": 1.2, "exit_ema": 20, "max_hold": 50},
            {"lookback": (10, 20, 40, 63), "obv_ema": (10, 20, 40), "rvol_period": (10, 20, 30), "rvol_min": (1.0, 1.2, 1.5, 2.0), "exit_ema": (10, 20, 30, 50), "max_hold": (20, 35, 50, 80)},
        ),
        IndicatorTemplate(
            "rolling_vwap_reclaim",
            "price_volume_reclaim",
            {"vwap_period": 20, "trend_ema": 100, "rsi_period": 7, "rsi_max": 70.0, "max_hold": 40},
            {"vwap_period": (10, 20, 40, 63), "trend_ema": (50, 100, 150, 200), "rsi_period": (5, 7, 10, 14), "rsi_max": (60.0, 65.0, 70.0, 75.0), "max_hold": (20, 40, 60)},
        ),
        IndicatorTemplate(
            "donchian_adx_breakout",
            "trend_breakout",
            {"lookback": 20, "exit_lookback": 10, "adx_period": 14, "adx_min": 20.0, "max_hold": 80},
            {"lookback": (10, 20, 40, 63), "exit_lookback": (5, 10, 20, 30), "adx_period": (10, 14, 20), "adx_min": (15.0, 20.0, 25.0, 30.0), "max_hold": (35, 50, 80, 120)},
        ),
        IndicatorTemplate(
            "multi_signal_ensemble",
            "indicator_ensemble",
            {"trend_ema": 100, "rsi_period": 7, "rsi_max": 60.0, "macd_fast": 8, "macd_slow": 21, "macd_signal": 5, "adx_period": 14, "adx_min": 18.0, "rvol_period": 20, "rvol_min": 1.0, "entry_votes": 4, "exit_votes": 2, "max_hold": 50},
            {"trend_ema": (50, 100, 150, 200), "rsi_period": (5, 7, 10, 14), "rsi_max": (50.0, 60.0, 70.0), "macd_fast": (5, 8, 12), "macd_slow": (18, 21, 26), "macd_signal": (4, 5, 9), "adx_period": (10, 14, 20), "adx_min": (15.0, 18.0, 22.0, 25.0), "rvol_period": (10, 20, 30), "rvol_min": (0.8, 1.0, 1.2, 1.5), "entry_votes": (3, 4, 5), "exit_votes": (1, 2, 3), "max_hold": (20, 35, 50, 80)},
        ),
    )


def _stable_seed(name: str, seed: int) -> int:
    digest = hashlib.sha256(f"{seed}|{name}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 2_147_483_647


def _hypothesis_id(template: str, params: Mapping[str, Any]) -> str:
    payload = json.dumps(
        {
            "template": template,
            "params": dict(params),
            "timeframe": PRIMARY_TIMEFRAME,
            "source_engine": SOURCE_ENGINE,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _params_valid(template: str, params: Mapping[str, Any]) -> bool:
    if "fast" in params and "slow" in params and int(params["fast"]) >= int(params["slow"]):
        return False
    if "fast_ema" in params and "slow_ema" in params and int(params["fast_ema"]) >= int(params["slow_ema"]):
        return False
    if "macd_fast" in params and "macd_slow" in params and int(params["macd_fast"]) >= int(params["macd_slow"]):
        return False
    if "entry" in params and "exit" in params:
        if template in {"rsi_trend_reversion", "stoch_trend_reversion", "mfi_trend_reversion"} and float(params["entry"]) >= float(params["exit"]):
            return False
        if template == "cci_trend_reversion" and float(params["entry"]) >= float(params["exit"]):
            return False
        if template == "williams_trend_reversion" and float(params["entry"]) >= float(params["exit"]):
            return False
    if "entry_z" in params and "exit_z" in params and float(params["entry_z"]) >= float(params["exit_z"]):
        return False
    if "entry_votes" in params and "exit_votes" in params and int(params["entry_votes"]) <= int(params["exit_votes"]):
        return False
    return True


def _sample_variants(template: IndicatorTemplate, maximum: int, seed: int) -> list[dict[str, Any]]:
    if maximum <= 0:
        raise ValueError("maximum variants must be positive")
    default = dict(template.default_params)
    output = [default]
    seen = {json.dumps(default, sort_keys=True, default=str)}

    for key, values in template.choices.items():
        for value in values:
            candidate = dict(default)
            candidate[key] = value
            marker = json.dumps(candidate, sort_keys=True, default=str)
            if marker not in seen and _params_valid(template.name, candidate):
                output.append(candidate)
                seen.add(marker)
            if len(output) >= maximum:
                return output

    keys = tuple(template.choices)
    pools = [template.choices[key] for key in keys]
    combinations = list(itertools.product(*pools))
    rng = random.Random(_stable_seed(template.name, seed))
    rng.shuffle(combinations)
    for values in combinations:
        candidate = dict(zip(keys, values, strict=True))
        marker = json.dumps(candidate, sort_keys=True, default=str)
        if marker in seen or not _params_valid(template.name, candidate):
            continue
        output.append(candidate)
        seen.add(marker)
        if len(output) >= maximum:
            break
    return output


def generate_indicator_hypotheses(
    *,
    max_variants_per_template: int,
    seed: int,
    enabled_templates: set[str] | None = None,
) -> list[IndicatorHypothesis]:
    output: list[IndicatorHypothesis] = []
    for template in template_registry():
        if enabled_templates is not None and template.name not in enabled_templates:
            continue
        for params in _sample_variants(template, max_variants_per_template, seed):
            output.append(
                IndicatorHypothesis(
                    hypothesis_id=_hypothesis_id(template.name, params),
                    template=template.name,
                    family=template.family,
                    params=params,
                    execution_contract=template.execution_contract,
                )
            )
    ids = [item.hypothesis_id for item in output]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate indicator hypothesis ids")
    return output


def indicator_hypotheses_frame(items: list[IndicatorHypothesis]) -> pd.DataFrame:
    return pd.DataFrame([item.as_record() for item in items])


def _shift(values: np.ndarray, periods: int = 1) -> np.ndarray:
    result = np.full(len(values), np.nan, dtype=float)
    if periods < len(values):
        result[periods:] = values[:-periods]
    return result


def _cross_above(left: np.ndarray, right: np.ndarray | float) -> np.ndarray:
    a = np.asarray(left, dtype=float)
    b = np.full(len(a), float(right), dtype=float) if np.isscalar(right) else np.asarray(right, dtype=float)
    return (a > b) & (_shift(a) <= _shift(b))


def _cross_below(left: np.ndarray, right: np.ndarray | float) -> np.ndarray:
    a = np.asarray(left, dtype=float)
    b = np.full(len(a), float(right), dtype=float) if np.isscalar(right) else np.asarray(right, dtype=float)
    return (a < b) & (_shift(a) >= _shift(b))


def stochastic_k(cache: FeatureCache, period: int, smooth: int) -> np.ndarray:
    high = cache.rolling_max("high", int(period))
    low = cache.rolling_min("low", int(period))
    close = cache.arr("close")
    raw = 100.0 * (close - low) / np.where((high - low) == 0, np.nan, high - low)
    return pd.Series(raw).rolling(int(smooth), min_periods=int(smooth)).mean().to_numpy()


def cci(cache: FeatureCache, period: int) -> np.ndarray:
    typical = (cache.arr("high") + cache.arr("low") + cache.arr("close")) / 3.0
    series = pd.Series(typical)
    mean = series.rolling(int(period), min_periods=int(period)).mean()
    mad = series.rolling(int(period), min_periods=int(period)).apply(
        lambda values: float(np.mean(np.abs(values - np.mean(values)))), raw=True
    )
    return ((series - mean) / (0.015 * mad.replace(0.0, np.nan))).to_numpy()


def mfi(cache: FeatureCache, period: int) -> np.ndarray:
    typical = (cache.arr("high") + cache.arr("low") + cache.arr("close")) / 3.0
    volume = np.nan_to_num(cache.arr("volume"), nan=0.0)
    money = typical * volume
    delta = np.diff(typical, prepend=np.nan)
    positive = np.where(delta > 0, money, 0.0)
    negative = np.where(delta < 0, money, 0.0)
    pos = pd.Series(positive).rolling(int(period), min_periods=int(period)).sum()
    neg = pd.Series(negative).rolling(int(period), min_periods=int(period)).sum()
    ratio = pos / neg.replace(0.0, np.nan)
    values = 100.0 - 100.0 / (1.0 + ratio)
    values = values.where(neg != 0.0, 100.0)
    return values.to_numpy()


def roc(cache: FeatureCache, period: int) -> np.ndarray:
    close = pd.Series(cache.arr("close"))
    return close.pct_change(int(period)).to_numpy()


def relative_volume(cache: FeatureCache, period: int) -> np.ndarray:
    volume = pd.Series(np.nan_to_num(cache.arr("volume"), nan=0.0))
    baseline = volume.shift(1).rolling(int(period), min_periods=int(period)).mean()
    return (volume / baseline.replace(0.0, np.nan)).to_numpy()


def obv(cache: FeatureCache) -> np.ndarray:
    close = cache.arr("close")
    volume = np.nan_to_num(cache.arr("volume"), nan=0.0)
    direction = np.sign(np.diff(close, prepend=close[0]))
    return np.cumsum(direction * volume)


def rolling_vwap(cache: FeatureCache, period: int) -> np.ndarray:
    typical = (cache.arr("high") + cache.arr("low") + cache.arr("close")) / 3.0
    volume = np.nan_to_num(cache.arr("volume"), nan=0.0)
    numerator = pd.Series(typical * volume).rolling(int(period), min_periods=int(period)).sum()
    denominator = pd.Series(volume).rolling(int(period), min_periods=int(period)).sum()
    return (numerator / denominator.replace(0.0, np.nan)).to_numpy()


def _safe_score(condition: np.ndarray, weight: float = 1.0) -> np.ndarray:
    return np.asarray(condition, dtype=float) * float(weight)


def build_indicator_trades(
    hypothesis: IndicatorHypothesis,
    frame: pd.DataFrame,
    cache: FeatureCache,
) -> TradeBatch:
    p = hypothesis.params
    close = cache.arr("close")
    template = hypothesis.template
    n = len(frame)
    false = np.zeros(n, dtype=bool)
    entry = false.copy()
    exit_signal = false.copy()
    score = np.zeros(n, dtype=float)
    max_hold = int(p.get("max_hold", 50))

    if template == "rsi_trend_reversion":
        r = cache.rsi(int(p["rsi_period"]))
        trend = cache.ema("close", int(p["trend_ema"]))
        entry = (r <= float(p["entry"])) & (close > trend)
        exit_signal = (r >= float(p["exit"])) | (close < trend)
        score = np.nan_to_num((float(p["entry"]) - r) / 20.0, nan=0.0)

    elif template == "stoch_trend_reversion":
        k = stochastic_k(cache, int(p["period"]), int(p["smooth"]))
        trend = cache.ema("close", int(p["trend_ema"]))
        entry = (k <= float(p["entry"])) & (close > trend)
        exit_signal = (k >= float(p["exit"])) | (close < trend)
        score = np.nan_to_num((float(p["entry"]) - k) / 20.0, nan=0.0)

    elif template == "cci_trend_reversion":
        values = cci(cache, int(p["period"]))
        trend = cache.ema("close", int(p["trend_ema"]))
        entry = (values <= float(p["entry"])) & (close > trend)
        exit_signal = (values >= float(p["exit"])) | (close < trend)
        score = np.nan_to_num((float(p["entry"]) - values) / 100.0, nan=0.0)

    elif template == "mfi_trend_reversion":
        values = mfi(cache, int(p["period"]))
        trend = cache.ema("close", int(p["trend_ema"]))
        entry = (values <= float(p["entry"])) & (close > trend)
        exit_signal = (values >= float(p["exit"])) | (close < trend)
        score = np.nan_to_num((float(p["entry"]) - values) / 20.0, nan=0.0)

    elif template == "macd_adx_reentry":
        hist = cache.macd_hist(int(p["fast"]), int(p["slow"]), int(p["signal"]))
        adx, plus, minus = cache.adx(int(p["adx_period"]))
        trend = cache.ema("close", int(p["trend_ema"]))
        entry = _cross_above(hist, 0.0) & (adx >= float(p["adx_min"])) & (plus > minus) & (close > trend)
        exit_signal = _cross_below(hist, 0.0) | (close < trend)
        score = np.nan_to_num(hist / np.where(cache.atr(14) == 0, np.nan, cache.atr(14)), nan=0.0)

    elif template == "roc_volume_momentum":
        values = roc(cache, int(p["roc_period"]))
        rvol = relative_volume(cache, int(p["rvol_period"]))
        trend = cache.ema("close", int(p["trend_ema"]))
        entry = (values >= float(p["roc_entry"])) & (rvol >= float(p["rvol_min"])) & (close > trend)
        exit_signal = (values <= 0.0) | (close < trend)
        score = np.nan_to_num(values * np.clip(rvol, 0.0, 3.0), nan=0.0)

    elif template == "bollinger_z_reversion":
        period = int(p["period"])
        mean = cache.sma("close", period)
        std = cache.rolling_std("close", period)
        z = (close - mean) / np.where(std == 0, np.nan, std)
        trend = cache.ema("close", int(p["trend_ema"]))
        entry = (z <= float(p["entry_z"])) & (close > trend)
        exit_signal = (z >= float(p["exit_z"])) | (close < trend)
        score = np.nan_to_num(-z, nan=0.0)

    elif template == "squeeze_breakout":
        period = int(p["compression_period"])
        std = cache.rolling_std("close", period)
        atr = cache.atr(period)
        compression = (2.0 * std) / np.where(atr == 0, np.nan, atr)
        prior_high = cache.rolling_max("high", int(p["breakout_lookback"]), shift=1)
        rvol = relative_volume(cache, int(p["rvol_period"]))
        exit_ema = cache.ema("close", int(p["exit_ema"]))
        compressed_recently = pd.Series(compression <= float(p["compression_max"])).rolling(5, min_periods=1).max().astype(bool).to_numpy()
        entry = compressed_recently & (close > prior_high) & (rvol >= float(p["rvol_min"]))
        exit_signal = close < exit_ema
        score = np.nan_to_num((close / prior_high - 1.0) * np.clip(rvol, 0.0, 3.0), nan=0.0)

    elif template == "adx_rsi_pullback":
        fast = cache.ema("close", int(p["fast_ema"]))
        slow = cache.ema("close", int(p["slow_ema"]))
        adx, plus, minus = cache.adx(int(p["adx_period"]))
        r = cache.rsi(int(p["rsi_period"]))
        entry = (fast > slow) & (adx >= float(p["adx_min"])) & (plus > minus) & (r <= float(p["rsi_entry"]))
        exit_signal = (r >= float(p["rsi_exit"])) | (fast < slow)
        score = np.nan_to_num(adx / 100.0 + (float(p["rsi_entry"]) - r) / 50.0, nan=0.0)

    elif template == "williams_trend_reversion":
        values = cache.williams_r(int(p["period"]))
        trend = cache.ema("close", int(p["trend_ema"]))
        entry = (values <= float(p["entry"])) & (close > trend)
        exit_signal = (values >= float(p["exit"])) | (close < trend)
        score = np.nan_to_num((-values - 80.0) / 20.0, nan=0.0)

    elif template == "obv_breakout":
        values = obv(cache)
        obv_mean = pd.Series(values).ewm(span=int(p["obv_ema"]), adjust=False, min_periods=int(p["obv_ema"])).mean().to_numpy()
        prior_high = cache.rolling_max("high", int(p["lookback"]), shift=1)
        rvol = relative_volume(cache, int(p["rvol_period"]))
        exit_ema = cache.ema("close", int(p["exit_ema"]))
        entry = (close > prior_high) & (values > obv_mean) & (rvol >= float(p["rvol_min"]))
        exit_signal = close < exit_ema
        score = np.nan_to_num((values - obv_mean) / np.where(np.abs(obv_mean) < 1.0, np.nan, np.abs(obv_mean)), nan=0.0)

    elif template == "rolling_vwap_reclaim":
        vw = rolling_vwap(cache, int(p["vwap_period"]))
        trend = cache.ema("close", int(p["trend_ema"]))
        r = cache.rsi(int(p["rsi_period"]))
        entry = _cross_above(close, vw) & (close > trend) & (r <= float(p["rsi_max"]))
        exit_signal = _cross_below(close, vw) | (close < trend)
        score = np.nan_to_num((close / vw - 1.0), nan=0.0)

    elif template == "donchian_adx_breakout":
        high = cache.rolling_max("high", int(p["lookback"]), shift=1)
        low = cache.rolling_min("low", int(p["exit_lookback"]), shift=1)
        adx, plus, minus = cache.adx(int(p["adx_period"]))
        entry = (close > high) & (adx >= float(p["adx_min"])) & (plus > minus)
        exit_signal = close < low
        score = np.nan_to_num(adx / 100.0 + (close / high - 1.0), nan=0.0)

    elif template == "multi_signal_ensemble":
        trend = close > cache.ema("close", int(p["trend_ema"]))
        r = cache.rsi(int(p["rsi_period"]))
        hist = cache.macd_hist(int(p["macd_fast"]), int(p["macd_slow"]), int(p["macd_signal"]))
        adx, plus, minus = cache.adx(int(p["adx_period"]))
        rvol = relative_volume(cache, int(p["rvol_period"]))
        votes = (
            _safe_score(trend)
            + _safe_score(r <= float(p["rsi_max"]))
            + _safe_score(hist > 0.0)
            + _safe_score((adx >= float(p["adx_min"])) & (plus > minus))
            + _safe_score(rvol >= float(p["rvol_min"]))
        )
        entry = (votes >= int(p["entry_votes"])) & (_shift(votes) < int(p["entry_votes"]))
        exit_signal = votes <= int(p["exit_votes"])
        score = votes / 5.0

    else:
        raise KeyError(f"unknown indicator template: {template}")

    entry = np.asarray(entry, dtype=bool) & np.isfinite(close)
    exit_signal = np.asarray(exit_signal, dtype=bool) & np.isfinite(close)
    return trades_from_signals(
        frame,
        entry,
        exit_signal,
        score=np.asarray(score, dtype=float),
        max_hold=max_hold,
        force_close_end=True,
    )


def evaluate_indicator_hypothesis(
    hypothesis: IndicatorHypothesis,
    frames: Mapping[str, pd.DataFrame],
    caches: Mapping[str, FeatureCache],
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for symbol, frame in frames.items():
        trades = build_indicator_trades(hypothesis, frame, caches[symbol])
        if len(trades) == 0:
            continue
        part = pd.DataFrame(
            {
                "hypothesis_id": hypothesis.hypothesis_id,
                "strategy": hypothesis.template,
                "family": hypothesis.family,
                "symbol": symbol,
                "entry_time": pd.to_datetime(trades.entry_dates, utc=True),
                "exit_time": pd.to_datetime(trades.exit_dates, utc=True),
                "gross_return": np.asarray(trades.gross_returns, dtype=float),
                "score": np.asarray(trades.scores, dtype=float),
                "duration_bars": np.asarray(trades.durations, dtype=int),
                "forced": np.asarray(trades.forced, dtype=bool),
            }
        )
        part = part.loc[np.isfinite(part["gross_return"])].copy()
        if not part.empty:
            rows.append(part)
    if not rows:
        return pd.DataFrame(
            columns=["hypothesis_id", "strategy", "family", "symbol", "entry_time", "exit_time", "gross_return", "score", "duration_bars", "forced"]
        )
    return pd.concat(rows, ignore_index=True).sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def promotion_status(
    *,
    evaluated_folds: int,
    selection_frequency: float,
    positive_ratio: float,
    stress_positive_ratio: float,
    median_expectancy_bps: float,
    worst_expectancy_bps: float,
    median_stress_bps: float,
    median_profit_factor: float,
) -> str:
    strong = (
        evaluated_folds >= 3
        and selection_frequency >= 0.75
        and positive_ratio == 1.0
        and stress_positive_ratio == 1.0
        and median_expectancy_bps > 0
        and worst_expectancy_bps > 0
        and median_stress_bps > 0
        and median_profit_factor >= 1.25
    )
    provisional = (
        evaluated_folds >= 2
        and selection_frequency >= 0.50
        and positive_ratio == 1.0
        and stress_positive_ratio == 1.0
        and median_expectancy_bps > 0
        and worst_expectancy_bps > 0
        and median_stress_bps > 0
        and median_profit_factor > 1.10
    )
    survivor = (
        evaluated_folds >= 3
        and selection_frequency >= 0.75
        and positive_ratio >= 0.75
        and stress_positive_ratio >= 0.75
        and median_expectancy_bps > 0
        and median_stress_bps > 0
        and median_profit_factor > 1.10
    )
    if strong:
        return "STRONG_SURVIVOR"
    if provisional:
        return "PROVISIONAL_SURVIVOR"
    if survivor:
        return "SURVIVOR"
    return "REJECT"


def validation_route(execution_contract: str) -> str:
    if execution_contract == "NEXT_OPEN_REPLAY":
        return "PYBROKER_CROSS_ENGINE_REQUIRED"
    return "EXECUTION_CHRONOLOGY_VALIDATION_REQUIRED"
