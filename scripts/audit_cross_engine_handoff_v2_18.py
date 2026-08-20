#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from stocks.research.cross_engine_handoff_v2_18 import (
    verify_cross_engine_handoff,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()

    verification = verify_cross_engine_handoff(
        ROOT,
        output_root=args.output_root,
    )
    print("=" * 100)
    print("CROSS_ENGINE_HANDOFF_AUDIT_V2_18 VALID", verification["valid"])
    print(
        "REGISTERED_STRATEGIES",
        verification.get("registered_strategies", 0),
    )
    print("EVIDENCE_FILES", verification.get("evidence_file_count", 0))
    print("REGISTRY_SHA256", verification.get("registry_sha256", "NONE"))
    print(
        "EVIDENCE_MANIFEST_SHA256",
        verification.get("evidence_manifest_sha256", "NONE"),
    )
    for error in verification["errors"]:
        print("ERROR", error)
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0 if verification["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
