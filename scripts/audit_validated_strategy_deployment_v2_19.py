#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from stocks.orchestration.validated_strategy_deployment_v2_19 import (
    verify_validated_strategy_deployment,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()

    result = verify_validated_strategy_deployment(
        ROOT,
        output_root=args.output_root,
    )
    print("=" * 100)
    print("VALIDATED_STRATEGY_DEPLOYMENT_AUDIT_V2_19 VALID", result["valid"])
    print("ELIGIBLE_STRATEGIES", result.get("eligible_strategies", 0))
    print("REGISTRY_SHA256", result.get("registry_sha256", "NONE"))
    print("SOURCE_FINGERPRINT", result.get("source_fingerprint", "NONE"))
    for error in result["errors"]:
        print("ERROR", error)
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
