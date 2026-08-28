#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from stocks.orchestration.dynamic_shadow_target_book_v2_26 import (
    DEFAULT_OUTPUT_ROOT,
    ShadowSizingPolicyV226,
    build_dynamic_shadow_target_book_from_project_v226,
    write_dynamic_shadow_target_book_v226,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-time", default=datetime.now(UTC).isoformat())
    parser.add_argument("--broker-snapshot")
    parser.add_argument("--eligibility")
    args = parser.parse_args()
    decision_time = datetime.fromisoformat(args.decision_time.replace("Z", "+00:00"))
    if decision_time.tzinfo is None:
        decision_time = decision_time.replace(tzinfo=UTC)

    config = json.loads((ROOT / "config/pit_shariah_portfolio_v2_25_26.json").read_text(encoding="utf-8"))
    p = config["portfolio"]
    policy = ShadowSizingPolicyV226(
        signal_max_age_seconds=int(p["signal_max_age_seconds"]),
        broker_snapshot_max_age_seconds=int(p["broker_snapshot_max_age_seconds"]),
        maximum_positions=int(p["maximum_positions"]),
        maximum_single_weight=float(p["maximum_single_weight"]),
        maximum_portfolio_heat=float(p["maximum_portfolio_heat"]),
        cash_floor=float(p["cash_floor"]),
        base_risk_fraction=float(p["base_risk_fraction"]),
        strong_risk_fraction=float(p["strong_risk_fraction"]),
        strong_conviction_threshold=float(p["strong_conviction_threshold"]),
        hard_max_risk_fraction=float(p["hard_max_risk_fraction"]),
        atr_period=int(p["atr_period"]),
        stop_atr_multiple=float(p["stop_atr_multiple"]),
        minimum_stop_fraction=float(p["minimum_stop_fraction"]),
        minimum_quantity=int(p["minimum_quantity"]),
        require_flat_broker=bool(p["require_flat_broker_for_initial_shadow"]),
        require_no_open_orders=bool(p["require_no_open_orders"]),
    )
    target_book, shadow_orders, audit = build_dynamic_shadow_target_book_from_project_v226(
        ROOT,
        decision_time=decision_time,
        broker_snapshot_path=args.broker_snapshot,
        eligibility_path=args.eligibility,
        policy=policy,
    )
    output = write_dynamic_shadow_target_book_v226(
        target_book,
        shadow_orders,
        audit,
        ROOT / DEFAULT_OUTPUT_ROOT,
    )
    print(
        "DYNAMIC_SHADOW_TARGET_BOOK_V2_26",
        "READY", audit.get("ready"),
        "SHADOW_READY", audit.get("shadow_ready"),
        "TARGETS", len(target_book),
        "SHADOW_ORDERS", len(shadow_orders),
    )
    if audit.get("blockers"):
        print("BLOCKERS", "|".join(str(v) for v in audit["blockers"]))
    print("BROKER_SUBMISSION_ENABLED", False)
    print("AUTOMATIC_LIVE_PROMOTION", False)
    print("BROKER_CALLS", audit.get("broker_calls", 0))
    print("ORDER_CALLS", audit.get("order_calls", 0))
    print("EXECUTION_AUTHORITY", audit.get("execution_authority", "NONE"))
    print("OUTPUT", output)
    return 0 if audit.get("ready") else 2


if __name__ == "__main__":
    raise SystemExit(main())
