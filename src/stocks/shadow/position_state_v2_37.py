from __future__ import annotations
from dataclasses import asdict, dataclass
from .ledger_v2_37 import ShadowEventV237

@dataclass(frozen=True)
class ShadowPositionStateV237:
    position_id: str
    strategy_id: str
    family: str
    symbol: str
    quantity: float
    average_entry_price: float
    average_entry_reference_price: float
    entry_notional: float
    entry_explicit_cost_amount: float
    entry_implementation_shortfall_amount: float
    exit_explicit_cost_amount: float
    exit_implementation_shortfall_amount: float
    last_price: float
    high_price: float
    low_price: float
    mfe_bps: float
    mae_bps: float
    bars_held: int
    status: str
    exit_reason: str | None
    realized_reference_gross_pnl: float
    realized_fill_pnl: float
    realized_net_pnl: float
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def reduce_position(events: tuple[ShadowEventV237, ...] | list[ShadowEventV237]) -> ShadowPositionStateV237:
    events = list(events)
    opened = next((e for e in events if e.event_type == "POSITION_OPENED"), None)
    if opened is None:
        raise ValueError("position has no POSITION_OPENED event")
    p = opened.payload
    qty = float(p["quantity"])
    avg_fill = float(p["entry_price"])
    avg_ref = float(p.get("reference_price", avg_fill))
    entry_fill_notional = qty * avg_fill
    entry_ref_notional = qty * avg_ref
    entry_explicit = float(p.get("entry_explicit_cost_amount", p.get("entry_cost_amount", 0.0)))
    entry_is = float(p.get("entry_implementation_shortfall_amount", entry_explicit))
    last = high = low = avg_fill
    bars = 0
    exit_explicit = exit_is = 0.0
    fill_pnl = reference_gross = 0.0
    exit_reason = None
    status = "OPEN"
    for event in events:
        ep = event.payload
        if event.event_type == "POSITION_INCREASED":
            q = float(ep["quantity"])
            fill_price = float(ep["entry_price"])
            ref_price = float(ep.get("reference_price", fill_price))
            new_fill_notional = entry_fill_notional + q * fill_price
            new_ref_notional = entry_ref_notional + q * ref_price
            qty += q
            entry_fill_notional = new_fill_notional
            entry_ref_notional = new_ref_notional
            avg_fill = new_fill_notional / qty
            avg_ref = new_ref_notional / qty
            entry_explicit += float(ep.get("entry_explicit_cost_amount", ep.get("entry_cost_amount", 0.0)))
            entry_is += float(ep.get("entry_implementation_shortfall_amount", 0.0))
        elif event.event_type == "POSITION_MARK":
            last = float(ep["price"])
            high = max(high, last)
            low = min(low, last)
            bars = max(bars, int(ep.get("bars_held", bars)))
        elif event.event_type == "EXIT_REQUESTED":
            status = "EXIT_PENDING"
            exit_reason = str(ep["reason"])
        elif event.event_type in {"POSITION_REDUCED", "POSITION_CLOSED"}:
            q = min(float(ep["quantity"]), qty)
            fill_price = float(ep["exit_price"])
            ref_price = float(ep.get("reference_price", fill_price))
            fill_pnl += (fill_price - avg_fill) * q
            reference_gross += (ref_price - avg_ref) * q
            exit_explicit += float(ep.get("exit_explicit_cost_amount", ep.get("exit_cost_amount", 0.0)))
            exit_is += float(ep.get("exit_implementation_shortfall_amount", 0.0))
            qty -= q
            qty = max(qty, 0.0)
            last = fill_price
            if event.event_type == "POSITION_CLOSED":
                status = "CLOSED"
                exit_reason = str(ep.get("reason") or exit_reason or "UNKNOWN")
    mfe = round((high / avg_fill - 1.0) * 10000.0, 10) if avg_fill > 0 else 0.0
    mae = round((low / avg_fill - 1.0) * 10000.0, 10) if avg_fill > 0 else 0.0
    net = fill_pnl - entry_explicit - exit_explicit
    # Reference-price gross minus implementation shortfall should equal fill-based net,
    # modulo numerical rounding.
    if status == "CLOSED" and abs((reference_gross - entry_is - exit_is) - net) > max(1e-6, abs(net) * 1e-8):
        raise AssertionError("implementation-shortfall accounting identity failed")
    return ShadowPositionStateV237(
        opened.aggregate_id, str(p["strategy_id"]), str(p["family"]), str(p["symbol"]),
        qty, avg_fill, avg_ref, entry_ref_notional, entry_explicit, entry_is,
        exit_explicit, exit_is, last, high, low, mfe, mae, bars, status, exit_reason,
        reference_gross, fill_pnl, net,
    )

__all__ = ["ShadowPositionStateV237", "reduce_position"]
