#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from stocks.agents.candle_fabric import frame_for_timeframe
from stocks.agents.validation import (
    ALGORITHMS,
    load_validation_config,
    upsert_registry,
    validate_algorithm,
)


ROOT = Path(__file__).resolve().parents[1]


def symbols_from_queue(limit: int) -> list[str]:
    path = (
        ROOT
        / "artifacts/research_runtime/"
        "agent_training_queue_v2_13/queue.csv"
    )
    if not path.is_file():
        raise FileNotFoundError(
            "agent training queue missing; run "
            "build_agent_training_queue_v2_13.py first"
        )
    frame = pd.read_csv(path)
    return [
        str(value).upper()
        for value in frame["symbol"].head(limit)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols")
    parser.add_argument("--from-queue", action="store_true")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument(
        "--algorithms",
        default="DQN,SAC,MASKABLE_PPO",
    )
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--deploy", action="store_true")
    args = parser.parse_args()

    if args.smoke and args.deploy:
        raise SystemExit(
            "--deploy is forbidden for smoke validation"
        )

    if args.from_queue:
        symbols = symbols_from_queue(
            max(1, int(args.limit))
        )
    elif args.symbols:
        symbols = [
            item.strip().upper()
            for item in args.symbols.split(",")
            if item.strip()
        ]
    else:
        raise SystemExit(
            "provide --symbols or --from-queue"
        )

    algorithms = [
        value.strip().upper()
        for value in args.algorithms.split(",")
        if value.strip()
    ]
    unknown = set(algorithms).difference(ALGORITHMS)
    if unknown:
        raise SystemExit(
            f"unsupported algorithms: {sorted(unknown)}"
        )

    config = load_validation_config(
        ROOT / "config/agent_validation_v2_13.yaml"
    )

    results = []

    for symbol in symbols:
        frame = frame_for_timeframe(
            ROOT,
            symbol,
            args.timeframe,
        )

        for algorithm in algorithms:
            print(
                "=" * 78,
                "\nVALIDATE",
                symbol,
                args.timeframe,
                algorithm,
                "MODE",
                "SMOKE" if args.smoke else "FULL",
            )

            result = validate_algorithm(
                frame,
                symbol=symbol,
                timeframe=args.timeframe,
                algorithm=algorithm,
                project_root=ROOT,
                config=config,
                smoke=bool(args.smoke),
                deploy=bool(args.deploy),
            )
            results.append(result)

            summary = result["summary"]
            print(
                "RESULT",
                result["registry_status"],
                "POS_TEST",
                round(
                    summary["positive_test_fold_ratio"],
                    4,
                ),
                "POS_STRESS",
                round(
                    summary["positive_stress_fold_ratio"],
                    4,
                ),
                "MED_RETURN",
                round(
                    summary["median_test_return"],
                    6,
                ),
                "MED_SHARPE",
                round(
                    summary["median_test_sharpe"],
                    4,
                ),
                "WORST_DD",
                round(
                    summary["worst_test_drawdown"],
                    4,
                ),
                "BENCH_EDGE",
                round(
                    summary["benchmark_edge_ratio"],
                    4,
                ),
                "DEPLOYMENT",
                bool(result["deployment_manifest"]),
            )

    registry = upsert_registry(
        ROOT,
        results,
    )

    print("=" * 78)
    print("AGENT_VALIDATION_V2_13 COMPLETE")
    print("RESULTS", len(results))
    print("REGISTRY", registry)
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
