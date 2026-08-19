#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from stocks.intelligence_agent.strategy_combo_research_lab import FeatureCache
from stocks.research.canonical_trade_handoff_v2_17_8 import (
    materialize_survivor_trades,
)
from stocks.research.strategy_factory_1h import (
    period_metrics,
    prepare_one_hour_frame,
)
from stocks.research.strategy_generation_v2_22 import (
    MINIMUM_EVALUATED_FOLDS,
    ORDINARY_MAXIMUM_NEGATIVE_FOLDS,
    SCHEMA,
    blueprint_registry,
    build_diversified_validation_queue,
    cross_sectional_trade_metrics,
    evaluate_generated_hypothesis,
    generate_strategy_hypotheses,
    hypotheses_frame,
    promotion_blockers,
    promotion_status,
    robust_selection_score,
)
from stocks.research.walkforward_splits import rolling_periods

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/research_runtime/strategy_generation_v2_22"


def _source(symbol: str) -> Path:
    candidates = (
        ROOT / "data/canonical/provider_fabric" / f"{symbol}_1h.parquet",
        ROOT / "data/adjusted" / f"{symbol}_1h.parquet",
        ROOT / "data/derived" / f"{symbol}_1h.parquet",
        ROOT / "data/processed" / f"{symbol}_1h.parquet",
    )
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(f"{symbol}: 1h source missing")


