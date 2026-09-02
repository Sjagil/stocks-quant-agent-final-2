#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from stocks.orchestration.dynamic_shadow_target_book_v2_26 import (
    DEFAULT_OUTPUT_ROOT,
    ShadowSizingPolicyV226,
    build_dynamic_shadow_target_book_from_project_v226,
    write_dynamic_shadow_target_book_v226,
)
from stocks.orchestration.start_preflight_v2_26 import (
    build_start_preflight_from_project_v226,
)

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_OUTPUT = ROOT / "artifacts/research_runtime/operational_start_preflight_v2_26"


def main() -> int:
    now = datetime.now(UTC)
    preflight = build_start_preflight_from_project_v226(ROOT, decision_time=now)
    PREFLIGHT_OUTPUT.mkdir(parents=True, exist_ok=True)
    (PREFLIGHT_OUTPUT / "audit.json").write_text(
        json.dumps(preflight, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    if not preflight.get("start_ready"):
        print("SHADOW_CYCLE_V2_26", "BLOCKED")
        print("BLOCKERS", "|".join(preflight.get("blockers") or ["UNKNOWN"]))
        print("BROKER_SUBMISSION_ENABLED", False)
        print("ORDER_CALLS", 0)
        print("EXECUTION_AUTHORITY", "NONE")
        return 2

    config = json.loads(
        (ROOT / "config/pit_shariah_portfolio_v2_25_26.json").read_text(encoding="utf-8")
    )
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
        decision_time=now,
        policy=policy,
    )
    output = write_dynamic_shadow_target_book_v226(
        target_book,
        shadow_orders,
        audit,
        ROOT / DEFAULT_OUTPUT_ROOT,
    )
    if not audit.get("ready"):
        print("SHADOW_CYCLE_V2_26", "BLOCKED_AFTER_PREFLIGHT")
        print("BLOCKERS", "|".join(audit.get("blockers") or ["UNKNOWN"]))
        return 2
    print("SHADOW_CYCLE_V2_26", "READY")
    print("TARGET_BOOK_ROWS", len(target_book))
    print("SHADOW_ORDER_ROWS", len(shadow_orders))
    print("TRANSMIT", False)
    print("BROKER_SUBMISSION_ENABLED", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    print("OUTPUT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
