#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.rl.pipeline_v2_21 import audit_rl_marl_pipeline_v221


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit one v2.21 RL/MARL run directory.")
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    audit = audit_rl_marl_pipeline_v221(args.run_root)
    print("RL_MARL_PIPELINE_AUDIT_V2_21", "VALID", audit["valid"])
    print("BROKER_CALLS", audit["broker_calls"])
    print("ORDER_CALLS", audit["order_calls"])
    print("EXECUTION_AUTHORITY", audit["execution_authority"])
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
