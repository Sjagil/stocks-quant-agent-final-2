#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from stocks.intelligence_agent.strategy_combo_research_lab import FeatureCache
from stocks.research.indicator_discovery import (
    evaluate_indicator_hypothesis,
    generate_indicator_hypotheses,
    indicator_hypotheses_frame,
    promotion_status,
    validation_route,
)
from stocks.research.strategy_factory_1h import period_metrics, prepare_one_hour_frame
from stocks.research.walkforward_splits import rolling_periods

ROOT = Path(__file__).resolve().parents[1]


def _source(symbol: str) -> Path:
    for path in (
        ROOT / "data/canonical/provider_fabric" / f"{symbol}_1h.parquet",
        ROOT / "data/adjusted" / f"{symbol}_1h.parquet",
        ROOT / "data/derived" / f"{symbol}_1h.parquet",
        ROOT / "data/processed" / f"{symbol}_1h.parquet",
    ):
        if path.is_file():
            return path
    raise FileNotFoundError(f"{symbol}: 1h source missing")


def _load_frames(symbols: list[str]) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    frames: dict[str, pd.DataFrame] = {}
    sources: dict[str, str] = {}
    for symbol in symbols:
        path = _source(symbol)
        frame = prepare_one_hour_frame(pd.read_parquet(path), symbol)
        if len(frame) < 4000:
            raise ValueError(f"{symbol}: fewer than 4000 causal 1h bars")
        frames[symbol] = frame
        sources[symbol] = str(path)
        print(symbol, "1H_ROWS", len(frame), "FIRST", frame["date"].min(), "LAST", frame["date"].max())
    return frames, sources


