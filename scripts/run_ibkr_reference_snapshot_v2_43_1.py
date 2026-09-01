#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.production.ibkr_reference_snapshot_v2_43_1 import (
    fetch_reference_broker_snapshot_v2431,
    write_reference_snapshot_status_v2431,
)


def main() -> int:
    result = fetch_reference_broker_snapshot_v2431(ROOT)
    path = write_reference_snapshot_status_v2431(ROOT, result)
    payload = {
        "schema": "ibkr_reference_snapshot_v2_43_1",
        "status": "READY" if result.healthy else "BLOCKED",
        "healthy": result.healthy,
        "blockers": list(result.blockers),
        "diagnostics": result.diagnostics,
        "snapshot": result.snapshot.to_dict() if result.snapshot is not None else None,
        "artifact": str(path),
        "broker_write_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    print("IBKR_REFERENCE_SNAPSHOT_V2_43_1", payload["status"])
    return 0 if result.healthy else 2


if __name__ == "__main__":
    raise SystemExit(main())
