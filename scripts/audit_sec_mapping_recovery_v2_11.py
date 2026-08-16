#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stocks.research.sec_mapping_audit_v2_11 import summarize_recovery


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    before_path = (
        ROOT
        / "artifacts/research_runtime/"
        "shariah_financial_verification_v2_10_baseline/"
        "verification.csv"
    )
    after_path = (
        ROOT
        / "artifacts/research_runtime/"
        "shariah_financial_verification/"
        "verification.csv"
    )

    if not before_path.is_file():
        print("SEC_MAPPING_AUDIT_V2_11 ERROR BASELINE_MISSING", before_path)
        return 2
    if not after_path.is_file():
        print("SEC_MAPPING_AUDIT_V2_11 ERROR CURRENT_VERIFICATION_MISSING", after_path)
        return 2

    before = pd.read_csv(before_path)
    after = pd.read_csv(after_path)
    frame, audit = summarize_recovery(before, after)

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "sec_mapping_audit_v2_11"
    )
    output.mkdir(parents=True, exist_ok=True)

    frame.to_csv(output / "recovery.csv", index=False)
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "SEC_MAPPING_AUDIT_V2_11",
        "CHANGED",
        audit["changed"],
        "RECOVERED",
        audit["recovered_from_incomplete"],
        "REMAINING_INCOMPLETE",
        audit["remaining_incomplete"],
        "TRADE_ELIGIBLE",
        audit["trade_eligible"],
    )

    if not frame.empty:
        changed = frame.loc[frame["changed"]]
        if not changed.empty:
            print(
                changed[
                    [
                        "symbol",
                        "before_status",
                        "after_status",
                        "after_business_status",
                        "after_financial_ratio_status",
                    ]
                ].to_string(index=False)
            )

    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