def _finite_positive(value: object) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def _expanded(prefix: str, values: dict) -> dict:
    return {f"{prefix}_{key}": value for key, value in values.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "config/indicator_discovery.json"))
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--templates", default=None)
    parser.add_argument("--max-variants-per-template", type=int, default=None)
    args = parser.parse_args()

    policy = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if policy.get("schema") != "indicator_strategy_discovery_policy_v1":
        raise ValueError("invalid indicator discovery policy")

    symbols = [item.strip().upper() for item in (args.symbols.split(",") if args.symbols else policy["symbols"]) if item.strip()]
    templates = {item.strip() for item in args.templates.split(",") if item.strip()} if args.templates else set(policy["templates"])
    maximum = int(args.max_variants_per_template or policy["max_variants_per_template"])

    frames, sources = _load_frames(symbols)
    anchor = "SPY" if "SPY" in frames else symbols[0]
    anchor_index = pd.DatetimeIndex(frames[anchor]["date"]).sort_values().drop_duplicates()
    folds = rolling_periods(anchor_index, hold_bars=int(policy["purge_bars"]), requested_folds=int(policy["folds"]))

    hypotheses = generate_indicator_hypotheses(
        max_variants_per_template=maximum,
        seed=int(policy["seed"]),
        enabled_templates=templates,
    )
    hypothesis_map = {item.hypothesis_id: item for item in hypotheses}
    print("INDICATOR_TEMPLATES", len({item.template for item in hypotheses}))
    print("INDICATOR_HYPOTHESES", len(hypotheses))
    print("FOLDS", len(folds))

    caches = {symbol: FeatureCache(frame) for symbol, frame in frames.items()}
    trade_cache: dict[str, pd.DataFrame] = {}
    failures: list[dict] = []
    by_template: dict[str, list] = {}
    for hypothesis in hypotheses:
        by_template.setdefault(hypothesis.template, []).append(hypothesis)
    for template, items in sorted(by_template.items()):
        print("EVALUATE_INDICATOR", template, "VARIANTS", len(items))
        for hypothesis in items:
            try:
                trade_cache[hypothesis.hypothesis_id] = evaluate_indicator_hypothesis(hypothesis, frames, caches)
            except Exception as exc:
                failures.append({"hypothesis_id": hypothesis.hypothesis_id, "strategy": hypothesis.template, "error": f"{type(exc).__name__}: {exc}"})
                trade_cache[hypothesis.hypothesis_id] = pd.DataFrame()

    candidate_rows: list[dict] = []
    selected_rows: list[dict] = []
    for fold_number, periods in enumerate(folds, start=1):
        fold_rows: list[dict] = []
        for hypothesis in hypotheses:
            trades = trade_cache[hypothesis.hypothesis_id]
            train = period_metrics(trades, periods["train"], cost_bps_per_side=float(policy["base_cost_bps_per_side"]))
            valid = period_metrics(trades, periods["valid"], cost_bps_per_side=float(policy["base_cost_bps_per_side"]))
            stress = period_metrics(trades, periods["valid"], cost_bps_per_side=float(policy["stress_cost_bps_per_side"]))
            train_pf = train["profit_factor"]
            valid_pf = valid["profit_factor"]
            gate = (
                train["trades"] >= int(policy["min_train_trades"])
                and valid["trades"] >= int(policy["min_valid_trades"])
                and _finite_positive(train["net_expectancy"])
                and _finite_positive(valid["net_expectancy"])
                and _finite_positive(stress["net_expectancy"])
                and float(train_pf) > 1.0
                and float(valid_pf) > 1.0
            )
            robust_expectancy = min(float(train["net_expectancy_bps"]), float(valid["net_expectancy_bps"])) if math.isfinite(float(train["net_expectancy_bps"])) and math.isfinite(float(valid["net_expectancy_bps"])) else -math.inf
            robust_pf = min(float(train_pf), float(valid_pf)) if not pd.isna(train_pf) and not pd.isna(valid_pf) else -math.inf
            row = {
                "fold": fold_number,
                "hypothesis_id": hypothesis.hypothesis_id,
                "strategy": hypothesis.template,
                "family": hypothesis.family,
                "params_json": json.dumps(hypothesis.params, sort_keys=True, separators=(",", ":")),
                "execution_contract": hypothesis.execution_contract,
                "gate_pass": bool(gate),
                "robust_expectancy_bps": robust_expectancy,
                "robust_profit_factor": robust_pf,
                **_expanded("train", train),
                **_expanded("valid", valid),
                **_expanded("valid_stress", stress),
            }
            fold_rows.append(row)
            candidate_rows.append(row)
        fold_frame = pd.DataFrame(fold_rows)
        passed = (
            fold_frame.loc[fold_frame["gate_pass"]]
            .sort_values(["family", "robust_expectancy_bps", "robust_profit_factor", "valid_trades"], ascending=[True, False, False, False])
            .groupby("family", sort=False)
            .head(int(policy["top_per_family"]))
        )
        print("FOLD", fold_number, "CANDIDATES", int(fold_frame["gate_pass"].sum()), "SELECTED", len(passed))
        for _, selected in passed.iterrows():
            trades = trade_cache[str(selected["hypothesis_id"])]
            test = period_metrics(trades, periods["test"], cost_bps_per_side=float(policy["base_cost_bps_per_side"]))
            test_stress = period_metrics(trades, periods["test"], cost_bps_per_side=float(policy["stress_cost_bps_per_side"]))
            row = selected.to_dict()
            row.update(_expanded("test", test))
            row.update(_expanded("test_stress", test_stress))
            row["test_usable"] = test["trades"] >= int(policy["min_test_trades"])
            selected_rows.append(row)

    selected = pd.DataFrame(selected_rows)
    aggregate: list[dict] = []
    if not selected.empty:
        for hypothesis_id, group in selected.groupby("hypothesis_id"):
            usable = group.loc[group["test_usable"]]
            if usable.empty:
                evaluated = 0
                positive = stress_positive = 0.0
                median_exp = worst_exp = median_stress = median_pf = math.nan
                total_trades = 0
            else:
                evaluated = len(usable)
                positive = float((usable["test_net_expectancy"] > 0).mean())
                stress_positive = float((usable["test_stress_net_expectancy"] > 0).mean())
                median_exp = float(usable["test_net_expectancy_bps"].median())
                worst_exp = float(usable["test_net_expectancy_bps"].min())
                median_stress = float(usable["test_stress_net_expectancy_bps"].median())
                median_pf = float(usable["test_profit_factor"].median())
                total_trades = int(usable["test_trades"].sum())
            selected_folds = len(group)
            frequency = selected_folds / max(len(folds), 1)
            status = promotion_status(
                evaluated_folds=evaluated,
                selection_frequency=frequency,
                positive_ratio=positive,
                stress_positive_ratio=stress_positive,
                median_expectancy_bps=median_exp,
                worst_expectancy_bps=worst_exp,
                median_stress_bps=median_stress,
                median_profit_factor=median_pf,
            )
            hypothesis = hypothesis_map[str(hypothesis_id)]
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
                    "total_test_trades": total_trades,
                    "status": status,
                    "promotion_stage": "VALIDATION_QUEUE" if status != "REJECT" else "REJECTED",
                    "validation_route": validation_route(hypothesis.execution_contract),
                    "cross_engine_validated": False,
                    "dynamic_universe_generalized": False,
                    "execution_authority": "NONE",
                }
            )

    hypothesis_frame = indicator_hypotheses_frame(hypotheses)
    summary = hypothesis_frame.merge(
        pd.DataFrame(aggregate),
        on=["hypothesis_id", "template", "family", "primary_timeframe", "execution_timeframe", "execution_contract", "source_engine", "research_stage", "execution_authority", "params_json"],
        how="left",
        suffixes=("", "_agg"),
    ) if aggregate else hypothesis_frame.copy()
    if "status" not in summary:
        summary["status"] = "REJECT_NOT_SELECTED"
    else:
        summary["status"] = summary["status"].fillna("REJECT_NOT_SELECTED")
    if "promotion_stage" not in summary:
        summary["promotion_stage"] = "REJECTED"
    else:
        summary["promotion_stage"] = summary["promotion_stage"].fillna("REJECTED")

    survivors = summary.loc[summary["status"].isin(["SURVIVOR", "PROVISIONAL_SURVIVOR", "STRONG_SURVIVOR"])].copy()
    rejected = summary.loc[~summary.index.isin(survivors.index)].copy()
    output = ROOT / "artifacts/research_runtime/indicator_discovery_1h"
    output.mkdir(parents=True, exist_ok=True)
    hypothesis_frame.to_csv(output / "hypotheses.csv", index=False)
    pd.DataFrame(candidate_rows).to_csv(output / "fold_candidates.csv", index=False)
    selected.to_csv(output / "fold_selected.csv", index=False)
    summary.to_csv(output / "all_hypotheses_summary.csv", index=False)
    survivors.to_csv(output / "survivors.csv", index=False)
    rejected.to_csv(output / "rejected.csv", index=False)
    (output / "audit.json").write_text(
        json.dumps(
            {
                "schema": "indicator_strategy_discovery_audit_v1",
                "templates": len({item.template for item in hypotheses}),
                "hypotheses": len(hypotheses),
                "survivors": len(survivors),
                "strong_survivors": int((survivors.get("status", pd.Series(dtype=str)) == "STRONG_SURVIVOR").sum()),
                "validation_queue": len(survivors),
                "source_symbols": symbols,
                "source_paths": sources,
                "folds": len(folds),
                "base_cost_bps_per_side": policy["base_cost_bps_per_side"],
                "stress_cost_bps_per_side": policy["stress_cost_bps_per_side"],
                "failed_hypotheses": failures,
                "automatic_finalist_promotion": False,
                "cross_engine_validation_required": True,
                "dynamic_universe_generalization_required": True,
                "execution_authority": "NONE",
                "broker_calls": 0,
                "order_calls": 0,
            },
            indent=2,
            sort_keys=True,
            default=str,
        ) + "\n",
        encoding="utf-8",
    )
    print("INDICATOR_DISCOVERY_1H HYPOTHESES", len(hypotheses), "SURVIVORS", len(survivors), "VALIDATION_QUEUE", len(survivors))
    if not survivors.empty:
        cols = ["hypothesis_id", "template", "family", "status", "selected_folds", "positive_test_fold_ratio", "median_test_expectancy_bps", "worst_test_expectancy_bps", "median_stress_test_expectancy_bps", "median_test_profit_factor", "total_test_trades", "validation_route"]
        print(survivors[cols].sort_values(["status", "median_test_expectancy_bps"], ascending=[True, False]).to_string(index=False))
    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
