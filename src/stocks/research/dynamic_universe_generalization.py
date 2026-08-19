from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from stocks.research.validation_policy import classify_generalization

ONE_HOUR_DIRS = (
    "data/canonical/provider_fabric",
    "data/adjusted",
    "data/derived",
    "data/processed",
)
FIFTEEN_MINUTE_DIRS = ONE_HOUR_DIRS


def discover_interval_sources(project_root: Path, interval: str) -> dict[str, Path]:
    result: dict[str, Path] = {}
    suffix = f"_{interval}.parquet"
    for relative in ONE_HOUR_DIRS:
        directory = project_root / relative
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob(f"*{suffix}")):
            symbol = path.name[: -len(suffix)].upper()
            result.setdefault(symbol, path)
    return result


def contextual_symbols(project_root: Path) -> set[str]:
    candidates = (
        project_root / "artifacts/research_runtime/contextual_discovery/candidates.csv",
        project_root / "artifacts/research_runtime/discovery_screener/candidates.csv",
    )
    for path in candidates:
        if not path.is_file():
            continue
        try:
            frame = pd.read_csv(path)
        except Exception:
            continue
        if "symbol" in frame.columns and not frame.empty:
            return set(frame["symbol"].dropna().astype(str).str.upper())
    return set()


def configured_holdout_symbols(project_root: Path) -> set[str]:
    path = project_root / "config/generalization_holdout_v1.json"
    if not path.is_file():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not payload.get("frozen"):
        raise ValueError("generalization holdout is not frozen")
    return {
        str(value).strip().upper()
        for value in payload.get("symbols", [])
        if str(value).strip()
    }


def build_universe_plan(
    project_root: Path,
    *,
    development_symbols: set[str],
    holdout_symbols: set[str] | None = None,
) -> pd.DataFrame:
    one_hour = discover_interval_sources(project_root, "1h")
    fifteen = discover_interval_sources(project_root, "15m")
    context = contextual_symbols(project_root)
    holdout = (
        configured_holdout_symbols(project_root)
        if holdout_symbols is None
        else {str(x).upper() for x in holdout_symbols}
    )
    symbols = sorted(set(one_hour) | set(fifteen) | context | holdout)
    rows = []
    for symbol in symbols:
        rows.append({
            "symbol": symbol,
            "development_symbol": symbol in development_symbols,
            "generalization_holdout": symbol in holdout,
            "contextual_candidate": symbol in context,
            "has_1h": symbol in one_hour,
            "has_15m": symbol in fifteen,
            "one_hour_path": str(one_hour[symbol]) if symbol in one_hour else None,
            "fifteen_minute_path": str(fifteen[symbol]) if symbol in fifteen else None,
            "eligible_unseen_1h": (
                symbol not in development_symbols
                and symbol in one_hour
                and (not holdout or symbol in holdout)
            ),
            "eligible_unseen_15m": (
                symbol not in development_symbols
                and symbol in fifteen
                and (not holdout or symbol in holdout)
            ),
        })
    return pd.DataFrame(rows)


def load_one_hour_frames(
    project_root: Path,
    symbols: list[str],
    *,
    min_rows: int = 4000,
) -> dict[str, pd.DataFrame]:
    from stocks.research.strategy_factory_1h import prepare_one_hour_frame
    sources = discover_interval_sources(project_root, "1h")
    frames: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        path = sources.get(symbol)
        if path is None:
            continue
        raw = pd.read_parquet(path)
        frame = prepare_one_hour_frame(raw, symbol)
        if len(frame) >= int(min_rows):
            frames[symbol] = frame
    return frames


def walkforward_readiness(
    frames: Mapping[str, pd.DataFrame],
    *,
    min_symbols: int,
    min_rows: int = 4000,
) -> dict[str, Any]:
    anchor_rows = max((len(frame) for frame in frames.values()), default=0)
    if len(frames) < int(min_symbols):
        return {
            "ready": False,
            "reason": "INSUFFICIENT_UNSEEN_SYMBOLS",
            "symbol_count": int(len(frames)),
            "anchor_rows": int(anchor_rows),
        }
    if anchor_rows < int(min_rows):
        return {
            "ready": False,
            "reason": "INSUFFICIENT_ANCHOR_HISTORY",
            "symbol_count": int(len(frames)),
            "anchor_rows": int(anchor_rows),
        }
    return {
        "ready": True,
        "reason": None,
        "symbol_count": int(len(frames)),
        "anchor_rows": int(anchor_rows),
    }


