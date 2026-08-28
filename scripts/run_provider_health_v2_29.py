#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.providers.health_v2_29 import provider_health_table

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT = ROOT / "artifacts/research_runtime/provider_federation_v2_27/audit.json"
OUTPUT = ROOT / "artifacts/research_runtime/provider_health_v2_29"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", default=str(DEFAULT_AUDIT))
    args = parser.parse_args()

    audit_path = Path(args.audit)
    if not audit_path.is_file():
        print("PROVIDER_HEALTH_V2_29 BLOCKED AUDIT_MISSING", audit_path)
        return 2

    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    summary = payload.get("source_fabric_summary", {}).get("providers", {})
    table = provider_health_table(summary)
    if not table:
        print("PROVIDER_HEALTH_V2_29 BLOCKED PROVIDER_SUMMARY_EMPTY")
        return 2

    output = {
        "schema": "provider_health_v2_29",
        "source_audit": str(audit_path),
        "providers": table,
        "healthy": [row["provider"] for row in table if row["status"] == "HEALTHY"],
        "degraded": [row["provider"] for row in table if row["status"] == "DEGRADED"],
        "weak": [row["provider"] for row in table if row["status"] == "WEAK"],
        "failed": [row["provider"] for row in table if row["status"] == "FAILED"],
        "broker_submission_enabled": False,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / "provider_health.json"
    target.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        "PROVIDER_HEALTH_V2_29",
        "PROVIDERS", len(table),
        "HEALTHY", len(output["healthy"]),
        "DEGRADED", len(output["degraded"]),
        "WEAK", len(output["weak"]),
        "FAILED", len(output["failed"]),
    )
    for row in table:
        print(
            "PROVIDER",
            row["provider"],
            "STATUS", row["status"],
            "SCORE", f'{float(row["reliability_score"]):.4f}',
            "OK_RATE", f'{float(row["ok_rate"]):.4f}',
            "ERROR_RATE", f'{float(row["error_rate"]):.4f}',
        )
    print("BROKER_SUBMISSION_ENABLED False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT", target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
