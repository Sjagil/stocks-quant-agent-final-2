from __future__ import annotations
from dataclasses import asdict, dataclass
from .ledger_v2_37 import ShadowLedgerV237
from .order_state_v2_37 import reduce_order
from .position_state_v2_37 import reduce_position

@dataclass(frozen=True)
class ShadowReplaySnapshotV237:
    orders: dict[str, dict]
    positions: dict[str, dict]
    event_count: int
    last_event_hash: str | None
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def replay_shadow_state(ledger: ShadowLedgerV237) -> ShadowReplaySnapshotV237:
    events = ledger.events()
    order_ids = sorted({e.aggregate_id for e in events if e.aggregate_type == "ORDER" and e.event_type == "SHADOW_ORDER_CREATED"})
    position_ids = sorted({e.aggregate_id for e in events if e.aggregate_type == "POSITION" and e.event_type == "POSITION_OPENED"})
    orders = {oid: reduce_order(ledger.events(aggregate_type="ORDER", aggregate_id=oid)).as_dict() for oid in order_ids}
    positions = {pid: reduce_position(ledger.events(aggregate_type="POSITION", aggregate_id=pid)).as_dict() for pid in position_ids}
    return ShadowReplaySnapshotV237(
        orders, positions, len(events), events[-1].event_hash if events else None,
    )

__all__ = ["ShadowReplaySnapshotV237", "replay_shadow_state"]
