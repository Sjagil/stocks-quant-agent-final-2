from __future__ import annotations
from dataclasses import asdict, dataclass
from .ledger_v2_37 import ShadowLedgerV237
from .order_state_v2_37 import reduce_order
from .position_state_v2_37 import reduce_position

@dataclass(frozen=True)
class ShadowReconciliationV237:
    status: str
    event_count: int
    orders: int
    positions: int
    open_positions: int
    blockers: tuple[str, ...]
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def reconcile_shadow_ledger(ledger: ShadowLedgerV237) -> ShadowReconciliationV237:
    blockers = []
    if not ledger.verify_hash_chain():
        blockers.append("EVENT_HASH_CHAIN_INVALID")
    all_events = ledger.events()
    order_ids = sorted({e.aggregate_id for e in all_events if e.aggregate_type == "ORDER"})
    position_ids = sorted({e.aggregate_id for e in all_events if e.aggregate_type == "POSITION"})
    seen_keys = {}
    for event in all_events:
        if event.event_type == "SHADOW_ORDER_CREATED" and event.idempotency_key:
            existing = seen_keys.get(event.idempotency_key)
            if existing is not None and existing != event.aggregate_id:
                blockers.append("DUPLICATE_IDEMPOTENCY_KEY")
            seen_keys[event.idempotency_key] = event.aggregate_id
    for oid in order_ids:
        try:
            state = reduce_order(ledger.events(aggregate_type="ORDER", aggregate_id=oid))
            if state.filled_progress_notional > state.requested_notional * (1.0 + 1e-9):
                blockers.append(f"ORDER_OVERFILLED:{oid}")
        except Exception:
            blockers.append(f"ORDER_STATE_INVALID:{oid}")
    open_positions = 0
    for pid in position_ids:
        try:
            state = reduce_position(ledger.events(aggregate_type="POSITION", aggregate_id=pid))
            if state.quantity < -1e-9:
                blockers.append(f"NEGATIVE_POSITION:{pid}")
            if state.status != "CLOSED":
                open_positions += 1
        except Exception:
            blockers.append(f"POSITION_STATE_INVALID:{pid}")
    return ShadowReconciliationV237(
        "READY" if not blockers else "BLOCKED",
        len(all_events), len(order_ids), len(position_ids), open_positions,
        tuple(dict.fromkeys(blockers)),
    )

__all__ = ["ShadowReconciliationV237", "reconcile_shadow_ledger"]
