#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from stocks.orchestration.forward_signal_engine_v2_19 import (
    write_validated_forward_signal_state,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployment-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()

    frame, audit, destination = write_validated_forward_signal_state(
        ROOT,
        deployment_root=args.deployment_root,
        output_root=args.output_root,
    )
    print("=" * 100)
    print("VALIDATED_FORWARD_SIGNALS_V2_19 READY", audit["ready"])
    print("ROWS", len(frame))
    print("NEW_ENTRY_READY", audit.get("new_entry_ready", 0))
    print("ELIGIBLE_STRATEGIES", audit["eligible_strategies"])
    print("STRICT_VALIDATED_DEPLOYMENT_GATE True")
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT_ROOT", destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
