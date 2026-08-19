from __future__ import annotations

import json
import math
import runpy
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from stocks.intelligence_agent.strategy_combo_research_lab import FeatureCache
from stocks.research.candidate_strategy_matrix import _evaluate
from stocks.research.dynamic_universe_generalization import _hypothesis_trades
from stocks.research.strategy_generation_v2_22 import (
    GeneratedStrategyHypothesis,
    aroon,
    blueprint_registry,
    build_cross_engine_scope_config,
    build_diversified_validation_queue,
    build_generated_trades,
    chaikin_money_flow,
    cross_sectional_trade_metrics,
    efficiency_ratio,
    generate_strategy_hypotheses,
    promotion_blockers,
    promotion_status,
    range_quantile,
    robust_selection_score,
)


def _frame(rows: int = 900, symbol: str = "TEST") -> pd.DataFrame:
    rng = np.random.default_rng(20260818)
    regime = np.where(
        np.arange(rows) % 180 < 120,
        0.00065,
        -0.00020,
    )
    returns = regime + rng.normal(0.0, 0.0075, rows)
    close = 100.0 * np.cumprod(1.0 + returns)
    gap = rng.normal(0.0, 0.004, rows)
    gap[np.arange(rows) % 97 == 0] = -0.025
    open_ = np.r_[close[0], close[:-1]] * (1.0 + gap)
    high = np.maximum(open_, close) * (1.0 + rng.uniform(0.001, 0.012, rows))
    low = np.minimum(open_, close) * (1.0 - rng.uniform(0.001, 0.012, rows))
    volume = rng.integers(100_000, 2_000_000, rows).astype(float)
    volume[np.arange(rows) % 61 == 0] *= 3.0
    return pd.DataFrame(
        {
            "symbol": symbol,
            "date": pd.date_range("2020-01-01", periods=rows, freq="h", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def test_registry_expands_beyond_rsi_and_obv() -> None:
    blueprints = blueprint_registry()
    assert len(blueprints) >= 9
    assert len({item.name for item in blueprints}) == len(blueprints)
    assert len({item.family for item in blueprints}) == len(blueprints)
    assert not any(
        item.name.lower().startswith(("rsi_", "obv_")) for item in blueprints
    )
    expected = {
        "multi_horizon_momentum",
        "volatility_breakout",
        "adaptive_trend",
        "money_flow_confirmation",
        "volatility_normalized_pullback",
        "range_contraction",
        "opening_gap_recovery",
        "trend_persistence",
        "market_structure_retest",
    }
    assert {item.family for item in blueprints} == expected


def test_generation_is_deterministic_bounded_and_non_authoritative() -> None:
    left = generate_strategy_hypotheses(
        max_variants_per_blueprint=11,
        seed=42,
    )
    right = generate_strategy_hypotheses(
        max_variants_per_blueprint=11,
        seed=42,
    )
    assert [item.hypothesis_id for item in left] == [
        item.hypothesis_id for item in right
    ]
    assert len(left) <= len(blueprint_registry()) * 11
    assert len({item.hypothesis_id for item in left}) == len(left)
    assert all(item.execution_contract == "NEXT_OPEN_REPLAY" for item in left)
    assert all(item.execution_authority == "NONE" for item in left)
    defaults_only = generate_strategy_hypotheses(
        max_variants_per_blueprint=1,
        seed=42,
    )
    assert len(defaults_only) == len(blueprint_registry())


def test_generated_features_are_prefix_causal() -> None:
    full_frame = _frame(900)
    prefix_frame = full_frame.iloc[:650].copy()
    full = FeatureCache(full_frame)
    prefix = FeatureCache(prefix_frame)

    checks = [
        (efficiency_ratio(full, 20)[:650], efficiency_ratio(prefix, 20)),
        (chaikin_money_flow(full, 20)[:650], chaikin_money_flow(prefix, 20)),
        (range_quantile(full, 20, 0.25)[:650], range_quantile(prefix, 20, 0.25)),
    ]
    full_up, full_down = aroon(full, 25)
    prefix_up, prefix_down = aroon(prefix, 25)
    checks.extend(
        [
            (full_up[:650], prefix_up),
            (full_down[:650], prefix_down),
        ]
    )
    for actual, expected in checks:
        np.testing.assert_allclose(actual, expected, equal_nan=True)


def test_every_default_blueprint_executes_with_next_open_contract() -> None:
    frame = _frame()
    cache = FeatureCache(frame)
    for blueprint in blueprint_registry():
        hypothesis = GeneratedStrategyHypothesis(
            hypothesis_id=f"TEST-{blueprint.name}",
            strategy=blueprint.name,
            family=blueprint.family,
            rationale=blueprint.rationale,
            params=dict(blueprint.default_params),
            complexity=len(blueprint.default_params),
        )
        trades = build_generated_trades(hypothesis, frame, cache)
        assert trades is not None
        assert hypothesis.execution_authority == "NONE"
        if len(trades):
            assert np.all(trades.exit_dates >= trades.entry_dates)
            assert np.all(np.isfinite(trades.gross_returns))
            assert np.all(trades.durations >= 0)


def test_selection_score_penalizes_concentration_forcing_and_complexity() -> None:
    base = robust_selection_score(
        train_expectancy_bps=20.0,
        valid_expectancy_bps=15.0,
        stress_expectancy_bps=8.0,
        train_profit_factor=1.4,
        valid_profit_factor=1.3,
        positive_symbol_ratio=0.8,
        max_symbol_trade_share=0.25,
        forced_trade_ratio=0.10,
        complexity=4,
    )
    weak = robust_selection_score(
        train_expectancy_bps=20.0,
        valid_expectancy_bps=15.0,
        stress_expectancy_bps=8.0,
        train_profit_factor=1.4,
        valid_profit_factor=1.3,
        positive_symbol_ratio=0.4,
        max_symbol_trade_share=0.70,
        forced_trade_ratio=0.60,
        complexity=9,
    )
    assert base > weak
    assert (
        robust_selection_score(
            train_expectancy_bps=math.nan,
            valid_expectancy_bps=15.0,
            stress_expectancy_bps=8.0,
            train_profit_factor=1.4,
            valid_profit_factor=1.3,
            positive_symbol_ratio=0.8,
            max_symbol_trade_share=0.25,
            forced_trade_ratio=0.10,
            complexity=4,
        )
        == -math.inf
    )


def test_promotion_requires_breadth_and_low_concentration() -> None:
    kwargs = {
        "evaluated_folds": 4,
        "selection_frequency": 1.0,
        "positive_fold_ratio": 1.0,
        "stress_positive_fold_ratio": 1.0,
        "median_expectancy_bps": 20.0,
        "worst_expectancy_bps": 5.0,
        "median_stress_expectancy_bps": 10.0,
        "median_profit_factor": 1.5,
        "median_positive_symbol_ratio": 0.75,
        "maximum_symbol_trade_share": 0.35,
        "maximum_forced_trade_ratio": 0.20,
    }
    assert promotion_status(**kwargs) == "DIVERSE_STRONG_SURVIVOR"
    assert (
        promotion_status(
            **{
                **kwargs,
                "median_positive_symbol_ratio": 0.40,
                "maximum_symbol_trade_share": 0.70,
            }
        )
        == "REJECT"
    )


def test_ordinary_survivor_allows_one_negative_fold() -> None:
    kwargs = {
        "evaluated_folds": 3,
        "selection_frequency": 0.75,
        "positive_fold_ratio": 2.0 / 3.0,
        "stress_positive_fold_ratio": 2.0 / 3.0,
        "median_expectancy_bps": 83.75,
        "worst_expectancy_bps": -34.94,
        "median_stress_expectancy_bps": 69.65,
        "median_profit_factor": 1.86,
        "median_positive_symbol_ratio": 0.77,
        "maximum_symbol_trade_share": 0.18,
        "maximum_forced_trade_ratio": 0.09,
    }
    assert promotion_blockers(**kwargs) == ()
    assert promotion_status(**kwargs) == "DIVERSE_SURVIVOR"


def test_ordinary_survivor_rejects_two_negative_folds() -> None:
    kwargs = {
        "evaluated_folds": 4,
        "selection_frequency": 1.0,
        "positive_fold_ratio": 0.50,
        "stress_positive_fold_ratio": 0.50,
        "median_expectancy_bps": 20.0,
        "worst_expectancy_bps": -10.0,
        "median_stress_expectancy_bps": 10.0,
        "median_profit_factor": 1.4,
        "median_positive_symbol_ratio": 0.75,
        "maximum_symbol_trade_share": 0.20,
        "maximum_forced_trade_ratio": 0.10,
    }
    blockers = promotion_blockers(**kwargs)
    assert "MORE_THAN_ONE_NEGATIVE_TEST_FOLD" in blockers
    assert "MORE_THAN_ONE_NEGATIVE_STRESS_FOLD" in blockers
    assert promotion_status(**kwargs) == "REJECT"


def _trade_rows(
    hypothesis_id: str,
    *,
    offset: int,
    returns: list[float],
) -> list[dict]:
    rows = []
    for index, gross_return in enumerate(returns):
        entry = pd.Timestamp("2024-01-01", tz="UTC") + pd.Timedelta(
            days=offset + index * 2
        )
        rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "strategy": hypothesis_id,
                "family": hypothesis_id,
                "symbol": "AAPL" if index % 2 == 0 else "MSFT",
                "entry_time": entry,
                "exit_time": entry + pd.Timedelta(hours=4),
                "gross_return": gross_return,
                "duration_bars": 4,
                "forced": False,
            }
        )
    return rows


def test_validation_queue_removes_redundant_hypotheses() -> None:
    survivors = pd.DataFrame(
        [
            {
                "hypothesis_id": "A",
                "strategy": "a",
                "family": "family_a",
                "robustness_score": 50.0,
                "median_test_expectancy_bps": 20.0,
            },
            {
                "hypothesis_id": "B",
                "strategy": "b",
                "family": "family_b",
                "robustness_score": 40.0,
                "median_test_expectancy_bps": 18.0,
            },
            {
                "hypothesis_id": "C",
                "strategy": "c",
                "family": "family_c",
                "robustness_score": 30.0,
                "median_test_expectancy_bps": 15.0,
            },
        ]
    )
    returns = [0.01, -0.004, 0.008, 0.012, -0.002, 0.009]
    trades = pd.DataFrame(
        _trade_rows("A", offset=0, returns=returns)
        + _trade_rows("B", offset=0, returns=returns)
        + _trade_rows("C", offset=1, returns=list(reversed(returns)))
    )
    queue, redundancy = build_diversified_validation_queue(
        survivors,
        trades,
        maximum_total=3,
        maximum_per_family=1,
        entry_jaccard_limit=0.50,
        pnl_correlation_limit=0.80,
    )
    assert "A" in set(queue["hypothesis_id"])
    assert "B" not in set(queue["hypothesis_id"])
    assert queue["family"].nunique() == len(queue)
    assert not redundancy.empty
    decisions = redundancy.attrs["queue_decisions"]
    b = decisions.loc[decisions["hypothesis_id"] == "B"].iloc[0]
    assert str(b["decision"]).startswith("REDUNDANT_WITH:A")
    assert set(queue["execution_authority"]) == {"NONE"}


def test_cross_sectional_metrics_expose_symbol_concentration() -> None:
    rows = _trade_rows("A", offset=0, returns=[0.01] * 6)
    trades = pd.DataFrame(rows)
    trades.loc[1:, "symbol"] = "AAPL"
    period = ["2024-01-01 00:00:00+00:00", "2024-02-01 00:00:00+00:00"]
    metrics = cross_sectional_trade_metrics(
        trades,
        period,
        cost_bps_per_side=3.0,
    )
    assert metrics["traded_symbols"] == 1
    assert metrics["max_symbol_trade_share"] == 1.0
    assert metrics["positive_symbol_ratio"] == 1.0


def test_cross_engine_scope_is_frozen_from_queue() -> None:
    base = {
        "scope": {
            "strategies": [{"hypothesis_id": "OLD", "strategy": "old"}],
            "primary_timeframe": "1h",
        },
        "promotion": {
            "automatic_live_promotion": True,
            "execution_authority": "LIVE",
        },
    }
    queue = pd.DataFrame(
        [
            {
                "queue_rank": 2,
                "hypothesis_id": "B",
                "strategy": "strategy_b",
                "execution_contract": "NEXT_OPEN_REPLAY",
                "queue_status": "CROSS_ENGINE_VALIDATION_QUEUE",
            },
            {
                "queue_rank": 1,
                "hypothesis_id": "A",
                "strategy": "strategy_a",
                "execution_contract": "NEXT_OPEN_REPLAY",
                "queue_status": "CROSS_ENGINE_VALIDATION_QUEUE",
            },
        ]
    )
    result = build_cross_engine_scope_config(base, queue)
    assert [item["hypothesis_id"] for item in result["scope"]["strategies"]] == [
        "A",
        "B",
    ]
    assert result["scope"]["scope_frozen"] is True
    assert len(result["scope"]["scope_hash"]) == 64
    assert result["promotion"]["automatic_live_promotion"] is False
    assert result["promotion"]["execution_authority"] == "NONE"
    assert base["promotion"]["execution_authority"] == "LIVE"


def test_dynamic_universe_dispatches_generated_hypothesis() -> None:
    hypothesis = generate_strategy_hypotheses(
        enabled_strategies={"dual_horizon_momentum"},
        max_variants_per_blueprint=1,
        seed=42,
    )[0]
    row = {
        "hypothesis_id": hypothesis.hypothesis_id,
        "strategy": hypothesis.strategy,
        "family": hypothesis.family,
        "rationale": hypothesis.rationale,
        "complexity": hypothesis.complexity,
        "source_engine": "strategy_generation_v2_22",
        "params_json": json.dumps(hypothesis.params),
    }
    trades = _hypothesis_trades(row, {"TEST": _frame()})
    assert isinstance(trades, pd.DataFrame)
    assert {
        "hypothesis_id",
        "strategy",
        "family",
        "symbol",
        "entry_time",
        "exit_time",
        "gross_return",
    }.issubset(trades.columns)
    if not trades.empty:
        assert set(trades["hypothesis_id"]) == {hypothesis.hypothesis_id}


def test_candidate_matrix_dispatches_generated_hypothesis() -> None:
    hypothesis = generate_strategy_hypotheses(
        enabled_strategies={"keltner_volume_breakout"},
        max_variants_per_blueprint=1,
        seed=42,
    )[0]
    row = {
        "hypothesis_id": hypothesis.hypothesis_id,
        "strategy": hypothesis.strategy,
        "family": hypothesis.family,
        "rationale": hypothesis.rationale,
        "complexity": hypothesis.complexity,
        "source_engine": "strategy_generation_v2_22",
        "params_json": json.dumps(hypothesis.params),
    }
    trades = _evaluate(row, symbol="TEST", frame=_frame())
    assert isinstance(trades, pd.DataFrame)
    assert {
        "hypothesis_id",
        "strategy",
        "family",
        "symbol",
        "entry_time",
        "exit_time",
        "gross_return",
    }.issubset(trades.columns)


def test_finalizer_orders_registry_and_validation_evidence() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts/run_strategy_research_finalization_v2_22.py").read_text(
        encoding="utf-8"
    )
    registry_pre = text.index('"REGISTRY_PRE_CROSS_ENGINE"')
    cross_engine = text.index('"CROSS_ENGINE_VALIDATION"')
    registry_post_cross = text.index('"REGISTRY_POST_CROSS_ENGINE"')
    generalization = text.index('"DYNAMIC_UNIVERSE_GENERALIZATION"')
    registry_post_generalization = text.index(
        '"REGISTRY_POST_GENERALIZATION"'
    )
    redundancy = text.index('"STRATEGY_REDUNDANCY"')
    roster = text.index('"FINAL_STRATEGY_ROSTER"')
    pipeline_audit = text.index('"GENERATED_STRATEGY_PIPELINE_AUDIT"')
    assert (
        registry_pre
        < cross_engine
        < registry_post_cross
        < generalization
        < registry_post_generalization
        < redundancy
        < roster
        < pipeline_audit
    )


def test_cross_engine_scope_builder_reports_empty_queue_cleanly(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    queue = tmp_path / "empty_queue.csv"
    pd.DataFrame(columns=["hypothesis_id", "strategy"]).to_csv(
        queue,
        index=False,
    )
    root = Path(__file__).resolve().parents[1]
    namespace = runpy.run_path(str(root / "scripts/build_cross_engine_scope_v2_22.py"))
    monkeypatch.setattr(
        sys,
        "argv",
        ["build_cross_engine_scope_v2_22.py", "--queue", str(queue)],
    )
    assert namespace["main"]() == 3
    output = capsys.readouterr().out
    assert "NO_CANDIDATE_SURVIVED" in output
    assert "Traceback" not in output
