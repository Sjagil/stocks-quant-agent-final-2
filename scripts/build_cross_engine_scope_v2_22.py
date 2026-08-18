#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from stocks.research.strategy_generation_v2_22 import (
    build_cross_engine_scope_config,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = (
    ROOT / "artifacts/research_runtime/strategy_generation_v2_22/validation_queue.csv"
)
DEFAULT_OUTPUT = (
    ROOT / "artifacts/research_runtime/strategy_generation_v2_22/"
    "cross_engine_scope.yaml"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE))
    parser.add_argument(
        "--base-config",
        default=str(ROOT / "config/cross_engine_strategy_validation_v2_17.yaml"),
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    queue_path = Path(args.queue).resolve()
    if not queue_path.is_file():
        raise FileNotFoundError(f"v2.22 validation queue missing: {queue_path}")
    queue = pd.read_csv(queue_path)
    base = yaml.safe_load(Path(args.base_config).read_text(encoding="utf-8"))
    config = build_cross_engine_scope_config(base, queue)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )

    print("CROSS_ENGINE_SCOPE_V2_22", "READY", True)
    print("STRATEGIES", len(config["scope"]["strategies"]))
    print("SCOPE_HASH", config["scope"]["scope_hash"])
    print("AUTOMATIC_LIVE_PROMOTION", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    print("OUTPUT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
