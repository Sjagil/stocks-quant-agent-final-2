#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from stocks.orchestration.validated_strategy_deployment_v2_19 import (
    write_validated_strategy_deployment,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()

    registry, manifest, audit, destination, changed = (
        write_validated_strategy_deployment(
            ROOT,
            config_path=args.config,
            output_root=args.output_root,
        )
    )
    print("=" * 100)
    print("VALIDATED_STRATEGY_DEPLOYMENT_V2_19 READY", audit["deployment_ready"])
    print("ELIGIBLE_STRATEGIES", len(registry))
    print("SOURCE_FILES", manifest["file_count"])
    print("SOURCE_FINGERPRINT", audit["source_fingerprint"])
    print("REGISTRY_SHA256", audit["registry_sha256"])
    print("OUTPUT_CHANGED", changed)
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT_ROOT", destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
