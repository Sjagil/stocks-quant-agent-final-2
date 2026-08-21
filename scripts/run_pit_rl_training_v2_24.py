from __future__ import annotations

import argparse
from pathlib import Path

from stocks.rl.dataset_v2_21 import load_portfolio_dataset_v221
from stocks.rl.pipeline_v2_21 import (
    audit_rl_marl_pipeline_v221,
    load_rl_marl_pipeline_config_v221,
    run_rl_marl_pipeline_v221,
)
from stocks.training.pit_dataset_v2_24 import audit_rl_episode_v221_pit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--maximum-folds", type=int, default=None)
    parser.add_argument("--algorithms", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--verify-reproducibility", action="store_true")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    pipeline = load_rl_marl_pipeline_config_v221(args.config, project_root=root)
    bundle = load_portfolio_dataset_v221(
        pipeline.data_root,
        symbols=pipeline.symbols,
        timeframe=pipeline.timeframe,
        benchmark_symbol=pipeline.benchmark_symbol,
        verify_hash=pipeline.verify_source_hashes,
    )
    pit_audit = audit_rl_episode_v221_pit(bundle)
    if not pit_audit["valid"]:
        raise ValueError("PIT RL dataset audit failed: " + "|".join(pit_audit["errors"]))

    output = run_rl_marl_pipeline_v221(
        pipeline,
        smoke=args.smoke,
        maximum_folds=args.maximum_folds,
        algorithms=args.algorithms,
        seeds=args.seeds,
        verify_reproducibility=args.verify_reproducibility,
        project_root=root,
    )
    audit = audit_rl_marl_pipeline_v221(output)
    print("PIT_RL_TRAINING_V2_24", "COMPLETE", True)
    print("PIT_DATASET_VALID", pit_audit["valid"])
    print("DATASET_HASH", pit_audit["dataset_hash"])
    print("PIPELINE_AUDIT_VALID", audit.get("valid", not audit.get("blockers")))
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    print("OUTPUT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