def _hypothesis_trades(
    row: Mapping[str, Any],
    frames: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    source_engine = str(row.get("source_engine") or "")
    params_raw = row.get("params_json", "{}")
    params = params_raw if isinstance(params_raw, dict) else json.loads(str(params_raw))
    if source_engine == "indicator_discovery_v1":
        from stocks.intelligence_agent.strategy_combo_research_lab import FeatureCache
        from stocks.research.indicator_crosscheck import hypothesis_from_survivor_row
        from stocks.research.indicator_discovery import evaluate_indicator_hypothesis
        hypothesis = hypothesis_from_survivor_row(row)
        caches = {symbol: FeatureCache(frame) for symbol, frame in frames.items()}
        return evaluate_indicator_hypothesis(hypothesis, frames, caches)
    if source_engine == "strategy_generation_v2_22":
        from stocks.intelligence_agent.strategy_combo_research_lab import FeatureCache
        from stocks.research.strategy_generation_v2_22 import (
            GeneratedStrategyHypothesis,
            evaluate_generated_hypothesis,
        )

        hypothesis = GeneratedStrategyHypothesis(
            hypothesis_id=str(row["hypothesis_id"]),
            strategy=str(row["strategy"]),
            family=str(row["family"]),
            rationale=str(row.get("rationale") or ""),
            params=dict(params),
            complexity=int(row.get("complexity") or len(params)),
        )
        caches = {symbol: FeatureCache(frame) for symbol, frame in frames.items()}
        return evaluate_generated_hypothesis(hypothesis, frames, caches)
    from stocks.research.strategy_factory_1h import (
        OneHourHypothesis,
        build_feature_caches,
        eligible_1h_specs,
        evaluate_hypothesis,
    )
    strategy = str(row["strategy"])
    specs = {spec.name: spec for spec in eligible_1h_specs()}
    if strategy not in specs:
        raise KeyError(f"strategy not present in eligible_1h_specs: {strategy}")
    hypothesis = OneHourHypothesis(
        hypothesis_id=str(row["hypothesis_id"]),
        strategy=strategy,
        family=str(row["family"]),
        horizon="DYNAMIC_UNIVERSE_GENERALIZATION",
        params=dict(params),
    )
    caches = build_feature_caches(frames)
    return evaluate_hypothesis(hypothesis, specs[strategy], frames, caches)


def evaluate_generalization(
    row: Mapping[str, Any],
    frames: Mapping[str, pd.DataFrame],
    *,
    policy: Mapping[str, Any],
    folds: list[dict[str, tuple[pd.Timestamp, pd.Timestamp]]],
    base_cost_bps_per_side: float,
    stress_cost_bps_per_side: float,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    from stocks.research.strategy_factory_1h import contained_trades, trade_metrics
    trades = _hypothesis_trades(row, frames)
    fold_rows: list[dict[str, Any]] = []
    oos_parts: list[pd.DataFrame] = []
    for fold_number, periods in enumerate(folds, start=1):
        test = contained_trades(trades, periods["test"])
        base = trade_metrics(test, cost_bps_per_side=float(base_cost_bps_per_side))
        stress = trade_metrics(test, cost_bps_per_side=float(stress_cost_bps_per_side))
        if not test.empty:
            oos_parts.append(test.assign(fold=fold_number))
        fold_rows.append({
            "hypothesis_id": str(row["hypothesis_id"]),
            "strategy": str(row["strategy"]),
            "fold": fold_number,
            "trades": int(base["trades"]),
            "base_expectancy_bps": float(base["net_expectancy_bps"]),
            "base_profit_factor": float(base["profit_factor"]),
            "stress_expectancy_bps": float(stress["net_expectancy_bps"]),
            "stress_profit_factor": float(stress["profit_factor"]),
        })
    oos = pd.concat(oos_parts, ignore_index=True) if oos_parts else trades.iloc[0:0].copy()
    symbol_rows: list[dict[str, Any]] = []
    groups = oos.groupby("symbol") if not oos.empty else []
    for symbol, group in groups:
        base = trade_metrics(group, cost_bps_per_side=float(base_cost_bps_per_side))
        stress = trade_metrics(group, cost_bps_per_side=float(stress_cost_bps_per_side))
        symbol_rows.append({
            "hypothesis_id": str(row["hypothesis_id"]),
            "strategy": str(row["strategy"]),
            "symbol": str(symbol),
            "trades": int(base["trades"]),
            "base_expectancy_bps": float(base["net_expectancy_bps"]),
            "base_profit_factor": float(base["profit_factor"]),
            "stress_expectancy_bps": float(stress["net_expectancy_bps"]),
            "stress_profit_factor": float(stress["profit_factor"]),
        })
    fold_frame = pd.DataFrame(fold_rows)
    symbol_frame = pd.DataFrame(symbol_rows)
    usable_folds = fold_frame.loc[fold_frame["trades"] > 0] if not fold_frame.empty else fold_frame
    positive_fold_ratio = float((usable_folds["base_expectancy_bps"] > 0).mean()) if not usable_folds.empty else 0.0
    stress_positive_fold_ratio = float((usable_folds["stress_expectancy_bps"] > 0).mean()) if not usable_folds.empty else 0.0
    positive_symbol_ratio = float((symbol_frame["base_expectancy_bps"] > 0).mean()) if not symbol_frame.empty else 0.0
    stress_positive_symbol_ratio = float((symbol_frame["stress_expectancy_bps"] > 0).mean()) if not symbol_frame.empty else 0.0
    counts = oos["symbol"].value_counts() if not oos.empty else pd.Series(dtype=float)
    max_share = float(counts.max() / counts.sum()) if not counts.empty else 1.0
    base_values = usable_folds["base_expectancy_bps"].replace([np.inf, -np.inf], np.nan).dropna() if not usable_folds.empty else pd.Series(dtype=float)
    stress_values = usable_folds["stress_expectancy_bps"].replace([np.inf, -np.inf], np.nan).dropna() if not usable_folds.empty else pd.Series(dtype=float)
    median_base = float(base_values.median()) if not base_values.empty else math.nan
    median_stress = float(stress_values.median()) if not stress_values.empty else math.nan
    decision = classify_generalization(
        unseen_symbols_available=len(frames),
        unseen_symbols_traded=int(symbol_frame["symbol"].nunique()) if not symbol_frame.empty else 0,
        oos_trades=int(len(oos)),
        positive_fold_ratio=positive_fold_ratio,
        stress_positive_fold_ratio=stress_positive_fold_ratio,
        median_expectancy_bps=median_base,
        median_stress_expectancy_bps=median_stress,
        positive_symbol_ratio=positive_symbol_ratio,
        stress_positive_symbol_ratio=stress_positive_symbol_ratio,
        max_symbol_trade_share=max_share,
        policy=policy,
    )
    summary = {
        "hypothesis_id": str(row["hypothesis_id"]),
        "strategy": str(row["strategy"]),
        "family": str(row["family"]),
        "source_engine": str(row.get("source_engine") or ""),
        "unseen_symbols_available": int(len(frames)),
        "unseen_symbols_traded": int(symbol_frame["symbol"].nunique()) if not symbol_frame.empty else 0,
        "oos_trades": int(len(oos)),
        "usable_folds": int(len(usable_folds)),
        "positive_fold_ratio": positive_fold_ratio,
        "stress_positive_fold_ratio": stress_positive_fold_ratio,
        "median_expectancy_bps": median_base,
        "median_stress_expectancy_bps": median_stress,
        "positive_symbol_ratio": positive_symbol_ratio,
        "stress_positive_symbol_ratio": stress_positive_symbol_ratio,
        "max_symbol_trade_share": max_share,
        "generalization_status": decision.status,
        "generalization_passed": decision.passed,
        "generalization_evaluable": decision.evaluable,
        "generalization_reasons": "|".join(decision.reasons),
        "execution_authority": "NONE",
    }
    return summary, fold_frame, symbol_frame
