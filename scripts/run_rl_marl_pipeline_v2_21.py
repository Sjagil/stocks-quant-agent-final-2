#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from stocks.rl.pipeline_v2_21 import (
    audit_rl_marl_pipeline_v221,
    load_rl_marl_pipeline_config_v221,
    run_rl_marl_pipeline_v221,
)

ROOT = Path(__file__).resolve().parents[1]


def _csv_strings(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    result = tuple(part.strip().upper() for part in value.split(",") if part.strip())
    return result or None


def _csv_ints(value: str | None) -> tuple[int, ...] | None:
    if value is None:
        return None
    result = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    return result or None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the v2.21 point-in-time MAPPO/MATD3 research pipeline."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config/rl_marl_pipeline_v2_21.yaml",
    )
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--algorithms", help="Comma-separated MAPPO,MATD3 subset")
    parser.add_argument("--seeds", help="Comma-separated seed subset; full runs require 10")
    parser.add_argument("--symbols", help="Comma-separated canonical dataset symbols")
    parser.add_argument("--benchmark-symbol")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--max-folds", type=int)
    parser.add_argument(
        "--verify-reproducibility",
        action="store_true",
        help="Repeat every train/evaluate trial and require identical evidence.",
    )
    args = parser.parse_args()

    pipeline = load_rl_marl_pipeline_config_v221(args.config, project_root=ROOT)
    selected_symbols = _csv_strings(args.symbols) or pipeline.symbols
    benchmark_symbol = (
        args.benchmark_symbol.strip().upper()
        if args.benchmark_symbol
        else (
            pipeline.benchmark_symbol
            if pipeline.benchmark_symbol in selected_symbols
            else None
        )
    )
    pipeline = replace(
        pipeline,
        symbols=selected_symbols,
        benchmark_symbol=benchmark_symbol,
        data_root=(args.data_root.resolve() if args.data_root else pipeline.data_root),
        output_root=(
            args.output_root.resolve() if args.output_root else pipeline.output_root
        ),
    )
    run_root = run_rl_marl_pipeline_v221(
        pipeline,
        smoke=args.smoke,
        maximum_folds=args.max_folds,
        algorithms=_csv_strings(args.algorithms),
        seeds=_csv_ints(args.seeds),
        verify_reproducibility=args.verify_reproducibility,
        project_root=ROOT,
    )
    audit = audit_rl_marl_pipeline_v221(run_root)
    print("=" * 100)
    print("RL_MARL_PIPELINE_V2_21", "VALID", audit["valid"])
    print("RUN_ROOT", run_root)
    print("TRIALS", audit["trials"])
    print("AUTOMATIC_LIVE_PROMOTION", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
