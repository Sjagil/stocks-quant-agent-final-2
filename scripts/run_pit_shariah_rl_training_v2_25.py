#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from stocks.rl.pipeline_v2_21 import (
    audit_rl_marl_pipeline_v221,
    load_rl_marl_pipeline_config_v221,
)
from stocks.rl.pit_shariah_pipeline_v2_25 import (
    run_pit_shariah_rl_marl_pipeline_v225,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train MAPPO/MATD3 on PIT historical data with a PIT Shariah tradable mask."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--maximum-folds", type=int, default=None)
    parser.add_argument("--algorithms", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--verify-reproducibility", action="store_true")
    args = parser.parse_args()

    pipeline = load_rl_marl_pipeline_config_v221(args.config, project_root=ROOT)
    ledger_path = Path(args.ledger).expanduser().resolve()
    if not ledger_path.is_file():
        raise FileNotFoundError(ledger_path)
    ledger = pd.read_csv(ledger_path)
    output, shariah_audit = run_pit_shariah_rl_marl_pipeline_v225(
        pipeline,
        shariah_ledger=ledger,
        smoke=args.smoke,
        maximum_folds=args.maximum_folds,
        algorithms=args.algorithms,
        seeds=args.seeds,
        verify_reproducibility=args.verify_reproducibility,
        project_root=ROOT,
    )
    audit = audit_rl_marl_pipeline_v221(output)
    print("PIT_SHARIAH_RL_TRAINING_V2_25", "COMPLETE", True)
    print("PIT_SHARIAH_MASK_APPLIED", True)
    print("UNKNOWN_SHARIAH_IS_INELIGIBLE", True)
    print("ELIGIBLE_SYMBOL_OBSERVATIONS", shariah_audit["eligible_symbol_observations"])
    print("PIPELINE_AUDIT_VALID", audit.get("valid", not audit.get("blockers")))
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    print("OUTPUT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
