from __future__ import annotations

from typing import Any

from .state_store_v2_41 import ProductionStoreV241


def ingest_broker_fills(store: ProductionStoreV241, fills: tuple[dict[str, Any], ...]) -> int:
    added = 0
    for fill in fills:
        order_ref = str(fill.get("order_ref", "") or "")
        intent_id = None
        if order_ref.startswith("SQA:"):
            candidate = order_ref[4:]
            if store.intent_exists(candidate):
                intent_id = candidate
        if intent_id is None and fill.get("broker_order_id") is not None:
            intent_id = store.intent_for_order(int(fill["broker_order_id"]))
        payload = dict(fill)
        payload["intent_id"] = intent_id
        if store.record_fill(payload):
            added += 1
    return added


def reconcile(
    store: ProductionStoreV241,
    broker_positions: dict[str, float],
    open_orders: tuple[dict[str, Any], ...],
    *,
    tolerance: float = 1e-8,
) -> dict[str, Any]:
    if not store.get("baseline_adopted", False):
        return {
            "passed": False,
            "blockers": ["BASELINE_NOT_ADOPTED"],
            "position_mismatches": {},
            "unknown_open_orders": [],
        }

    expected = store.expected_positions()
    actual = {s.upper(): float(q) for s, q in broker_positions.items() if abs(float(q)) > tolerance}
    all_symbols = sorted(set(expected) | set(actual))
    mismatches = {
        s: {"expected": expected.get(s, 0.0), "actual": actual.get(s, 0.0)}
        for s in all_symbols
        if abs(expected.get(s, 0.0) - actual.get(s, 0.0)) > tolerance
    }

    known_orders = store.known_order_ids()
    known_intents = store.known_intent_ids()
    unknown_orders = []
    for row in open_orders:
        order_id = int(row.get("order_id", 0) or 0)
        order_ref = str(row.get("order_ref", "") or "")
        if order_id in known_orders:
            continue
        if order_ref.startswith("SQA:") and order_ref[4:] in known_intents:
            continue
        unknown_orders.append(row)

    blockers = []
    if mismatches:
        blockers.append("BROKER_INTERNAL_POSITION_MISMATCH")
    if unknown_orders:
        blockers.append("UNKNOWN_OPEN_BROKER_ORDERS")
    return {
        "passed": not blockers,
        "blockers": blockers,
        "position_mismatches": mismatches,
        "unknown_open_orders": unknown_orders,
        "expected_positions": expected,
        "actual_positions": actual,
    }
