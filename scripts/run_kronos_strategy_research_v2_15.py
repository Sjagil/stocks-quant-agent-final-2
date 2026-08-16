#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd
import yaml

from stocks.agents.candle_fabric import frame_for_timeframe
from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner
from stocks.research.kronos_strategy_factory import (
    evaluate_kronos_hypothesis,
    generate_kronos_hypotheses,
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
        str(value).upper()
        for value in frame["symbol"].head(limit)
    ]


def _expanded(prefix: str, values: dict) -> dict:
    return {
        f"{prefix}_{key}": value
        for key, value in values.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols")
    parser.add_argument("--from-queue", action="store_true")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--model")
    parser.add_argument("--tokenizer")
    parser.add_argument("--lookback", type=int)
    parser.add_argument("--pred-len", type=int)
    parser.add_argument("--stride", type=int)
    parser.add_argument("--sample-count", type=int)
    args = parser.parse_args()

    cfg = yaml.safe_load(
        (ROOT / "config/kronos_research_v2_15.yaml").read_text(
            encoding="utf-8"
        )
    )
    integration_cfg = dict(cfg["integration"])
    backtest_cfg = dict(cfg["backtest"])
    promotion_cfg = dict(cfg["promotion"])

    if args.from_queue:
        symbols = _queue_symbols(max(1, args.limit))
    elif args.symbols:
        symbols = [
            item.strip().upper()
            for item in args.symbols.split(",")
            if item.strip()
        ]
    else:
        symbols = _queue_symbols(max(1, args.limit))

    if not symbols:
        raise SystemExit("no symbols resolved")

    overrides = {
        "model": args.model,
        "tokenizer": args.tokenizer,
        "lookback": args.lookback,
        "pred_len": args.pred_len,
        "stride": args.stride,
        "sample_count": args.sample_count,
    }
    for key, value in overrides.items():
        if value is not None:
            integration_cfg[key] = value

    registry = IntegrationRegistry.load(
        ROOT / "config/integrations.yaml",
        project_root=ROOT,
    )
    runner = IntegrationRunner(registry)
    health = runner.health("kronos")
    if not health.ok:
        raise SystemExit(
            f"Kronos integration unavailable: {health.error}"
        )
    print("KRONOS_HEALTH", health.state.value, health.data)

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "kronos_strategy_research_v2_15"
    )
    input_root = output / "inputs"
    output.mkdir(parents=True, exist_ok=True)
    input_root.mkdir(parents=True, exist_ok=True)

    hypotheses = generate_kronos_hypotheses()
    all_fold_rows = []
    all_selected_rows = []
    summary_rows = []
    forecast_inventory = []

    for symbol in symbols:
        bars = frame_for_timeframe(
            ROOT, symbol, args.timeframe
        ).copy()
        bars.index = pd.to_datetime(bars.index, utc=True)
        bars = bars.sort_index()

        input_path = input_root / f"{symbol}_{args.timeframe}.parquet"
        bars.to_parquet(input_path)

        response = runner.run(
            "kronos",
            "forecast_series",
            {
                "input_parquet": str(input_path),
                "model": integration_cfg["model"],
                "tokenizer": integration_cfg["tokenizer"],
                "max_context": int(integration_cfg["max_context"]),
                "lookback": int(integration_cfg["lookback"]),
                "pred_len": int(integration_cfg["pred_len"]),
                "stride": int(integration_cfg["stride"]),
                "batch_size": int(integration_cfg["batch_size"]),
                "temperature": float(
                    integration_cfg["temperature"]
                ),
                "top_k": int(integration_cfg["top_k"]),
                "top_p": float(integration_cfg["top_p"]),
                "sample_count": int(
                    integration_cfg["sample_count"]
                ),
                "seed": int(integration_cfg.get("seed", 17)),
                "device": integration_cfg["device"],
            },
            timeout_seconds=3600,
            raise_on_error=True,
        )
        forecast_artifact = next(
            item
            for item in response.artifacts
            if item.path.endswith(
                "historical_forecasts.parquet"
            )
        )
        forecasts = pd.read_parquet(
            forecast_artifact.path
        )
        forecast_inventory.append(
            {
                "symbol": symbol,
                "rows": len(forecasts),
                "artifact": forecast_artifact.path,
                **response.data,
            }
        )
        print(
            "KRONOS_FORECASTS",
            symbol,
            "ROWS",
            len(forecasts),
            "MODEL",
            response.data.get("model"),
        )

        decisions = pd.DatetimeIndex(
            pd.to_datetime(
                forecasts["decision_timestamp"],
                utc=True,
            )
        ).sort_values().drop_duplicates()

        if len(decisions) < 100:
            print(
                "KRONOS_SKIP",
                symbol,
                "INSUFFICIENT_FORECAST_DECISIONS",
                len(decisions),
            )
            continue

        # Walk-forward geometry is defined on the underlying candle
        # chronology, not on sparse Kronos forecast rows.
        folds = rolling_periods(
            pd.DatetimeIndex(bars.index).sort_values().drop_duplicates(),
            hold_bars=int(backtest_cfg["purge_bars"]),
            requested_folds=int(backtest_cfg["folds"]),
        )
        trade_cache = {
            item.hypothesis_id: evaluate_kronos_hypothesis(
                item, bars, forecasts
            )
            for item in hypotheses
        }
        selected_by_id: dict[str, list[dict]] = {}

        for fold_number, periods in enumerate(
            folds, start=1
        ):
            candidates = []
            for hypothesis in hypotheses:
                trades = trade_cache[
                    hypothesis.hypothesis_id
                ]
                train = trade_metrics(
                    trades,
                    periods["train"][0],
                    periods["train"][1],
                    cost_bps_per_side=float(
                        backtest_cfg[
                            "base_cost_bps_per_side"
                        ]
                    ),
                )
                valid = trade_metrics(
                    trades,
                    periods["valid"][0],
                    periods["valid"][1],
                    cost_bps_per_side=float(
                        backtest_cfg[
                            "base_cost_bps_per_side"
                        ]
                    ),
                )
                stress = trade_metrics(
                    trades,
                    periods["valid"][0],
                    periods["valid"][1],
                    cost_bps_per_side=float(
                        backtest_cfg[
                            "stress_cost_bps_per_side"
                        ]
                    ),
                )
                gate = (
                    train["trades"]
                    >= int(
                        backtest_cfg[
                            "minimum_train_trades"
                        ]
                    )
                    and valid["trades"]
                    >= int(
                        backtest_cfg[
                            "minimum_valid_trades"
                        ]
                    )
                    and math.isfinite(
                        float(train["net_expectancy"])
                    )
                    and math.isfinite(
                        float(valid["net_expectancy"])
                    )
                    and math.isfinite(
                        float(stress["net_expectancy"])
                    )
                    and float(train["net_expectancy"]) > 0.0
                    and float(valid["net_expectancy"]) > 0.0
                    and float(stress["net_expectancy"]) > 0.0
                    and float(train["profit_factor"]) > 1.0
                    and float(valid["profit_factor"]) > 1.0
                )
                robust = (
                    min(
                        float(
                            train["net_expectancy_bps"]
                        ),
                        float(
                            valid["net_expectancy_bps"]
                        ),
                    )
                    if gate
                    else -math.inf
                )
                row = {
                    "symbol": symbol,
                    "fold": fold_number,
                    **hypothesis.as_record(),
                    "gate_pass": bool(gate),
                    "robust_expectancy_bps": robust,
                    **_expanded("train", train),
                    **_expanded("valid", valid),
                    **_expanded("valid_stress", stress),
                }
                all_fold_rows.append(row)
                candidates.append(row)

            candidate_frame = pd.DataFrame(candidates)
            passed = (
                candidate_frame.loc[
                    candidate_frame["gate_pass"]
                ]
                .sort_values(
                    ["family", "robust_expectancy_bps"],
                    ascending=[True, False],
                )
                .groupby("family", sort=False)
                .head(int(backtest_cfg["top_per_family"]))
            )

            print(
                "KRONOS_FOLD",
                symbol,
                fold_number,
                "PASS",
                int(
                    candidate_frame[
                        "gate_pass"
                    ].sum()
                ),
                "SELECTED",
                len(passed),
            )

            for selected in passed.to_dict(
                orient="records"
            ):
                hypothesis_id = str(
                    selected["hypothesis_id"]
                )
                trades = trade_cache[hypothesis_id]
                test = trade_metrics(
                    trades,
                    periods["test"][0],
                    periods["test"][1],
                    cost_bps_per_side=float(
                        backtest_cfg[
                            "base_cost_bps_per_side"
                        ]
                    ),
                )
                test_stress = trade_metrics(
                    trades,
                    periods["test"][0],
                    periods["test"][1],
                    cost_bps_per_side=float(
                        backtest_cfg[
                            "stress_cost_bps_per_side"
                        ]
                    ),
                )
                row = {
                    **selected,
                    **_expanded("test", test),
                    **_expanded(
                        "test_stress", test_stress
                    ),
                    "test_usable": (
                        test["trades"]
                        >= int(
                            backtest_cfg[
                                "minimum_test_trades"
                            ]
                        )
                    ),
                }
                all_selected_rows.append(row)
                selected_by_id.setdefault(
                    hypothesis_id, []
                ).append(row)

        hypothesis_map = {
            item.hypothesis_id: item
            for item in hypotheses
        }

        for hypothesis_id, rows in selected_by_id.items():
            group = pd.DataFrame(rows)
            usable = group.loc[group["test_usable"]]
            if usable.empty:
                continue

            selected_folds = len(group)
            positive_ratio = float(
                (
                    usable["test_net_expectancy"]
                    > 0.0
                ).mean()
            )
            stress_ratio = float(
                (
                    usable[
                        "test_stress_net_expectancy"
                    ]
                    > 0.0
                ).mean()
            )
            median_expectancy = float(
                usable[
                    "test_net_expectancy_bps"
                ].median()
            )
            worst_expectancy = float(
                usable[
                    "test_net_expectancy_bps"
                ].min()
            )
            median_stress = float(
                usable[
                    "test_stress_net_expectancy_bps"
                ].median()
            )
            median_pf = float(
                usable["test_profit_factor"].median()
            )
            total_trades = int(
                usable["test_trades"].sum()
            )

            quality_gate = (
                selected_folds
                >= int(
                    promotion_cfg[
                        "minimum_selected_folds"
                    ]
                )
                and positive_ratio
                >= float(
                    promotion_cfg[
                        "minimum_positive_test_fold_ratio"
                    ]
                )
                and stress_ratio
                >= float(
                    promotion_cfg[
                        "minimum_stress_positive_test_fold_ratio"
                    ]
                )
                and median_expectancy
                > float(
                    promotion_cfg[
                        "minimum_median_test_expectancy_bps"
                    ]
                )
                and worst_expectancy
                > float(
                    promotion_cfg[
                        "minimum_worst_test_expectancy_bps"
                    ]
                )
                and median_stress
                > float(
                    promotion_cfg[
                        "minimum_median_stress_expectancy_bps"
                    ]
                )
                and median_pf
                > float(
                    promotion_cfg[
                        "minimum_median_profit_factor"
                    ]
                )
            )
            enough_oos_folds = (
                len(usable)
                >= int(
                    promotion_cfg.get(
                        "minimum_evaluated_test_folds",
                        2,
                    )
                )
            )
            survivor = bool(
                quality_gate
                and enough_oos_folds
            )
            insufficient_oos = bool(
                quality_gate
                and not enough_oos_folds
            )

            hypothesis = hypothesis_map[
                hypothesis_id
            ]
            summary_rows.append(
                {
                    "symbol": symbol,
                    **hypothesis.as_record(),
                    "selected_folds": selected_folds,
                    "evaluated_test_folds": len(
                        usable
                    ),
                    "positive_test_fold_ratio": positive_ratio,
                    "stress_positive_test_fold_ratio": stress_ratio,
                    "median_test_expectancy_bps": median_expectancy,
                    "worst_test_expectancy_bps": worst_expectancy,
                    "median_stress_test_expectancy_bps": median_stress,
                    "median_test_profit_factor": median_pf,
                    "total_test_trades": total_trades,
                    "status": (
                        "PROVISIONAL_SURVIVOR"
                        if survivor
                        else (
                            "INSUFFICIENT_OOS_EVIDENCE"
                            if insufficient_oos
                            else "REJECT"
                        )
                    ),
                    "promotion_stage": (
                        "VALIDATION_QUEUE"
                        if survivor
                        else (
                            "GENERALIZATION_EVIDENCE_QUEUE"
                            if insufficient_oos
                            else "REJECTED"
                        )
                    ),
                    "validation_route": (
                        "KRONOS_CROSS_ENGINE_AND_DYNAMIC_GENERALIZATION_REQUIRED"
                    ),
                    "cross_engine_validated": False,
                    "dynamic_universe_generalized": False,
                    "automatic_finalist_promotion": False,
                    "execution_authority": "NONE",
                }
            )

    fold_frame = pd.DataFrame(all_fold_rows)
    selected_frame = pd.DataFrame(
        all_selected_rows
    )
    summary = pd.DataFrame(summary_rows)
    if summary.empty:
        summary = pd.DataFrame(
            columns=[
                "symbol",
                "hypothesis_id",
                "template",
                "family",
                "params_json",
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
                "automatic_finalist_promotion",
                "execution_authority",
            ]
        )
    survivors = (
        summary.loc[
            summary["status"].isin(
                [
                    "PROVISIONAL_SURVIVOR",
                    "SURVIVOR",
                    "STRONG_SURVIVOR",
                ]
            )
        ].copy()
        if not summary.empty
        else summary.copy()
    )

    fold_frame.to_csv(
        output / "fold_candidates.csv",
        index=False,
    )
    selected_frame.to_csv(
        output / "fold_selected.csv",
        index=False,
    )
    summary.to_csv(
        output / "all_hypotheses_summary.csv",
        index=False,
    )
    survivors.to_csv(
        output / "survivors.csv",
        index=False,
    )
    pd.DataFrame(forecast_inventory).to_csv(
        output / "forecast_inventory.csv",
        index=False,
    )
    (output / "audit.json").write_text(
        json.dumps(
            {
                "schema": (
                    "kronos_strategy_research_audit_v2_15"
                ),
                "symbols": symbols,
                "hypotheses": len(hypotheses),
                "summary_rows": len(summary),
                "survivors": len(survivors),
                "model": integration_cfg["model"],
                "tokenizer": integration_cfg[
                    "tokenizer"
                ],
                "lookback": integration_cfg[
                    "lookback"
                ],
                "pred_len": integration_cfg[
                    "pred_len"
                ],
                "stride": integration_cfg[
                    "stride"
                ],
                "point_in_time_forecast_generation": True,
                "future_prices_used_as_model_input": False,
                "future_timestamps_only": True,
                "cross_engine_validation_required": True,
                "dynamic_universe_generalization_required": True,
                "automatic_live_promotion": False,
                "execution_authority": "NONE",
                "broker_calls": 0,
                "order_calls": 0,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "KRONOS_STRATEGY_RESEARCH_V2_15",
        "SYMBOLS",
        len(symbols),
        "HYPOTHESES",
        len(hypotheses),
        "SURVIVORS",
        len(survivors),
    )
    if not survivors.empty:
        print(
            survivors[
                [
                    "symbol",
                    "hypothesis_id",
                    "template",
                    "family",
                    "positive_test_fold_ratio",
                    "stress_positive_test_fold_ratio",
                    "median_test_expectancy_bps",
                    "worst_test_expectancy_bps",
                    "median_test_profit_factor",
                    "total_test_trades",
                    "status",
                ]
            ].to_string(index=False)
        )
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
