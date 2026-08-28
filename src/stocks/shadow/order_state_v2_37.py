from __future__ import annotations
from dataclasses import asdict, dataclass
from .ledger_v2_37 import ShadowEventV237
from .contracts_v2_37 import ShadowOrderStatus

@dataclass(frozen=True)
class ShadowOrderStateV237:
    order_id: str
    decision_id: str
    strategy_id: str
    family: str
    symbol: str
    side: str
    requested_notional: float
    requested_quantity: float
    filled_quantity: float
    filled_notional: float
    filled_progress_notional: float
    average_fill_price: float
    realized_cost_amount: float
    predicted_cost_bps: float
    status: str
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def reduce_order(events: tuple[ShadowEventV237, ...] | list[ShadowEventV237]) -> ShadowOrderStateV237:
    events = list(events)
    created = next((e for e in events if e.event_type == "SHADOW_ORDER_CREATED"), None)
    if created is None:
        raise ValueError("order has no SHADOW_ORDER_CREATED event")
    p = created.payload
    requested_qty = float(p["requested_quantity"])
    fill_qty = fill_notional = fill_progress = cost = 0.0
    predicted_cost_bps = float(p.get("predicted_cost_bps", 0.0))
    rejected = cancelled = False
    for event in events:
        if event.event_type == "SHADOW_FILL_RECORDED":
            q = float(event.payload["quantity"])
            fill_qty += q
            fill_notional += q * float(event.payload["fill_price"])
            fill_progress += float(event.payload.get("order_progress_notional", q * float(event.payload["fill_price"])))
            cost += float(event.payload.get("explicit_cost_amount", 0.0))
        elif event.event_type == "SHADOW_ORDER_REJECTED":
            rejected = True
        elif event.event_type == "SHADOW_ORDER_CANCELLED":
            cancelled = True
    requested_notional = float(p["requested_notional"])
    if fill_progress > requested_notional * (1.0 + 1e-9):
        raise AssertionError("shadow order overfilled")
    if rejected:
        status = ShadowOrderStatus.REJECTED.value
    elif cancelled:
        status = ShadowOrderStatus.CANCELLED.value
    elif fill_qty <= 1e-12:
        status = ShadowOrderStatus.OPEN.value
    elif fill_progress + max(1e-8, requested_notional * 1e-9) >= requested_notional:
        status = ShadowOrderStatus.FILLED.value
    else:
        status = ShadowOrderStatus.PARTIALLY_FILLED.value
    avg = fill_notional / fill_qty if fill_qty > 0 else 0.0
    return ShadowOrderStateV237(
        created.aggregate_id, str(p["decision_id"]), str(p["strategy_id"]), str(p["family"]),
        str(p["symbol"]), str(p["side"]), float(p["requested_notional"]), requested_qty,
        fill_qty, fill_notional, fill_progress, avg, cost, predicted_cost_bps, status,
    )

__all__ = ["ShadowOrderStateV237", "reduce_order"]
