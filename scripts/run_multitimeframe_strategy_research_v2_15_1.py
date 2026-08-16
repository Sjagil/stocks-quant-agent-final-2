#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd
import yaml

from stocks.agents.candle_fabric import load_candle_bundle
from stocks.research.multitimeframe_strategy_factory import (
    TIMEFRAMES,
    evaluate_multitimeframe_hypothesis,
    generate_multitimeframe_hypotheses,
    trade_metrics,
)
from stocks.research.walkforward_splits import rolling_periods

ROOT = Path(__file__).resolve().parents[1]


def _queue_symbols(limit: int) -> list[str]:
    path = (
        ROOT
        / "artifacts/research_runtime/"
        "agent_training_queue_v2_13/queue.csv"
    )
    if not path.is_file():
        return []
    frame = pd.read_csv(path)
    return [
        str(value).strip().upper()
        for value in frame["symbol"].head(limit)
        if str(value).strip()
    ]


def _expanded(prefix: str, values: dict) -> dict:
    return {f"{prefix}_{key}": value for key, value in values.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols")
    parser.add_argument("--from-queue", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    cfg = yaml.safe_load(
        (ROOT / "config/multitimeframe_research_v2_15_1.yaml")
        .read_text(encoding="utf-8")
    )
    bt = cfg["backtest"]
    promo = cfg["promotion"]

    if args.from_queue or not args.symbols:
        symbols = _queue_symbols(max(1, args.limit))
    else:
        symbols = [
            item.strip().upper()
            for item in args.symbols.split(",")
            if item.strip()
        ]

    if not symbols:
        raise SystemExit("no symbols resolved")

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "multitimeframe_strategy_research_v2_15_1"
    )
    output.mkdir(parents=True, exist_ok=True)

    hypotheses = generate_multitimeframe_hypotheses()
    candidate_rows = []
    selected_rows = []
    summary_rows = []
    coverage_rows = []

    for symbol in symbols:
        bundle = load_candle_bundle(ROOT, symbol)
        available = tuple(tf for tf in TIMEFRAMES if tf in bundle.frames)
        missing = [tf for tf in TIMEFRAMES if tf not in bundle.frames]
        coverage_rows.append(
            {
                "symbol": symbol,
                "available": "|".join(available),
                "missing": "|".join(missing),
                **{
                    f"rows_{tf}": int(len(bundle.frames.get(tf, [])))
                    for tf in TIMEFRAMES
                },
            }
        )
        if missing:
            print("MTF_SKIP", symbol, "MISSING", "|".join(missing))
            continue

        frames = {tf: bundle.frames[tf] for tf in TIMEFRAMES}
        base_index = pd.DatetimeIndex(frames["15m"].index).sort_values()
        if len(base_index) < 2000:
            print("MTF_SKIP", symbol, "15M_ROWS", len(base_index))
            continue

        folds = rolling_periods(
            base_index,
            hold_bars=int(bt["purge_bars"]),
            requested_folds=int(bt["folds"]),
        )
        trade_cache = {
            h.hypothesis_id: evaluate_multitimeframe_hypothesis(h, frames)
            for h in hypotheses
        }
        hypothesis_map = {h.hypothesis_id: h for h in hypotheses}
        selected_by_id: dict[str, list[dict]] = {}

        for fold_number, periods in enumerate(folds, start=1):
            fold_rows = []
            for h in hypotheses:
                trades = trade_cache[h.hypothesis_id]
                train = trade_metrics(
                    trades,
                    periods["train"][0],
                    periods["train"][1],
                    cost_bps_per_side=float(bt["base_cost_bps_per_side"]),
                )
                valid = trade_metrics(
                    trades,
                    periods["valid"][0],
                    periods["valid"][1],
                    cost_bps_per_side=float(bt["base_cost_bps_per_side"]),
                )
                stress = trade_metrics(
                    trades,
                    periods["valid"][0],
                    periods["valid"][1],
                    cost_bps_per_side=float(bt["stress_cost_bps_per_side"]),
                )

                gate = (
                    train["trades"] >= int(bt["min_train_trades"])
                    and valid["trades"] >= int(bt["min_valid_trades"])
                    and math.isfinite(float(train["net_expectancy"]))
                    and math.isfinite(float(valid["net_expectancy"]))
                    and math.isfinite(float(stress["net_expectancy"]))
                    and float(train["net_expectancy"]) > 0.0
                    and float(valid["net_expectancy"]) > 0.0
                    and float(stress["net_expectancy"]) > 0.0
                    and float(train["profit_factor"]) > 1.0
                    and float(valid["profit_factor"]) > 1.0
                )
                robust = (
                    min(
                        float(train["net_expectancy_bps"]),
                        float(valid["net_expectancy_bps"]),
                    )
                    if gate
                    else -math.inf
                )
                row = {
                    "symbol": symbol,
                    "fold": fold_number,
                    **h.as_record(),
                    "gate_pass": bool(gate),
                    "robust_expectancy_bps": robust,
                    **_expanded("train", train),
                    **_expanded("valid", valid),
                    **_expanded("valid_stress", stress),
                }
                fold_rows.append(row)
                candidate_rows.append(row)

            fold_frame = pd.DataFrame(fold_rows)
            passed = (
                fold_frame.loc[fold_frame["gate_pass"]]
                .sort_values(
                    ["family", "robust_expectancy_bps"],
                    ascending=[True, False],
                )
                .groupby("family", sort=False)
                .head(int(bt["top_per_family"]))
            )
            print(
                "MTF_FOLD",
                symbol,
                fold_number,
                "PASS",
                int(fold_frame["gate_pass"].sum()),
                "SELECTED",
                len(passed),
            )

            for selected in passed.to_dict(orient="records"):
                hid = str(selected["hypothesis_id"])
                trades = trade_cache[hid]
                test = trade_metrics(
                    trades,
                    periods["test"][0],
                    periods["test"][1],
                    cost_bps_per_side=float(bt["base_cost_bps_per_side"]),
                )
                test_stress = trade_metrics(
                    trades,
                    periods["test"][0],
                    periods["test"][1],
                    cost_bps_per_side=float(bt["stress_cost_bps_per_side"]),
                )
                row = {
                    **selected,
                    **_expanded("test", test),
                    **_expanded("test_stress", test_stress),
                    "test_usable": (
                        test["trades"] >= int(bt["min_test_trades"])
                    ),
                }
                selected_rows.append(row)
                selected_by_id.setdefault(hid, []).append(row)

        for hid, rows in selected_by_id.items():
            group = pd.DataFrame(rows)
            usable = group.loc[group["test_usable"]]
            if usable.empty:
                continue

            pos = float((usable["test_net_expectancy"] > 0.0).mean())
            stress_pos = float(
                (usable["test_stress_net_expectancy"] > 0.0).mean()
            )
            med = float(usable["test_net_expectancy_bps"].median())
            worst = float(usable["test_net_expectancy_bps"].min())
            med_stress = float(
                usable["test_stress_net_expectancy_bps"].median()
            )
            med_pf = float(usable["test_profit_factor"].median())
            total_trades = int(usable["test_trades"].sum())

            survivor = (
                pos >= float(promo["positive_test_fold_ratio"])
                and stress_pos
                >= float(promo["stress_positive_test_fold_ratio"])
                and med > float(promo["median_test_expectancy_bps"])
                and worst > float(promo["worst_test_expectancy_bps"])
                and med_stress
                > float(promo["median_stress_expectancy_bps"])
                and med_pf > float(promo["median_profit_factor"])
            )
            h = hypothesis_map[hid]
            summary_rows.append(
                {
                    "symbol": symbol,
                    **h.as_record(),
                    "selected_folds": len(group),
                    "evaluated_test_folds": len(usable),
                    "positive_test_fold_ratio": pos,
                    "stress_positive_test_fold_ratio": stress_pos,
                    "median_test_expectancy_bps": med,
                    "worst_test_expectancy_bps": worst,
                    "median_stress_test_expectancy_bps": med_stress,
                    "median_test_profit_factor": med_pf,
                    "total_test_trades": total_trades,
                    "status": (
                        "PROVISIONAL_SURVIVOR"
                        if survivor
                        else "REJECT"
                    ),
                    "promotion_stage": (
                        "VALIDATION_QUEUE"
                        if survivor
                        else "REJECTED"
                    ),
                    "validation_route": (
                        "MTF_CROSS_ENGINE_AND_DYNAMIC_GENERALIZATION_REQUIRED"
                    ),
                    "cross_engine_validated": False,
                    "dynamic_universe_generalized": False,
                    "execution_authority": "NONE",
                }
            )

    candidates = pd.DataFrame(candidate_rows)
    selected = pd.DataFrame(selected_rows)
    summary = pd.DataFrame(summary_rows)
    if summary.empty:
        summary = pd.DataFrame(
            columns=[
                "symbol",
                "hypothesis_id",
                "template",
                "family",
                "params_json",
                "primary_timeframe",
                "execution_timeframe",
                "execution_contract",
                "source_engine",
                "research_stage",
                "selected_folds",
                "evaluated_test_folds",
                "positive_test_fold_ratio",
                "stress_positive_test_fold_ratio",
                "median_test_expectancy_bps",
                "worst_test_expectancy_bps",
                "median_stress_test_expectancy_bps",
                "median_test_profit_factor",
                "total_test_trades",
                "status",
                "promotion_stage",
                "validation_route",
                "cross_engine_validated",
                "dynamic_universe_generalized",
                "execution_authority",
            ]
        )
    survivors = (
        summary.loc[summary["status"] == "PROVISIONAL_SURVIVOR"].copy()
        if not summary.empty
        else summary.copy()
    )
    coverage = pd.DataFrame(coverage_rows)

    coverage.to_csv(output / "coverage.csv", index=False)
    candidates.to_csv(output / "fold_candidates.csv", index=False)
    selected.to_csv(output / "fold_selected.csv", index=False)
    summary.to_csv(output / "all_hypotheses_summary.csv", index=False)
    survivors.to_csv(output / "survivors.csv", index=False)

    audit = {
        "schema": "multitimeframe_strategy_research_audit_v2_15_1",
        "timeframes": list(TIMEFRAMES),
        "execution_timeframe": "15m",
        "primary_signal_timeframe": "1h",
        "higher_timeframe_lagged_one_complete_bar": True,
        "symbols_requested": symbols,
        "symbols_full_coverage": int(
            (coverage["missing"] == "").sum()
        ) if not coverage.empty else 0,
        "hypotheses": len(hypotheses),
        "survivors": len(survivors),
        "cross_engine_validation_required": True,
        "dynamic_universe_generalization_required": True,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "MULTITIMEFRAME_STRATEGY_RESEARCH_V2_15_1",
        "SYMBOLS",
        len(symbols),
        "FULL_COVERAGE",
        audit["symbols_full_coverage"],
        "HYPOTHESES",
        len(hypotheses),
        "SURVIVORS",
        len(survivors),
    )
    print(
        "TIMEFRAME_CHAIN",
        "1W_REGIME -> 1D_REGIME -> 4H/2H_SETUP -> 1H_SIGNAL -> 15M_EXECUTION",
    )
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
