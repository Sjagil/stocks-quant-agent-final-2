from __future__ import annotations

from typing import Any

import pandas as pd


def summarize_recovery(
    before: pd.DataFrame,
    after: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    def keyed(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
        if frame.empty or "symbol" not in frame.columns:
            return {}
        return {
            str(row["symbol"]).upper(): row
            for row in frame.to_dict(orient="records")
        }

    left = keyed(before)
    right = keyed(after)
    rows: list[dict[str, Any]] = []

    for symbol in sorted(set(left) | set(right)):
        old = left.get(symbol, {})
        new = right.get(symbol, {})
        old_status = str(old.get("status") or "MISSING")
        new_status = str(new.get("status") or "MISSING")

        rows.append(
            {
                "symbol": symbol,
                "before_status": old_status,
                "after_status": new_status,
                "changed": old_status != new_status,
                "recovered_from_incomplete": (
                    old_status == "SHARIAH_DATA_INCOMPLETE"
                    and new_status != "SHARIAH_DATA_INCOMPLETE"
                ),
                "after_business_status": new.get("business_status"),
                "after_financial_ratio_status": new.get(
                    "financial_ratio_status"
                ),
                "after_trade_eligible": bool(
                    new.get("trade_eligible", False)
                ),
                "after_fundamentals_source": new.get(
                    "fundamentals_source"
                ),
            }
        )

    frame = pd.DataFrame(rows)

    audit = {
        "schema": "sec_mapping_audit_v2_11",
        "rows": int(len(frame)),
        "changed": int(frame["changed"].sum()) if not frame.empty else 0,
        "recovered_from_incomplete": int(
            frame["recovered_from_incomplete"].sum()
        ) if not frame.empty else 0,
        "remaining_incomplete": int(
            (frame["after_status"] == "SHARIAH_DATA_INCOMPLETE").sum()
        ) if not frame.empty else 0,
        "trade_eligible": int(
            frame["after_trade_eligible"].sum()
        ) if not frame.empty else 0,
        "execution_authority": "NONE",
    }

    return frame, audit
