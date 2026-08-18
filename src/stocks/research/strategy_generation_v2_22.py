from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from stocks.intelligence_agent.strategy_combo_research_lab import (
    FeatureCache,
    TradeBatch,
    trades_from_signals,
)
from stocks.research.strategy_redundancy import pairwise_redundancy

SCHEMA = "strategy_generation_v2_22"
SOURCE_ENGINE = "strategy_generation_v2_22"
PRIMARY_TIMEFRAME = "1h"
EXECUTION_CONTRACT = "NEXT_OPEN_REPLAY"


@dataclass(frozen=True)
class StrategyBlueprint:
    name: str
    family: str
    rationale: str
    default_params: dict[str, Any]
    choices: dict[str, tuple[Any, ...]]
    max_complexity: int


@dataclass(frozen=True)
class GeneratedStrategyHypothesis:
    hypothesis_id: str
    strategy: str
    family: str
    rationale: str
    params: dict[str, Any]
    complexity: int
    primary_timeframe: str = PRIMARY_TIMEFRAME
    execution_timeframe: str = PRIMARY_TIMEFRAME
    execution_contract: str = EXECUTION_CONTRACT
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


def blueprint_registry() -> tuple[StrategyBlueprint, ...]:
    """Return economically distinct, long-only 1h research blueprints."""
    return (
        StrategyBlueprint(
            name="dual_horizon_momentum",
            family="multi_horizon_momentum",
            rationale=(
                "Require aligned medium and slow momentum above a structural "
                "trend filter instead of relying on one oscillator threshold."
            ),
            default_params={
                "fast_period": 20,
                "slow_period": 63,
                "fast_min": 0.025,
                "slow_min": 0.06,
                "trend_ema": 150,
                "exit_ema": 30,
                "max_hold": 80,
            },
            choices={
                "fast_period": (10, 20, 40),
                "slow_period": (63, 84, 126),
                "fast_min": (0.01, 0.025, 0.04, 0.06),
                "slow_min": (0.03, 0.06, 0.10, 0.15),
                "trend_ema": (100, 150, 200),
                "exit_ema": (20, 30, 50),
                "max_hold": (40, 80, 120),
            },
            max_complexity=7,
        ),
        StrategyBlueprint(
            name="keltner_volume_breakout",
            family="volatility_breakout",
            rationale=(
                "Enter an ATR-normalized channel expansion only when volume "
                "confirms the move and the long-term trend is positive."
            ),
            default_params={
                "basis_period": 20,
                "atr_period": 20,
                "atr_multiple": 1.75,
                "rvol_period": 20,
                "rvol_min": 1.2,
                "trend_ema": 100,
                "max_hold": 60,
            },
            choices={
                "basis_period": (10, 20, 30, 40),
                "atr_period": (10, 14, 20, 30),
                "atr_multiple": (1.25, 1.5, 1.75, 2.0, 2.5),
                "rvol_period": (10, 20, 30),
                "rvol_min": (1.0, 1.2, 1.5, 2.0),
                "trend_ema": (50, 100, 150, 200),
                "max_hold": (35, 60, 90),
            },
            max_complexity=7,
        ),
        StrategyBlueprint(
            name="efficiency_ratio_breakout",
            family="adaptive_trend",
            rationale=(
                "Demand both a price breakout and a high Kaufman efficiency "
                "ratio so noisy directional moves are rejected."
            ),
            default_params={
                "er_period": 20,
                "er_min": 0.35,
                "breakout_lookback": 40,
                "trend_ema": 100,
                "exit_ema": 30,
                "exit_er": 0.12,
                "max_hold": 80,
            },
            choices={
                "er_period": (10, 20, 30, 40),
                "er_min": (0.20, 0.30, 0.35, 0.45, 0.55),
                "breakout_lookback": (20, 40, 63, 84),
                "trend_ema": (50, 100, 150, 200),
                "exit_ema": (20, 30, 50),
                "exit_er": (0.08, 0.12, 0.18),
                "max_hold": (40, 80, 120),
            },
            max_complexity=7,
        ),
        StrategyBlueprint(
            name="chaikin_flow_breakout",
            family="money_flow_confirmation",
            rationale=(
                "Confirm a price breakout with persistent accumulation measured "
                "from intrabar location and volume, not OBV direction alone."
            ),
            default_params={
                "cmf_period": 20,
                "cmf_min": 0.08,
                "breakout_lookback": 30,
                "trend_ema": 100,
                "exit_cmf": -0.05,
                "max_hold": 70,
            },
            choices={
                "cmf_period": (10, 20, 30, 40),
                "cmf_min": (0.03, 0.08, 0.12, 0.18),
                "breakout_lookback": (15, 20, 30, 40, 63),
                "trend_ema": (50, 100, 150, 200),
                "exit_cmf": (-0.10, -0.05, 0.0),
                "max_hold": (35, 70, 100),
            },
            max_complexity=6,
        ),
        StrategyBlueprint(
            name="atr_pullback_resume",
            family="volatility_normalized_pullback",
            rationale=(
                "Buy a quantified ATR pullback only after price reclaims the "
                "fast trend inside an established dual-EMA uptrend."
            ),
            default_params={
                "fast_ema": 20,
                "slow_ema": 100,
                "atr_period": 14,
                "pullback_atr_min": 0.35,
                "pullback_atr_max": 1.75,
                "exit_ema": 50,
                "max_hold": 50,
            },
            choices={
                "fast_ema": (10, 20, 30, 40),
                "slow_ema": (75, 100, 150, 200),
                "atr_period": (10, 14, 20),
                "pullback_atr_min": (0.15, 0.35, 0.50, 0.75),
                "pullback_atr_max": (1.0, 1.5, 1.75, 2.5),
                "exit_ema": (30, 50, 75),
                "max_hold": (25, 50, 80),
            },
            max_complexity=7,
        ),
        StrategyBlueprint(
            name="range_contraction_expansion",
            family="range_contraction",
            rationale=(
                "Require a prior volatility contraction before a range expansion "
                "breakout, reducing duplicate generic high-break signals."
            ),
            default_params={
                "contraction_lookback": 20,
                "contraction_quantile": 0.25,
                "breakout_lookback": 20,
                "trend_ema": 100,
                "exit_ema": 20,
                "max_hold": 60,
            },
            choices={
                "contraction_lookback": (10, 20, 30, 40),
                "contraction_quantile": (0.15, 0.25, 0.35),
                "breakout_lookback": (10, 20, 40, 63),
                "trend_ema": (50, 100, 150, 200),
                "exit_ema": (10, 20, 30, 50),
                "max_hold": (30, 60, 90),
            },
            max_complexity=6,
        ),
        StrategyBlueprint(
            name="gap_recovery_trend",
            family="opening_gap_recovery",
            rationale=(
                "Use the open-to-prior-close gap as a separate information source "
                "and require same-bar recovery inside a positive trend."
            ),
            default_params={
                "gap_down_min": 0.0125,
                "recovery_min": 0.55,
                "trend_ema": 150,
                "exit_ema": 20,
                "max_hold": 30,
            },
            choices={
                "gap_down_min": (0.005, 0.01, 0.0125, 0.02, 0.03),
                "recovery_min": (0.35, 0.55, 0.75, 1.0),
                "trend_ema": (100, 150, 200),
                "exit_ema": (10, 20, 30, 50),
                "max_hold": (10, 20, 30, 50),
            },
            max_complexity=5,
        ),
        StrategyBlueprint(
            name="aroon_persistence",
            family="trend_persistence",
            rationale=(
                "Measure how recently highs and lows occurred, which captures "
                "trend persistence without reusing RSI or OBV."
            ),
            default_params={
                "period": 25,
                "up_min": 80.0,
                "down_max": 35.0,
                "trend_ema": 100,
                "exit_down": 70.0,
                "max_hold": 70,
            },
            choices={
                "period": (14, 20, 25, 40, 63),
                "up_min": (70.0, 80.0, 90.0, 100.0),
                "down_max": (20.0, 35.0, 50.0),
                "trend_ema": (50, 100, 150, 200),
                "exit_down": (60.0, 70.0, 80.0),
                "max_hold": (35, 70, 100),
            },
            max_complexity=6,
        ),
        StrategyBlueprint(
            name="breakout_retest_volume",
            family="market_structure_retest",
            rationale=(
                "Wait for a confirmed breakout and a later retest of the frozen "
                "breakout level instead of chasing the first expansion bar."
            ),
            default_params={
                "lookback": 30,
                "retest_window": 8,
                "tolerance_atr": 0.35,
                "atr_period": 14,
                "rvol_period": 20,
                "rvol_min": 0.9,
                "max_hold": 80,
            },
            choices={
                "lookback": (20, 30, 40, 63),
                "retest_window": (3, 5, 8, 12),
                "tolerance_atr": (0.15, 0.35, 0.50, 0.75),
                "atr_period": (10, 14, 20),
                "rvol_period": (10, 20, 30),
                "rvol_min": (0.8, 0.9, 1.0, 1.2),
                "max_hold": (40, 80, 120),
            },
            max_complexity=7,
        ),
    )


