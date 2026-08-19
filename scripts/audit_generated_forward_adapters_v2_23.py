#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from stocks.orchestration.generated_forward_adapter_audit_v2_23 import (
    write_generated_forward_adapter_audit,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-runtime", action="store_true")
    args = parser.parse_args()

    payload, path = write_generated_forward_adapter_audit(
        ROOT,
        require_runtime=args.require_runtime,
    )
    print(
        "GENERATED_FORWARD_ADAPTER_AUDIT_V2_23",
        "VALID",
        payload["coverage_complete"],
        "CATALOG",
        payload["catalog_strategy_count"],
        "SUPPORTED",
        payload["supported_generated_strategy_count"],
        "BROAD_GENERATED_FINALISTS",
        payload["broad_generated_finalists"],
        "RUNTIME_REQUIRED",
        payload["runtime_required"],
    )
    print(
        "MISSING_CATALOG_ADAPTERS",
        "|".join(payload["missing_catalog_adapters"]) or "NONE",
    )
    print(
        "MISSING_FINALIST_ADAPTERS",
        "|".join(payload["missing_finalist_adapters"]) or "NONE",
    )
    print(
        "RUNTIME_ERRORS",
        "|".join(payload["runtime_errors"]) or "NONE",
    )
    print("BROKER_CALLS", payload["broker_calls"])
    print("ORDER_CALLS", payload["order_calls"])
    print("EXECUTION_AUTHORITY", payload["execution_authority"])
    print("OUTPUT", path)
    return 0 if payload["coverage_complete"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
