#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from stocks.integrations.stocks_donor_contract_v2_17_1 import (
    write_stocks_donor_contract,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    audit = write_stocks_donor_contract(ROOT)

    print(
        "STOCKS_DONOR_INTEGRATION_V2_17_1",
        "STATUS", audit["status"],
        "COMMIT", audit.get("upstream_commit"),
        "RAW_CLEAN", audit.get("worktree_clean"),
        "CLEAN_FOR_CONTRACT", audit.get("worktree_clean_for_contract"),
    )

    for row in audit.get("active_workers", []):
        print(
            "ACTIVE_WORKER", row["integration"],
            "READY", row["active_contract_ready"],
            "MISSING", ",".join(row["missing_markers"]) or "NONE",
        )

    for row in audit.get("approved_sources", []):
        print(
            "DONOR_SOURCE", row["path"],
            "MODE", row["reuse_mode"],
            "READY", row["contract_ready"],
            "SHA", row.get("sha256"),
        )

    for row in audit.get("quarantine", []):
        print(
            "QUARANTINE", row["path"],
            "ENFORCED", row["quarantine_enforced"],
            "DETECTED", ",".join(row["detected_forbidden_markers"]) or "NONE",
            "REASON", row["reason"],
        )

    print(
        "PORTFOLIO_FEATURE_FILES",
        sum(bool(row["exists"]) for row in audit.get("portfolio_feature_sources", [])),
        "/",
        len(audit.get("portfolio_feature_sources", [])),
    )
    print(
        "ALLOWED_LOCAL_UNTRACKED",
        ",".join(audit.get("allowed_local_untracked", [])) or "NONE",
    )
    print("MANIFEST_HASH", audit.get("manifest_hash"))
    print("CANONICAL_BROKER_WRITER", audit.get("canonical_broker_writer"))
    print("WHOLE_SHARES_ONLY", audit["whole_shares_only"])
    print("FRACTIONAL_SHARES_ALLOWED", audit["fractional_shares_allowed"])
    print("FIXED_EURO_ORDER_CAP", audit["fixed_euro_order_cap"])
    print("DONOR_BROKER_WRITES", audit["donor_broker_writes"])
    print("AUTOMATIC_LIVE_PROMOTION", audit["automatic_live_promotion"])
    print("EXECUTION_AUTHORITY", audit["execution_authority"])
    print("BLOCKERS", "|".join(audit.get("blockers", [])) or "NONE")
    print(
        "ARTIFACT_ROOT",
        ROOT / "artifacts/research_runtime/stocks_donor_integration_v2_17_1",
    )
    return 0 if audit["status"] == "GO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
