#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from stocks.research.cross_engine_handoff_v2_18 import (
    write_cross_engine_handoff,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()

    registry, manifest, audit, destination = write_cross_engine_handoff(
        ROOT,
        config_path=args.config,
        output_root=args.output_root,
    )

    print("=" * 100)
    print("CROSS_ENGINE_HANDOFF_V2_18 READY", audit["handoff_ready"])
    print("REGISTERED_STRATEGIES", audit["registered_strategies"])
    print("REQUIRED_ENGINES", "|".join(audit["required_engines"]))
    print("EVIDENCE_FILES", manifest["file_count"])
    print("REGISTRY_SHA256", audit["registry_sha256"])
    print("EVIDENCE_MANIFEST_SHA256", manifest["manifest_sha256"])
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT_ROOT", destination)
    print()
    print(
        registry[
            [
                "hypothesis_id",
                "strategy",
                "symbols",
                "trades",
                "validation_status",
                "handoff_status",
            ]
        ].to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
