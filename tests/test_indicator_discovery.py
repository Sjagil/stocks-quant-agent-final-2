from __future__ import annotations

import numpy as np
import pandas as pd

from stocks.intelligence_agent.strategy_combo_research_lab import FeatureCache
from stocks.research.indicator_discovery import (
    IndicatorHypothesis,
    build_indicator_trades,
    cci,
    generate_indicator_hypotheses,
    mfi,
    promotion_status,
    relative_volume,
    rolling_vwap,
    stochastic_k,
    template_registry,
    validation_route,
)


def _frame(rows: int = 700) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    returns = rng.normal(0.0003, 0.01, rows)
    close = 100.0 * np.cumprod(1.0 + returns)
    open_ = close * (1.0 + rng.normal(0.0, 0.002, rows))
    high = np.maximum(open_, close) * (1.0 + rng.uniform(0.001, 0.012, rows))
    low = np.minimum(open_, close) * (1.0 - rng.uniform(0.001, 0.012, rows))
    volume = rng.integers(100_000, 2_000_000, rows)
    return pd.DataFrame(
        {
            "symbol": "TEST",
            "date": pd.date_range("2020-01-01", periods=rows, freq="h", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def test_hypothesis_generation_is_bounded_unique_and_long_only() -> None:
    items = generate_indicator_hypotheses(max_variants_per_template=7, seed=42)
    assert len(items) <= len(template_registry()) * 7
    assert len({item.hypothesis_id for item in items}) == len(items)
    assert all(item.execution_authority == "NONE" for item in items)
    assert all(item.execution_contract == "NEXT_OPEN_REPLAY" for item in items)


def test_indicator_prefix_is_causal() -> None:
    frame = _frame(700)
    prefix = frame.iloc[:500].copy()
    full = FeatureCache(frame)
    short = FeatureCache(prefix)
    checks = [
        (stochastic_k(full, 14, 3)[:500], stochastic_k(short, 14, 3)),
        (cci(full, 20)[:500], cci(short, 20)),
        (mfi(full, 14)[:500], mfi(short, 14)),
        (relative_volume(full, 20)[:500], relative_volume(short, 20)),
        (rolling_vwap(full, 20)[:500], rolling_vwap(short, 20)),
    ]
    for left, right in checks:
        np.testing.assert_allclose(left, right, equal_nan=True)


def test_all_default_templates_execute_without_authority() -> None:
    frame = _frame()
    cache = FeatureCache(frame)
    for template in template_registry():
        hypothesis = IndicatorHypothesis(
            hypothesis_id=f"TEST-{template.name}",
            template=template.name,
            family=template.family,
            params=dict(template.default_params),
        )
        trades = build_indicator_trades(hypothesis, frame, cache)
        assert trades is not None
        assert hypothesis.execution_authority == "NONE"
        if len(trades):
            assert np.all(trades.exit_dates >= trades.entry_dates)
            assert np.all(np.isfinite(trades.gross_returns))


def test_strong_survivor_requires_all_positive_test_folds() -> None:
    assert promotion_status(
        evaluated_folds=4,
        selection_frequency=1.0,
        positive_ratio=1.0,
        stress_positive_ratio=1.0,
        median_expectancy_bps=20.0,
        worst_expectancy_bps=5.0,
        median_stress_bps=10.0,
        median_profit_factor=1.5,
    ) == "STRONG_SURVIVOR"
    assert promotion_status(
        evaluated_folds=4,
        selection_frequency=1.0,
        positive_ratio=0.75,
        stress_positive_ratio=0.75,
        median_expectancy_bps=20.0,
        worst_expectancy_bps=-5.0,
        median_stress_bps=10.0,
        median_profit_factor=1.5,
    ) != "STRONG_SURVIVOR"


def test_survivors_route_to_cross_engine_not_finalist() -> None:
    assert validation_route("NEXT_OPEN_REPLAY") == "PYBROKER_CROSS_ENGINE_REQUIRED"