def _load_frames(
    symbols: list[str],
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    frames: dict[str, pd.DataFrame] = {}
    sources: dict[str, str] = {}
    for symbol in symbols:
        path = _source(symbol)
        frame = prepare_one_hour_frame(pd.read_parquet(path), symbol)
        if len(frame) < 4000:
            raise ValueError(f"{symbol}: fewer than 4000 causal 1h bars")
        frames[symbol] = frame
        sources[symbol] = str(path)
        print(
            "SOURCE",
            symbol,
            "ROWS",
            len(frame),
            "FIRST",
            frame["date"].min(),
            "LAST",
            frame["date"].max(),
        )
    return frames, sources


def _finite_positive(value: object) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0.0


def _prefixed(prefix: str, values: dict[str, Any]) -> dict[str, Any]:
    return {f"{prefix}_{key}": value for key, value in values.items()}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_catalog(
    hypotheses: list,
    enabled: set[str],
    policy: dict,
) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    hypotheses_frame(hypotheses).to_csv(OUTPUT / "hypotheses.csv", index=False)
    blueprints = pd.DataFrame(
        [
            {
                "strategy": blueprint.name,
                "family": blueprint.family,
                "rationale": blueprint.rationale,
                "default_params_json": json.dumps(
                    blueprint.default_params,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "parameter_count": len(blueprint.choices),
                "enabled": blueprint.name in enabled,
                "execution_contract": "NEXT_OPEN_REPLAY",
                "execution_authority": "NONE",
            }
            for blueprint in blueprint_registry()
        ]
    )
    blueprints.to_csv(OUTPUT / "blueprints.csv", index=False)
    (OUTPUT / "catalog_audit.json").write_text(
        json.dumps(
            {
                "schema": "strategy_generation_catalog_v2_22",
                "blueprints": len(blueprints),
                "enabled_blueprints": len(enabled),
                "families": int(blueprints["family"].nunique()),
                "hypotheses": len(hypotheses),
                "max_variants_per_blueprint": int(
                    policy["generation"]["max_variants_per_blueprint"]
                ),
                "legacy_rsi_or_obv_blueprints": int(
                    blueprints["strategy"].str.contains("rsi|obv", case=False).sum()
                ),
                "automatic_finalist_promotion": False,
                "automatic_live_promotion": False,
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": "NONE",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(ROOT / "config/strategy_generation_v2_22.yaml"),
    )
    parser.add_argument("--symbols")
    parser.add_argument("--strategies")
    parser.add_argument("--max-variants-per-blueprint", type=int)
    parser.add_argument("--catalog-only", action="store_true")
    args = parser.parse_args()

    policy = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if policy.get("schema") != "strategy_generation_policy_v2_22":
        raise ValueError("invalid strategy generation v2.22 policy")

    symbols = [
        item.strip().upper()
        for item in (args.symbols.split(",") if args.symbols else policy["symbols"])
        if item.strip()
    ]
    enabled = {
        item.strip()
        for item in (
            args.strategies.split(",") if args.strategies else policy["strategies"]
        )
        if item.strip()
    }
    known = {blueprint.name for blueprint in blueprint_registry()}
    unknown = sorted(enabled - known)
    if unknown:
        raise ValueError(f"unknown v2.22 strategies: {unknown}")
    maximum = int(
        args.max_variants_per_blueprint
        or policy["generation"]["max_variants_per_blueprint"]
    )
    hypotheses = generate_strategy_hypotheses(
        max_variants_per_blueprint=maximum,
        seed=int(policy["generation"]["seed"]),
        enabled_strategies=enabled,
    )
    _write_catalog(hypotheses, enabled, policy)
    print(
        "STRATEGY_GENERATION_CATALOG_V2_22",
        "BLUEPRINTS",
        len(enabled),
        "FAMILIES",
        len({item.family for item in hypotheses}),
        "HYPOTHESES",
        len(hypotheses),
    )
    if args.catalog_only:
        print("CATALOG_ONLY", True)
        print("BROKER_CALLS", 0)
        print("ORDER_CALLS", 0)
        print("EXECUTION_AUTHORITY", "NONE")
        print("ARTIFACT_ROOT", OUTPUT)
        return 0

    frames, sources = _load_frames(symbols)
    anchor = "SPY" if "SPY" in frames else max(frames, key=lambda x: len(frames[x]))
    anchor_index = (
        pd.DatetimeIndex(frames[anchor]["date"]).sort_values().drop_duplicates()
    )
    folds = rolling_periods(
        anchor_index,
        hold_bars=int(policy["walk_forward"]["purge_bars"]),
        requested_folds=int(policy["walk_forward"]["folds"]),
    )
    base_cost = float(policy["costs"]["base_bps_per_side"])
    stress_cost = float(policy["costs"]["stress_bps_per_side"])
    selection_policy = policy["selection"]

    caches = {symbol: FeatureCache(frame) for symbol, frame in frames.items()}
    trade_cache: dict[str, pd.DataFrame] = {}
    failures: list[dict[str, str]] = []
    grouped: dict[str, list] = {}
    for hypothesis in hypotheses:
        grouped.setdefault(hypothesis.strategy, []).append(hypothesis)
    for strategy, items in sorted(grouped.items()):
        print("EVALUATE_GENERATED_STRATEGY", strategy, "VARIANTS", len(items))
        for hypothesis in items:
            try:
                trade_cache[hypothesis.hypothesis_id] = evaluate_generated_hypothesis(
                    hypothesis, frames, caches
                )
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    {
                        "hypothesis_id": hypothesis.hypothesis_id,
                        "strategy": strategy,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                trade_cache[hypothesis.hypothesis_id] = pd.DataFrame()

    fold_rows: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for fold_number, periods in enumerate(folds, start=1):
        current: list[dict[str, Any]] = []
        for hypothesis in hypotheses:
            trades = trade_cache[hypothesis.hypothesis_id]
            train = period_metrics(
                trades,
                periods["train"],
                cost_bps_per_side=base_cost,
            )
            valid = period_metrics(
                trades,
                periods["valid"],
                cost_bps_per_side=base_cost,
            )
            valid_stress = period_metrics(
                trades,
                periods["valid"],
                cost_bps_per_side=stress_cost,
            )
            breadth = cross_sectional_trade_metrics(
                trades,
                periods["valid"],
                cost_bps_per_side=base_cost,
            )
            gate = (
                int(train["trades"]) >= int(selection_policy["min_train_trades"])
                and int(valid["trades"]) >= int(selection_policy["min_valid_trades"])
                and _finite_positive(train["net_expectancy"])
                and _finite_positive(valid["net_expectancy"])
                and _finite_positive(valid_stress["net_expectancy"])
                and float(train["profit_factor"]) > 1.0
                and float(valid["profit_factor"]) > 1.0
                and int(breadth["traded_symbols"])
                >= int(selection_policy["min_traded_symbols"])
                and float(breadth["positive_symbol_ratio"])
                >= float(selection_policy["min_positive_symbol_ratio"])
                and float(breadth["max_symbol_trade_share"])
                <= float(selection_policy["max_symbol_trade_share"])
                and float(breadth["forced_trade_ratio"])
                <= float(selection_policy["max_forced_trade_ratio"])
            )
            selection_score = robust_selection_score(
                train_expectancy_bps=float(train["net_expectancy_bps"]),
                valid_expectancy_bps=float(valid["net_expectancy_bps"]),
                stress_expectancy_bps=float(valid_stress["net_expectancy_bps"]),
                train_profit_factor=float(train["profit_factor"]),
                valid_profit_factor=float(valid["profit_factor"]),
                positive_symbol_ratio=float(breadth["positive_symbol_ratio"]),
                max_symbol_trade_share=float(breadth["max_symbol_trade_share"]),
                forced_trade_ratio=float(breadth["forced_trade_ratio"]),
                complexity=hypothesis.complexity,
            )
            row = {
                "fold": fold_number,
                **hypothesis.as_record(),
                "gate_pass": bool(gate),
                "selection_score": selection_score,
                **_prefixed("train", train),
                **_prefixed("valid", valid),
                **_prefixed("valid_stress", valid_stress),
                **_prefixed("valid_breadth", breadth),
            }
            current.append(row)
            fold_rows.append(row)

        frame = pd.DataFrame(current)
        selected = (
            frame.loc[frame["gate_pass"]]
            .sort_values(
                ["family", "selection_score", "valid_net_expectancy_bps"],
                ascending=[True, False, False],
            )
            .groupby("family", sort=False)
            .head(int(policy["walk_forward"]["top_per_family_per_fold"]))
        )
        print(
            "FOLD",
            fold_number,
            "GATE_PASS",
            int(frame["gate_pass"].sum()),
            "FAMILY_SELECTED",
            len(selected),
        )
        for row in selected.to_dict(orient="records"):
            hypothesis_id = str(row["hypothesis_id"])
            trades = trade_cache[hypothesis_id]
            test = period_metrics(
                trades,
                periods["test"],
                cost_bps_per_side=base_cost,
            )
            test_stress = period_metrics(
                trades,
                periods["test"],
                cost_bps_per_side=stress_cost,
            )
            test_breadth = cross_sectional_trade_metrics(
                trades,
                periods["test"],
                cost_bps_per_side=base_cost,
            )
            row.update(_prefixed("test", test))
            row.update(_prefixed("test_stress", test_stress))
            row.update(_prefixed("test_breadth", test_breadth))
            row["test_usable"] = int(test["trades"]) >= int(
                selection_policy["min_test_trades"]
            ) and int(test_breadth["traded_symbols"]) >= int(
                selection_policy["min_traded_symbols"]
            )
            selected_rows.append(row)

    selected = pd.DataFrame(selected_rows)
    hypothesis_map = {item.hypothesis_id: item for item in hypotheses}
    aggregate: list[dict[str, Any]] = []
    if not selected.empty:
        for hypothesis_id, group in selected.groupby("hypothesis_id"):
            usable = group.loc[group["test_usable"]].copy()
            if usable.empty:
                evaluated = 0
                positive = stress_positive = 0.0
                median_exp = worst_exp = median_stress = median_pf = math.nan
                median_symbol_positive = 0.0
                max_symbol_share = max_forced = 1.0
                total_trades = 0
            else:
                evaluated = len(usable)
                positive = float((usable["test_net_expectancy"] > 0).mean())
                stress_positive = float(
                    (usable["test_stress_net_expectancy"] > 0).mean()
                )
                median_exp = float(usable["test_net_expectancy_bps"].median())
                worst_exp = float(usable["test_net_expectancy_bps"].min())
                median_stress = float(usable["test_stress_net_expectancy_bps"].median())
                median_pf = float(usable["test_profit_factor"].median())
                median_symbol_positive = float(
                    usable["test_breadth_positive_symbol_ratio"].median()
                )
                max_symbol_share = float(
                    usable["test_breadth_max_symbol_trade_share"].max()
                )
                max_forced = float(usable["test_breadth_forced_trade_ratio"].max())
                total_trades = int(usable["test_trades"].sum())
            selected_folds = len(group)
            frequency = selected_folds / max(len(folds), 1)
            status = promotion_status(
                evaluated_folds=evaluated,
                selection_frequency=frequency,
                positive_fold_ratio=positive,
                stress_positive_fold_ratio=stress_positive,
                median_expectancy_bps=median_exp,
                worst_expectancy_bps=worst_exp,
                median_stress_expectancy_bps=median_stress,
                median_profit_factor=median_pf,
                median_positive_symbol_ratio=median_symbol_positive,
                maximum_symbol_trade_share=max_symbol_share,
                maximum_forced_trade_ratio=max_forced,
            )
            blockers = promotion_blockers(
                evaluated_folds=evaluated,
                selection_frequency=frequency,
                positive_fold_ratio=positive,
                stress_positive_fold_ratio=stress_positive,
                median_expectancy_bps=median_exp,
                worst_expectancy_bps=worst_exp,
                median_stress_expectancy_bps=median_stress,
                median_profit_factor=median_pf,
                median_positive_symbol_ratio=median_symbol_positive,
                maximum_symbol_trade_share=max_symbol_share,
                maximum_forced_trade_ratio=max_forced,
            )
            hypothesis = hypothesis_map[str(hypothesis_id)]
            finite_scores = (
                pd.to_numeric(group["selection_score"], errors="coerce")
                .replace([np.inf, -np.inf], np.nan)
                .dropna()
            )
            robustness = (
                float(finite_scores.median()) + float(median_exp)
                if not finite_scores.empty and math.isfinite(median_exp)
                else -math.inf
            )
            aggregate.append(
                {
                    **hypothesis.as_record(),
                    "selected_folds": selected_folds,
                    "selection_frequency": frequency,
                    "evaluated_test_folds": evaluated,
                    "positive_test_fold_ratio": positive,
                    "stress_positive_test_fold_ratio": stress_positive,
                    "median_test_expectancy_bps": median_exp,
                    "worst_test_expectancy_bps": worst_exp,
                    "median_stress_test_expectancy_bps": median_stress,
                    "median_test_profit_factor": median_pf,
                    "median_positive_symbol_ratio": median_symbol_positive,
                    "maximum_symbol_trade_share": max_symbol_share,
                    "maximum_forced_trade_ratio": max_forced,
                    "total_test_trades": total_trades,
                    "robustness_score": robustness,
                    "blockers": "|".join(blockers) if blockers else "NONE",
                    "blocker_count": len(blockers),
                    "status": status,
                    "promotion_stage": (
                        "VALIDATION_QUEUE" if status != "REJECT" else "REJECTED"
                    ),
                    "cross_engine_validated": False,
                    "dynamic_universe_generalized": False,
                    "execution_authority": "NONE",
                }
            )

    summary = hypotheses_frame(hypotheses)
    aggregate_frame = pd.DataFrame(aggregate)
    merge_keys = [
        "hypothesis_id",
        "strategy",
        "family",
        "rationale",
        "complexity",
        "primary_timeframe",
        "execution_timeframe",
        "execution_contract",
        "source_engine",
        "research_stage",
        "execution_authority",
        "params_json",
    ]
    if not aggregate_frame.empty:
        summary = summary.merge(
            aggregate_frame,
            on=merge_keys,
            how="left",
            suffixes=("", "_aggregate"),
        )
    summary["status"] = summary.get(
        "status", pd.Series(index=summary.index, dtype=object)
    ).fillna("REJECT_NOT_SELECTED")
    summary["promotion_stage"] = summary.get(
        "promotion_stage", pd.Series(index=summary.index, dtype=object)
    ).fillna("REJECTED")
    summary["blockers"] = summary.get(
        "blockers", pd.Series(index=summary.index, dtype=object)
    ).fillna("NOT_SELECTED_IN_ANY_FOLD")
    summary["blocker_count"] = (
        pd.to_numeric(
            summary.get(
                "blocker_count",
                pd.Series(index=summary.index, dtype=float),
            ),
            errors="coerce",
        )
        .fillna(1)
        .astype(int)
    )
    diagnostic_defaults = {
        "selected_folds": 0,
        "median_stress_test_expectancy_bps": math.nan,
        "median_test_expectancy_bps": math.nan,
    }
    for column, default in diagnostic_defaults.items():
        if column not in summary:
            summary[column] = default
    survivor_statuses = {"DIVERSE_SURVIVOR", "DIVERSE_STRONG_SURVIVOR"}
    survivors = summary.loc[summary["status"].isin(survivor_statuses)].copy()
    rejection_diagnostics = (
        summary.loc[~summary["status"].isin(survivor_statuses)]
        .sort_values(
            [
                "blocker_count",
                "selected_folds",
                "median_stress_test_expectancy_bps",
                "median_test_expectancy_bps",
            ],
            ascending=[True, False, False, False],
            na_position="last",
        )
        .reset_index(drop=True)
    )
    survivor_trades = materialize_survivor_trades(trade_cache, survivors)
    diversity = policy["diversity"]
    queue, redundancy = build_diversified_validation_queue(
        survivors,
        survivor_trades,
        maximum_total=int(diversity["maximum_validation_queue"]),
        maximum_per_family=int(diversity["maximum_per_family"]),
        entry_jaccard_limit=float(diversity["entry_jaccard_limit"]),
        pnl_correlation_limit=float(diversity["pnl_correlation_limit"]),
    )
    queue_decisions = redundancy.attrs.get("queue_decisions", pd.DataFrame())

    OUTPUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(fold_rows).to_csv(OUTPUT / "fold_candidates.csv", index=False)
    selected.to_csv(OUTPUT / "fold_selected.csv", index=False)
    summary.to_csv(OUTPUT / "all_hypotheses_summary.csv", index=False)
    rejection_diagnostics.to_csv(
        OUTPUT / "rejection_diagnostics.csv",
        index=False,
    )
    survivors.to_csv(OUTPUT / "survivors.csv", index=False)
    queue.to_csv(OUTPUT / "validation_queue.csv", index=False)
    redundancy.to_csv(OUTPUT / "redundancy.csv", index=False)
    queue_decisions.to_csv(OUTPUT / "queue_decisions.csv", index=False)
    survivor_trades.to_parquet(OUTPUT / "survivor_trades.parquet", index=False)

    artifact_names = (
        "blueprints.csv",
        "hypotheses.csv",
        "fold_candidates.csv",
        "fold_selected.csv",
        "all_hypotheses_summary.csv",
        "rejection_diagnostics.csv",
        "survivors.csv",
        "validation_queue.csv",
        "redundancy.csv",
        "queue_decisions.csv",
        "survivor_trades.parquet",
    )
    manifest = {
        name: {
            "sha256": _sha256(OUTPUT / name),
            "bytes": (OUTPUT / name).stat().st_size,
        }
        for name in artifact_names
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    audit = {
        "schema": SCHEMA,
        "blueprints": len(enabled),
        "families": len({item.family for item in hypotheses}),
        "hypotheses": len(hypotheses),
        "folds": len(folds),
        "survivors": len(survivors),
        "rejected_hypotheses": len(rejection_diagnostics),
        "survivor_families": int(survivors["family"].nunique())
        if not survivors.empty
        else 0,
        "validation_queue": len(queue),
        "validation_queue_families": int(queue["family"].nunique())
        if not queue.empty
        else 0,
        "survivor_trade_rows": len(survivor_trades),
        "failed_hypotheses": failures,
        "source_symbols": symbols,
        "source_paths": sources,
        "base_cost_bps_per_side": base_cost,
        "stress_cost_bps_per_side": stress_cost,
        "minimum_evaluated_folds": MINIMUM_EVALUATED_FOLDS,
        "ordinary_maximum_negative_folds": (ORDINARY_MAXIMUM_NEGATIVE_FOLDS),
        "strong_maximum_negative_folds": 0,
        "cross_engine_validation_required": True,
        "dynamic_universe_generalization_required": True,
        "automatic_finalist_promotion": False,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    print(
        "STRATEGY_GENERATION_V2_22",
        "HYPOTHESES",
        len(hypotheses),
        "SURVIVORS",
        len(survivors),
        "QUEUE",
        len(queue),
        "QUEUE_FAMILIES",
        audit["validation_queue_families"],
    )
    if not queue.empty:
        columns = [
            "queue_rank",
            "hypothesis_id",
            "strategy",
            "family",
            "status",
            "median_test_expectancy_bps",
            "median_stress_test_expectancy_bps",
            "median_test_profit_factor",
            "median_positive_symbol_ratio",
            "robustness_score",
        ]
        print(queue[columns].to_string(index=False))
    print("AUTOMATIC_FINALIST_PROMOTION", False)
    print("AUTOMATIC_LIVE_PROMOTION", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    print("ARTIFACT_ROOT", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
