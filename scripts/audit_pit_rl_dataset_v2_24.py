from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.rl.dataset_v2_21 import load_portfolio_dataset_v221
from stocks.rl.pipeline_v2_21 import load_rl_marl_pipeline_config_v221
from stocks.training.pit_dataset_v2_24 import audit_rl_episode_v221_pit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
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
    audit = audit_rl_episode_v221_pit(bundle)
    print(json.dumps(audit, indent=2, sort_keys=True, default=str))
    print("PIT_RL_DATASET_AUDIT_V2_24", "VALID", audit["valid"])
    print("DATASET_HASH", audit["dataset_hash"])
    print("EXECUTION_AUTHORITY", audit["execution_authority"])
    return 0 if audit["valid"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
