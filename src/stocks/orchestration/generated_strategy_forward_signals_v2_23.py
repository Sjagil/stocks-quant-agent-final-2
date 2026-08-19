from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from stocks.intelligence_agent.strategy_combo_research_lab import FeatureCache
from stocks.research.strategy_generation_v2_22 import (
    _breakout_retest_signal,
    _cross_above,
    _shift,
    aroon,
    chaikin_money_flow,
    efficiency_ratio,
    range_quantile,
    relative_volume,
)


GENERATED_NEXT_OPEN_STRATEGIES = frozenset(
    {
        "dual_horizon_momentum",
        "keltner_volume_breakout",
        "efficiency_ratio_breakout",
        "chaikin_flow_breakout",
        "atr_pullback_resume",
        "range_contraction_expansion",
        "gap_recovery_trend",
        "aroon_persistence",
        "breakout_retest_volume",
    }
)


def _latest_bool(values: np.ndarray) -> bool:
    array = np.asarray(values, dtype=bool)
    return bool(len(array) and array[-1])


def _entry_result(strategy: str, ready: bool) -> dict[str, Any]:
    state = "TRUE" if ready else "FALSE"
    return {
        "ready": bool(ready),
        "strategy": strategy,
        "reason": f"GENERATED_{strategy.upper()}_ENTRY_CONDITION_{state}",
        "adapter_version": "v2.23",
    }


def evaluate_latest_generated_entry_condition(
    *,
    strategy: str,
    frame: pd.DataFrame,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a v2.22 generated strategy on the latest closed 1h bar.

    This mirrors only the entry side of ``build_generated_trades`` and reuses
    the same v2.22 indicator helpers. It does not create trades, positions,
    broker requests, or orders. Existing NEXT_OPEN_REPLAY and authority gates
    remain authoritative.
    """
    if strategy not in GENERATED_NEXT_OPEN_STRATEGIES:
        return {
            "ready": False,
            "strategy": strategy,
            "reason": "GENERATED_STRATEGY_FORWARD_ADAPTER_NOT_IMPLEMENTED",
            "adapter_version": "v2.23",
        }
    if frame.empty:
        return {
            "ready": False,
            "strategy": strategy,
            "reason": "EMPTY_FRAME",
            "adapter_version": "v2.23",
        }

    cache = FeatureCache(frame)
    close = cache.arr("close")
    open_ = cache.arr("open")
    high = cache.arr("high")
    low = cache.arr("low")
    entry = np.zeros(len(frame), dtype=bool)

    if strategy == "dual_horizon_momentum":
        close_series = pd.Series(close)
        fast = close_series.pct_change(int(params["fast_period"])).to_numpy()
        slow = close_series.pct_change(int(params["slow_period"])).to_numpy()
        trend = cache.ema("close", int(params["trend_ema"]))
        condition = (
            (fast >= float(params["fast_min"]))
            & (slow >= float(params["slow_min"]))
            & (close > trend)
        )
        entry = condition & ~np.nan_to_num(
            _shift(condition.astype(float)), nan=0.0
        ).astype(bool)

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

    elif strategy == "efficiency_ratio_breakout":
        ratio = efficiency_ratio(cache, int(params["er_period"]))
        prior_high = cache.rolling_max(
            "high", int(params["breakout_lookback"]), shift=1
        )
        trend = cache.ema("close", int(params["trend_ema"]))
        entry = (
            (close > prior_high)
            & (ratio >= float(params["er_min"]))
            & (close > trend)
        )

    elif strategy == "chaikin_flow_breakout":
        flow = chaikin_money_flow(cache, int(params["cmf_period"]))
        prior_high = cache.rolling_max(
            "high", int(params["breakout_lookback"]), shift=1
        )
        trend = cache.ema("close", int(params["trend_ema"]))
        entry = (
            (close > prior_high)
            & (flow >= float(params["cmf_min"]))
            & (close > trend)
        )

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
        entry = prior_contracted & (close > prior_high) & (close > trend)

    elif strategy == "gap_recovery_trend":
        prior_close = _shift(close)
        gap = open_ / prior_close - 1.0
        recovery = (close - open_) / np.where(
            prior_close - open_ == 0,
            np.nan,
            prior_close - open_,
        )
        trend = cache.ema("close", int(params["trend_ema"]))
        entry = (
            (gap <= -float(params["gap_down_min"]))
            & (recovery >= float(params["recovery_min"]))
            & (close > open_)
            & (close > trend)
        )

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

    elif strategy == "breakout_retest_volume":
        retest, _ = _breakout_retest_signal(
            cache,
            lookback=int(params["lookback"]),
            retest_window=int(params["retest_window"]),
            tolerance_atr=float(params["tolerance_atr"]),
            atr_period=int(params["atr_period"]),
        )
        rvol = relative_volume(cache, int(params["rvol_period"]))
        entry = retest & (rvol >= float(params["rvol_min"]))

    finite = (
        np.isfinite(close)
        & np.isfinite(open_)
        & np.isfinite(high)
        & np.isfinite(low)
    )
    entry = np.asarray(entry, dtype=bool) & finite
    return _entry_result(strategy, _latest_bool(entry))


__all__ = [
    "GENERATED_NEXT_OPEN_STRATEGIES",
    "evaluate_latest_generated_entry_condition",
]