def _stable_seed(name: str, seed: int) -> int:
    digest = hashlib.sha256(f"{SCHEMA}|{seed}|{name}".encode()).hexdigest()
    return int(digest[:8], 16) % 2_147_483_647


def _hypothesis_id(name: str, params: Mapping[str, Any]) -> str:
    payload = json.dumps(
        {
            "schema": SCHEMA,
            "strategy": name,
            "params": dict(params),
            "timeframe": PRIMARY_TIMEFRAME,
            "execution_contract": EXECUTION_CONTRACT,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


def _params_valid(name: str, params: Mapping[str, Any]) -> bool:
    if (
        "fast_period" in params
        and "slow_period" in params
        and int(params["fast_period"]) >= int(params["slow_period"])
    ):
        return False
    if (
        "fast_ema" in params
        and "slow_ema" in params
        and int(params["fast_ema"]) >= int(params["slow_ema"])
    ):
        return False
    if (
        "pullback_atr_min" in params
        and "pullback_atr_max" in params
        and float(params["pullback_atr_min"]) >= float(params["pullback_atr_max"])
    ):
        return False
    return not (
        name == "aroon_persistence"
        and float(params["up_min"]) <= float(params["down_max"])
    )


def _sample_variants(
    blueprint: StrategyBlueprint,
    *,
    maximum: int,
    seed: int,
) -> list[dict[str, Any]]:
    if maximum <= 0:
        raise ValueError("maximum variants must be positive")
    variants = [dict(blueprint.default_params)]
    seen = {json.dumps(variants[0], sort_keys=True, default=str)}
    if len(variants) >= maximum:
        return variants

    for key, values in blueprint.choices.items():
        for value in values:
            candidate = dict(blueprint.default_params)
            candidate[key] = value
            marker = json.dumps(candidate, sort_keys=True, default=str)
            if marker not in seen and _params_valid(blueprint.name, candidate):
                variants.append(candidate)
                seen.add(marker)
            if len(variants) >= maximum:
                return variants

    keys = tuple(blueprint.choices)
    combinations = list(itertools.product(*(blueprint.choices[key] for key in keys)))
    rng = random.Random(_stable_seed(blueprint.name, seed))
    rng.shuffle(combinations)
    for values in combinations:
        candidate = dict(zip(keys, values, strict=True))
        marker = json.dumps(candidate, sort_keys=True, default=str)
        if marker in seen or not _params_valid(blueprint.name, candidate):
            continue
        variants.append(candidate)
        seen.add(marker)
        if len(variants) >= maximum:
            break
    return variants


def generate_strategy_hypotheses(
    *,
    max_variants_per_blueprint: int,
    seed: int,
    enabled_strategies: set[str] | None = None,
) -> list[GeneratedStrategyHypothesis]:
    hypotheses: list[GeneratedStrategyHypothesis] = []
    for blueprint in blueprint_registry():
        if enabled_strategies is not None and blueprint.name not in enabled_strategies:
            continue
        for params in _sample_variants(
            blueprint,
            maximum=max_variants_per_blueprint,
            seed=seed,
        ):
            hypotheses.append(
                GeneratedStrategyHypothesis(
                    hypothesis_id=_hypothesis_id(blueprint.name, params),
                    strategy=blueprint.name,
                    family=blueprint.family,
                    rationale=blueprint.rationale,
                    params=params,
                    complexity=min(len(params), blueprint.max_complexity),
                )
            )
    identifiers = [item.hypothesis_id for item in hypotheses]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate generated hypothesis ids")
    return hypotheses


def hypotheses_frame(
    hypotheses: Sequence[GeneratedStrategyHypothesis],
) -> pd.DataFrame:
    return pd.DataFrame([item.as_record() for item in hypotheses])


def _shift(values: np.ndarray, periods: int = 1) -> np.ndarray:
    output = np.full(len(values), np.nan, dtype=float)
    if 0 < periods < len(values):
        output[periods:] = values[:-periods]
    return output


def _cross_above(left: np.ndarray, right: np.ndarray | float) -> np.ndarray:
    a = np.asarray(left, dtype=float)
    b = (
        np.full(len(a), float(right), dtype=float)
        if np.isscalar(right)
        else np.asarray(right, dtype=float)
    )
    return (a > b) & (_shift(a) <= _shift(b))


def relative_volume(cache: FeatureCache, period: int) -> np.ndarray:
    volume = pd.Series(np.nan_to_num(cache.arr("volume"), nan=0.0))
    baseline = volume.shift(1).rolling(period, min_periods=period).mean()
    return (volume / baseline.replace(0.0, np.nan)).to_numpy()


def efficiency_ratio(cache: FeatureCache, period: int) -> np.ndarray:
    close = pd.Series(cache.arr("close"))
    direction = close.diff(period).abs()
    path = close.diff().abs().rolling(period, min_periods=period).sum()
    return (direction / path.replace(0.0, np.nan)).to_numpy()


def chaikin_money_flow(cache: FeatureCache, period: int) -> np.ndarray:
    high = pd.Series(cache.arr("high"))
    low = pd.Series(cache.arr("low"))
    close = pd.Series(cache.arr("close"))
    volume = pd.Series(np.nan_to_num(cache.arr("volume"), nan=0.0))
    spread = (high - low).replace(0.0, np.nan)
    multiplier = ((close - low) - (high - close)) / spread
    flow = multiplier.fillna(0.0) * volume
    numerator = flow.rolling(period, min_periods=period).sum()
    denominator = volume.rolling(period, min_periods=period).sum()
    return (numerator / denominator.replace(0.0, np.nan)).to_numpy()


def aroon(cache: FeatureCache, period: int) -> tuple[np.ndarray, np.ndarray]:
    high = pd.Series(cache.arr("high"))
    low = pd.Series(cache.arr("low"))

    def up_value(values: np.ndarray) -> float:
        periods_since = len(values) - 1 - int(np.argmax(values))
        return 100.0 * (period - periods_since) / period

    def down_value(values: np.ndarray) -> float:
        periods_since = len(values) - 1 - int(np.argmin(values))
        return 100.0 * (period - periods_since) / period

    up = high.rolling(period, min_periods=period).apply(up_value, raw=True)
    down = low.rolling(period, min_periods=period).apply(down_value, raw=True)
    return up.to_numpy(), down.to_numpy()


def range_quantile(cache: FeatureCache, lookback: int, quantile: float) -> np.ndarray:
    true_range = pd.Series(cache.true_range())
    return (
        true_range.shift(1)
        .rolling(lookback, min_periods=lookback)
        .quantile(float(quantile))
        .to_numpy()
    )


def _breakout_retest_signal(
    cache: FeatureCache,
    *,
    lookback: int,
    retest_window: int,
    tolerance_atr: float,
    atr_period: int,
) -> tuple[np.ndarray, np.ndarray]:
    close = cache.arr("close")
    low = cache.arr("low")
    level = cache.rolling_max("high", lookback, shift=1)
    atr = cache.atr(atr_period)
    breakout = close > level
    active_level = np.full(len(close), np.nan, dtype=float)
    age = retest_window + 1
    frozen_level = math.nan
    for index in range(len(close)):
        if bool(breakout[index]) and math.isfinite(float(level[index])):
            frozen_level = float(level[index])
            age = 0
        elif age <= retest_window:
            age += 1
        if 1 <= age <= retest_window:
            active_level[index] = frozen_level
    tolerance = np.asarray(atr, dtype=float) * float(tolerance_atr)
    retest = (
        np.isfinite(active_level)
        & (low <= active_level + tolerance)
        & (close >= active_level)
    )
    return retest, active_level


def build_generated_trades(
    hypothesis: GeneratedStrategyHypothesis,
    frame: pd.DataFrame,
    cache: FeatureCache,
) -> TradeBatch:
    params = hypothesis.params
    close = cache.arr("close")
    open_ = cache.arr("open")
    high = cache.arr("high")
    low = cache.arr("low")
    strategy = hypothesis.strategy
    entry = np.zeros(len(frame), dtype=bool)
    exit_signal = np.zeros(len(frame), dtype=bool)
    score = np.zeros(len(frame), dtype=float)

    if strategy == "dual_horizon_momentum":
        close_series = pd.Series(close)
        fast = close_series.pct_change(int(params["fast_period"])).to_numpy()
        slow = close_series.pct_change(int(params["slow_period"])).to_numpy()
        trend = cache.ema("close", int(params["trend_ema"]))
        exit_ema = cache.ema("close", int(params["exit_ema"]))
        condition = (
            (fast >= float(params["fast_min"]))
            & (slow >= float(params["slow_min"]))
            & (close > trend)
        )
        entry = condition & ~np.nan_to_num(
            _shift(condition.astype(float)), nan=0.0
        ).astype(bool)
        exit_signal = (fast <= 0.0) | (close < exit_ema)
        score = np.nan_to_num(fast + slow, nan=0.0)

    elif strategy == "keltner_volume_breakout":
        basis = cache.ema("close", int(params["basis_period"]))
        atr = cache.atr(int(params["atr_period"]))
        upper = basis + float(params["atr_multiple"]) * atr
        rvol = relative_volume(cache, int(params["rvol_period"]))
        trend = cache.ema("close", int(params["trend_ema"]))
        entry = (
            _cross_above(close, upper)
            & (rvol >= float(params["rvol_min"]))
            & (close > trend)
        )
        exit_signal = close < basis
        score = np.nan_to_num(
            (close - upper) / np.where(atr == 0, np.nan, atr), nan=0.0
        )

    elif strategy == "efficiency_ratio_breakout":
        ratio = efficiency_ratio(cache, int(params["er_period"]))
        prior_high = cache.rolling_max(
            "high", int(params["breakout_lookback"]), shift=1
        )
        trend = cache.ema("close", int(params["trend_ema"]))
        exit_ema = cache.ema("close", int(params["exit_ema"]))
        entry = (
            (close > prior_high) & (ratio >= float(params["er_min"])) & (close > trend)
        )
        exit_signal = (ratio <= float(params["exit_er"])) | (close < exit_ema)
        score = np.nan_to_num(ratio + close / prior_high - 1.0, nan=0.0)

    elif strategy == "chaikin_flow_breakout":
        flow = chaikin_money_flow(cache, int(params["cmf_period"]))
        prior_high = cache.rolling_max(
            "high", int(params["breakout_lookback"]), shift=1
        )
        trend = cache.ema("close", int(params["trend_ema"]))
        entry = (
            (close > prior_high) & (flow >= float(params["cmf_min"])) & (close > trend)
        )
        exit_signal = (flow <= float(params["exit_cmf"])) | (close < trend)
        score = np.nan_to_num(flow + close / prior_high - 1.0, nan=0.0)

    elif strategy == "atr_pullback_resume":
        fast = cache.ema("close", int(params["fast_ema"]))
        slow = cache.ema("close", int(params["slow_ema"]))
        atr = cache.atr(int(params["atr_period"]))
        previous_depth = (_shift(fast) - _shift(low)) / np.where(
            _shift(atr) == 0, np.nan, _shift(atr)
        )
        entry = (
            _cross_above(close, fast)
            & (fast > slow)
            & (previous_depth >= float(params["pullback_atr_min"]))
            & (previous_depth <= float(params["pullback_atr_max"]))
        )
        exit_ema = cache.ema("close", int(params["exit_ema"]))
        exit_signal = (fast < slow) | (close < exit_ema)
        score = np.nan_to_num(previous_depth + (fast / slow - 1.0), nan=0.0)

    elif strategy == "range_contraction_expansion":
        true_range = cache.true_range()
        threshold = range_quantile(
            cache,
            int(params["contraction_lookback"]),
            float(params["contraction_quantile"]),
        )
        prior_contracted = _shift(true_range) <= threshold
        prior_high = cache.rolling_max(
            "high", int(params["breakout_lookback"]), shift=1
        )
        trend = cache.ema("close", int(params["trend_ema"]))
        exit_ema = cache.ema("close", int(params["exit_ema"]))
        entry = prior_contracted & (close > prior_high) & (close > trend)
        exit_signal = close < exit_ema
        score = np.nan_to_num(
            (close - prior_high) / np.where(true_range == 0, np.nan, true_range),
            nan=0.0,
        )

    elif strategy == "gap_recovery_trend":
        prior_close = _shift(close)
        gap = open_ / prior_close - 1.0
        recovery = (close - open_) / np.where(
            prior_close - open_ == 0,
            np.nan,
            prior_close - open_,
        )
        trend = cache.ema("close", int(params["trend_ema"]))
        exit_ema = cache.ema("close", int(params["exit_ema"]))
        entry = (
            (gap <= -float(params["gap_down_min"]))
            & (recovery >= float(params["recovery_min"]))
            & (close > open_)
            & (close > trend)
        )
        exit_signal = close < exit_ema
        score = np.nan_to_num(-gap * np.clip(recovery, 0.0, 2.0), nan=0.0)

    elif strategy == "aroon_persistence":
        up, down = aroon(cache, int(params["period"]))
        trend = cache.ema("close", int(params["trend_ema"]))
        condition = (
            (up >= float(params["up_min"]))
            & (down <= float(params["down_max"]))
            & (close > trend)
        )
        entry = condition & ~np.nan_to_num(
            _shift(condition.astype(float)), nan=0.0
        ).astype(bool)
        exit_signal = (down >= float(params["exit_down"])) | (close < trend)
        score = np.nan_to_num((up - down) / 100.0, nan=0.0)

    elif strategy == "breakout_retest_volume":
        retest, level = _breakout_retest_signal(
            cache,
            lookback=int(params["lookback"]),
            retest_window=int(params["retest_window"]),
            tolerance_atr=float(params["tolerance_atr"]),
            atr_period=int(params["atr_period"]),
        )
        rvol = relative_volume(cache, int(params["rvol_period"]))
        entry = retest & (rvol >= float(params["rvol_min"]))
        exit_signal = close < level
        atr = cache.atr(int(params["atr_period"]))
        score = np.nan_to_num(
            (close - level) / np.where(atr == 0, np.nan, atr)
            + np.clip(rvol - 1.0, -1.0, 2.0),
            nan=0.0,
        )
    else:
        raise KeyError(f"unknown generated strategy: {strategy}")

    finite = (
        np.isfinite(close) & np.isfinite(open_) & np.isfinite(high) & np.isfinite(low)
    )
    entry = np.asarray(entry, dtype=bool) & finite
    exit_signal = np.asarray(exit_signal, dtype=bool) & finite
    return trades_from_signals(
        frame,
        entry,
        exit_signal,
        score=np.asarray(score, dtype=float),
        max_hold=int(params.get("max_hold", 80)),
        force_close_end=True,
    )


def evaluate_generated_hypothesis(
    hypothesis: GeneratedStrategyHypothesis,
    frames: Mapping[str, pd.DataFrame],
    caches: Mapping[str, FeatureCache],
) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for symbol, frame in frames.items():
        trades = build_generated_trades(hypothesis, frame, caches[symbol])
        if len(trades) == 0:
            continue
        part = pd.DataFrame(
            {
                "hypothesis_id": hypothesis.hypothesis_id,
                "strategy": hypothesis.strategy,
                "family": hypothesis.family,
                "symbol": str(symbol).upper(),
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
            parts.append(part)
    if not parts:
        return pd.DataFrame(
            columns=[
                "hypothesis_id",
                "strategy",
                "family",
                "symbol",
                "entry_time",
                "exit_time",
                "gross_return",
                "score",
                "duration_bars",
                "forced",
            ]
        )
    return (
        pd.concat(parts, ignore_index=True)
        .sort_values(["entry_time", "symbol", "exit_time"])
        .reset_index(drop=True)
    )


def contained_trades(trades: pd.DataFrame, period: Sequence[str]) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    start = pd.Timestamp(period[0])
    end = pd.Timestamp(period[1])
    start = (
        start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
    )
    end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")
    entry = pd.to_datetime(trades["entry_time"], utc=True)
    exit_time = pd.to_datetime(trades["exit_time"], utc=True)
    return trades.loc[(entry >= start) & (exit_time <= end)].copy()


def cross_sectional_trade_metrics(
    trades: pd.DataFrame,
    period: Sequence[str],
    *,
    cost_bps_per_side: float,
) -> dict[str, Any]:
    from stocks.research.strategy_factory_1h import trade_metrics

    work = contained_trades(trades, period)
    if work.empty:
        return {
            "traded_symbols": 0,
            "positive_symbol_ratio": 0.0,
            "median_symbol_expectancy_bps": math.nan,
            "worst_symbol_expectancy_bps": math.nan,
            "max_symbol_trade_share": 1.0,
            "forced_trade_ratio": 1.0,
        }
    rows = []
    for symbol, group in work.groupby("symbol"):
        metrics = trade_metrics(group, cost_bps_per_side=cost_bps_per_side)
        rows.append(
            {
                "symbol": symbol,
                "trades": int(metrics["trades"]),
                "expectancy_bps": float(metrics["net_expectancy_bps"]),
            }
        )
    symbols = pd.DataFrame(rows)
    counts = work["symbol"].value_counts()
    expectancy = symbols["expectancy_bps"].replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "traded_symbols": int(symbols["symbol"].nunique()),
        "positive_symbol_ratio": float((symbols["expectancy_bps"] > 0).mean()),
        "median_symbol_expectancy_bps": (
            float(expectancy.median()) if not expectancy.empty else math.nan
        ),
        "worst_symbol_expectancy_bps": (
            float(expectancy.min()) if not expectancy.empty else math.nan
        ),
        "max_symbol_trade_share": float(counts.max() / counts.sum()),
        "forced_trade_ratio": float(work["forced"].astype(bool).mean()),
    }


def robust_selection_score(
    *,
    train_expectancy_bps: float,
    valid_expectancy_bps: float,
    stress_expectancy_bps: float,
    train_profit_factor: float,
    valid_profit_factor: float,
    positive_symbol_ratio: float,
    max_symbol_trade_share: float,
    forced_trade_ratio: float,
    complexity: int,
) -> float:
    values = (train_expectancy_bps, valid_expectancy_bps, stress_expectancy_bps)
    if not all(math.isfinite(float(value)) for value in values):
        return -math.inf
    if not math.isfinite(train_profit_factor) or not math.isfinite(valid_profit_factor):
        return -math.inf
    worst_expectancy = min(float(value) for value in values)
    weakest_pf = min(float(train_profit_factor), float(valid_profit_factor))
    return float(
        worst_expectancy
        + 20.0 * max(-1.0, weakest_pf - 1.0)
        + 15.0 * float(positive_symbol_ratio)
        - 20.0 * float(max_symbol_trade_share)
        - 15.0 * float(forced_trade_ratio)
        - 0.75 * int(complexity)
    )


def promotion_status(
    *,
    evaluated_folds: int,
    selection_frequency: float,
    positive_fold_ratio: float,
    stress_positive_fold_ratio: float,
    median_expectancy_bps: float,
    worst_expectancy_bps: float,
    median_stress_expectancy_bps: float,
    median_profit_factor: float,
    median_positive_symbol_ratio: float,
    maximum_symbol_trade_share: float,
    maximum_forced_trade_ratio: float,
) -> str:
    common = (
        evaluated_folds >= 3
        and selection_frequency >= 0.50
        and positive_fold_ratio >= 0.75
        and stress_positive_fold_ratio >= 0.75
        and median_expectancy_bps > 0.0
        and median_stress_expectancy_bps > 0.0
        and median_profit_factor > 1.10
        and median_positive_symbol_ratio >= 0.50
        and maximum_symbol_trade_share <= 0.55
        and maximum_forced_trade_ratio <= 0.50
    )
    if not common:
        return "REJECT"
    if (
        selection_frequency >= 0.75
        and positive_fold_ratio == 1.0
        and stress_positive_fold_ratio == 1.0
        and worst_expectancy_bps > 0.0
        and median_profit_factor >= 1.25
        and median_positive_symbol_ratio >= 0.65
        and maximum_symbol_trade_share <= 0.45
        and maximum_forced_trade_ratio <= 0.35
    ):
        return "DIVERSE_STRONG_SURVIVOR"
    return "DIVERSE_SURVIVOR"


def build_diversified_validation_queue(
    survivors: pd.DataFrame,
    survivor_trades: pd.DataFrame,
    *,
    maximum_total: int,
    maximum_per_family: int,
    entry_jaccard_limit: float,
    pnl_correlation_limit: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if maximum_total <= 0 or maximum_per_family <= 0:
        raise ValueError("validation queue limits must be positive")
    if survivors.empty:
        return survivors.copy(), pairwise_redundancy(survivor_trades)
    required = {"hypothesis_id", "family", "robustness_score"}
    missing = sorted(required - set(survivors.columns))
    if missing:
        raise ValueError(f"survivors missing queue columns: {missing}")

    redundancy = pairwise_redundancy(survivor_trades)
    pair_lookup: dict[frozenset[str], tuple[float, float]] = {}
    for row in redundancy.to_dict(orient="records"):
        pair_lookup[frozenset((str(row["left"]), str(row["right"])))] = (
            float(row["entry_jaccard"]),
            float(row["realized_pnl_correlation"]),
        )

    ranked = survivors.sort_values(
        ["robustness_score", "median_test_expectancy_bps", "hypothesis_id"],
        ascending=[False, False, True],
    )
    selected: list[str] = []
    family_counts: dict[str, int] = {}
    reasons: dict[str, str] = {}
    for row in ranked.to_dict(orient="records"):
        hypothesis_id = str(row["hypothesis_id"])
        family = str(row["family"])
        if family_counts.get(family, 0) >= maximum_per_family:
            reasons[hypothesis_id] = "FAMILY_CAP"
            continue
        redundant_with = None
        for accepted in selected:
            jaccard, correlation = pair_lookup.get(
                frozenset((hypothesis_id, accepted)),
                (0.0, math.nan),
            )
            if jaccard >= entry_jaccard_limit or (
                math.isfinite(correlation) and correlation >= pnl_correlation_limit
            ):
                redundant_with = accepted
                break
        if redundant_with is not None:
            reasons[hypothesis_id] = f"REDUNDANT_WITH:{redundant_with}"
            continue
        selected.append(hypothesis_id)
        family_counts[family] = family_counts.get(family, 0) + 1
        reasons[hypothesis_id] = "SELECTED"
        if len(selected) >= maximum_total:
            break

    queue = ranked.loc[ranked["hypothesis_id"].astype(str).isin(selected)].copy()
    order = {hypothesis_id: index for index, hypothesis_id in enumerate(selected)}
    queue["queue_rank"] = queue["hypothesis_id"].astype(str).map(order).astype(int) + 1
    queue["queue_status"] = "CROSS_ENGINE_VALIDATION_QUEUE"
    queue["validation_route"] = "NATIVE_PYBROKER_NAUTILUS_LEAN_REQUIRED"
    queue["automatic_finalist_promotion"] = False
    queue["execution_authority"] = "NONE"
    queue = queue.sort_values("queue_rank").reset_index(drop=True)

    decision_rows = []
    for row in ranked.to_dict(orient="records"):
        hypothesis_id = str(row["hypothesis_id"])
        decision_rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "family": str(row["family"]),
                "decision": reasons.get(hypothesis_id, "QUEUE_FULL"),
                "selected": hypothesis_id in selected,
            }
        )
    decisions = pd.DataFrame(decision_rows)
    if redundancy.empty:
        redundancy = pd.DataFrame(
            columns=[
                "left",
                "right",
                "entry_jaccard",
                "realized_pnl_correlation",
                "redundancy_flag",
            ]
        )
    redundancy.attrs["queue_decisions"] = decisions
    return queue, redundancy


def build_cross_engine_scope_config(
    base_config: Mapping[str, Any],
    validation_queue: pd.DataFrame,
) -> dict[str, Any]:
    """Freeze a strict cross-engine scope from the diversified queue."""
    if validation_queue.empty:
        raise ValueError("v2.22 validation queue is empty")
    required = {
        "hypothesis_id",
        "strategy",
        "execution_contract",
        "queue_status",
        "queue_rank",
    }
    missing = sorted(required - set(validation_queue.columns))
    if missing:
        raise ValueError(f"validation queue missing scope columns: {missing}")
    if validation_queue["hypothesis_id"].astype(str).duplicated().any():
        raise ValueError("validation queue contains duplicate hypothesis ids")
    if set(validation_queue["execution_contract"].astype(str)) != {EXECUTION_CONTRACT}:
        raise ValueError("validation queue contains unsupported execution contract")
    if set(validation_queue["queue_status"].astype(str)) != {
        "CROSS_ENGINE_VALIDATION_QUEUE"
    }:
        raise ValueError("validation queue contains invalid queue status")

    config = deepcopy(dict(base_config))
    if "scope" not in config or "promotion" not in config:
        raise ValueError("base cross-engine config is incomplete")
    ranked = validation_queue.sort_values(
        ["queue_rank", "hypothesis_id"],
        ascending=[True, True],
    )
    config["scope"]["strategies"] = [
        {
            "hypothesis_id": str(row["hypothesis_id"]),
            "strategy": str(row["strategy"]),
        }
        for row in ranked.to_dict(orient="records")
    ]
    config["scope"]["source_queue"] = "strategy_generation_v2_22/validation_queue.csv"
    config["scope"]["scope_frozen"] = True
    config["scope"]["scope_hash"] = hashlib.sha256(
        json.dumps(
            config["scope"]["strategies"],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    config["promotion"]["automatic_live_promotion"] = False
    config["promotion"]["execution_authority"] = "NONE"
    return config
