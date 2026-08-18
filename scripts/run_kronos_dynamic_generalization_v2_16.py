#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from stocks.agents.candle_fabric import frame_for_timeframe
from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner
from stocks.research.kronos_dynamic_generalization_v2_16 import (
    aggregate_generalization,
    evaluate_symbol_tests,
    freeze_candidates,
)
from stocks.research.kronos_strategy_factory import (
    evaluate_kronos_hypothesis,
    generate_kronos_hypotheses,
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
        for value in frame["symbol"].head(max(1, int(limit)))
        if str(value).strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-symbol", default="SMCI")
    parser.add_argument("--symbols")
    parser.add_argument("--from-queue", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--max-candidates", type=int, default=8)
    parser.add_argument("--stride", type=int)
    parser.add_argument("--sample-count", type=int)
    args = parser.parse_args()

    source_symbol = args.source_symbol.upper()

    config = yaml.safe_load(
        (ROOT / "config/kronos_research_v2_15.yaml").read_text(
            encoding="utf-8"
        )
    )
    integration_cfg = dict(config["integration"])
    backtest_cfg = dict(config["backtest"])

    source_root = (
        ROOT
        / "artifacts/research_runtime/"
        "kronos_strategy_research_v2_15"
    )
    summary_path = source_root / "all_hypotheses_summary.csv"
    if not summary_path.is_file():
        raise SystemExit(
            "Kronos source summary missing; run v2.15 research first"
        )

    source_summary = pd.read_csv(summary_path)
    source_summary = source_summary.loc[
        source_summary["symbol"].astype(str).str.upper() == source_symbol
    ].copy()
    frozen = freeze_candidates(
        source_summary,
        max_candidates=args.max_candidates,
    )
    if frozen.empty:
        raise SystemExit(
            "No positive frozen Kronos challengers available for generalization"
        )

    if args.symbols:
        universe = [
            value.strip().upper()
            for value in args.symbols.split(",")
            if value.strip()
        ]
    else:
        universe = _queue_symbols(args.limit)
    universe = [
        symbol for symbol in universe if symbol != source_symbol
    ]
    if not universe:
        raise SystemExit("No unseen symbols resolved")

    audit_path = source_root / "audit.json"
    source_audit = (
        json.loads(audit_path.read_text(encoding="utf-8"))
        if audit_path.is_file()
        else {}
    )
    stride = int(
        args.stride
        if args.stride is not None
        else source_audit.get("stride", integration_cfg["stride"])
    )
    sample_count = int(
        args.sample_count
        if args.sample_count is not None
        else integration_cfg.get("sample_count", 1)
    )

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

    hypotheses = {
        item.hypothesis_id: item
        for item in generate_kronos_hypotheses()
    }
    frozen_ids = [
        str(value)
        for value in frozen["hypothesis_id"].tolist()
        if str(value) in hypotheses
    ]
    if not frozen_ids:
        raise SystemExit("Frozen IDs not found in current hypothesis factory")

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "kronos_dynamic_generalization_v2_16"
    )
    input_root = output / "inputs"
    output.mkdir(parents=True, exist_ok=True)
    input_root.mkdir(parents=True, exist_ok=True)

    symbol_rows = []
    fold_rows = []
    inventory = []

    for symbol in universe:
        bars = frame_for_timeframe(ROOT, symbol, "1h").copy()
        bars.index = pd.to_datetime(bars.index, utc=True)
        bars = bars.sort_index()

        input_path = input_root / f"{symbol}_1h.parquet"
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
                "stride": stride,
                "batch_size": int(integration_cfg["batch_size"]),
                "temperature": float(integration_cfg["temperature"]),
                "top_k": int(integration_cfg["top_k"]),
                "top_p": float(integration_cfg["top_p"]),
                "sample_count": sample_count,
                "seed": int(integration_cfg.get("seed", 17)),
                "device": integration_cfg["device"],
            },
            timeout_seconds=3600,
            raise_on_error=True,
        )
        artifact = next(
            item
            for item in response.artifacts
            if item.path.endswith("historical_forecasts.parquet")
        )
        forecasts = pd.read_parquet(artifact.path)

        folds = rolling_periods(
            pd.DatetimeIndex(bars.index).sort_values().drop_duplicates(),
            hold_bars=int(backtest_cfg["purge_bars"]),
            requested_folds=int(backtest_cfg["folds"]),
        )

        inventory.append(
            {
                "symbol": symbol,
                "forecast_rows": int(len(forecasts)),
                "stride": stride,
                "sample_count": sample_count,
                "artifact": artifact.path,
            }
        )
        print(
            "KRONOS_GENERALIZATION_FORECASTS",
            symbol,
            "ROWS",
            len(forecasts),
            "STRIDE",
            stride,
        )

        for hypothesis_id in frozen_ids:
            hypothesis = hypotheses[hypothesis_id]
            trades = evaluate_kronos_hypothesis(
                hypothesis,
                bars,
                forecasts,
            )
            evidence = evaluate_symbol_tests(
                trades,
                folds,
                minimum_test_trades=int(
                    backtest_cfg["minimum_test_trades"]
                ),
                base_cost_bps_per_side=float(
                    backtest_cfg["base_cost_bps_per_side"]
                ),
                stress_cost_bps_per_side=float(
                    backtest_cfg["stress_cost_bps_per_side"]
                ),
            )
            for fold_row in evidence.pop("fold_rows"):
                fold_rows.append(
                    {
                        "symbol": symbol,
                        "hypothesis_id": hypothesis_id,
                        **fold_row,
                        "execution_authority": "NONE",
                    }
                )
            symbol_rows.append(
                {
                    "symbol": symbol,
                    "hypothesis_id": hypothesis_id,
                    "template": hypothesis.template,
                    "family": hypothesis.family,
                    "params_json": hypothesis.params_json,
                    **evidence,
                    "hypothesis_frozen_before_unseen_evaluation": True,
                    "cross_symbol_reselection": False,
                    "execution_authority": "NONE",
                }
            )

    symbol_frame = pd.DataFrame(symbol_rows)
    summary = aggregate_generalization(symbol_frame)
    validated = summary.loc[
        summary["status"] == "DYNAMIC_UNIVERSE_VALIDATED"
    ].copy()

    pd.DataFrame(inventory).to_csv(
        output / "forecast_inventory.csv", index=False
    )
    pd.DataFrame(fold_rows).to_csv(
        output / "fold_results.csv", index=False
    )
    symbol_frame.to_csv(
        output / "symbol_results.csv", index=False
    )
    summary.to_csv(
        output / "hypothesis_summary.csv", index=False
    )
    validated.to_csv(
        output / "validated.csv", index=False
    )
    frozen.to_csv(
        output / "frozen_source_candidates.csv", index=False
    )

    audit = {
        "schema": "kronos_dynamic_generalization_audit_v2_16",
        "source_symbol": source_symbol,
        "unseen_symbols": universe,
        "frozen_candidate_ids": frozen_ids,
        "frozen_before_unseen_evaluation": True,
        "cross_symbol_reselection": False,
        "stride": stride,
        "sample_count": sample_count,
        "validated": int(len(validated)),
        "cross_engine_validation_required": True,
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
        "KRONOS_DYNAMIC_GENERALIZATION_V2_16",
        "SOURCE",
        source_symbol,
        "UNSEEN",
        len(universe),
        "FROZEN",
        len(frozen_ids),
        "VALIDATED",
        len(validated),
    )
    if not summary.empty:
        print(summary.to_string(index=False))
    print("CROSS_SYMBOL_RESELECTION False")
    print("CROSS_ENGINE_VALIDATION_REQUIRED True")
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
