from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone

from stocks.execution.cost_contracts_v2_36 import OrderIntentV236, OrderStyle, Side
from stocks.execution.execution_simulator_v2_36 import simulate_execution
from stocks.execution.transaction_cost_model_v2_36 import estimate_execution_cost

from .contracts_v2_37 import ExitPolicyV237, ShadowDecisionV237, ShadowSide
from .exits_v2_37 import evaluate_exit
from .fill_engine_v2_37 import deterministic_shadow_fill
from .idempotency_v2_37 import canonical_idempotency_key, deterministic_identifier
from .ledger_v2_37 import ShadowLedgerV237
from .order_state_v2_37 import reduce_order
from .position_state_v2_37 import reduce_position

def _event_time(value: str | None = None) -> str:
    if value:
        return str(value)
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

@dataclass(frozen=True)
class EntrySubmissionV237:
    status: str
    decision_id: str
    order_id: str | None
    idempotency_key: str
    blockers: tuple[str, ...]
    predicted_round_trip_cost_bps: float | None
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

class ShadowLifecycleEngineV237:
    def __init__(self, ledger_path: str | Path):
        self.ledger = ShadowLedgerV237(ledger_path)

    def close(self):
        self.ledger.close()

    def submit_entry(self, decision: ShadowDecisionV237, market_state) -> EntrySubmissionV237:
        if decision.side is not ShadowSide.BUY:
            raise ValueError("submit_entry accepts BUY decisions only; exits/reductions use risk-exit path")
        key = canonical_idempotency_key(decision)
        prior = self.ledger.events_for_idempotency(key)
        created = next((e for e in prior if e.event_type == "SHADOW_ORDER_CREATED"), None)
        rejected = next((e for e in prior if e.event_type == "DECISION_REJECTED"), None)
        if created:
            return EntrySubmissionV237("IDEMPOTENT_EXISTING", decision.decision_id, created.aggregate_id, key, (), float(created.payload.get("predicted_round_trip_cost_bps", 0.0)))
        if rejected:
            return EntrySubmissionV237("IDEMPOTENT_REJECTED", decision.decision_id, None, key, tuple(rejected.payload.get("blockers", [])), rejected.payload.get("predicted_round_trip_cost_bps"))
        intent = OrderIntentV236(decision.symbol, decision.target_notional, Side.BUY, OrderStyle.MARKET, 0.5)
        research = simulate_execution(intent, market_state, gross_edge_bps=decision.gross_edge_bps)
        edge = research.edge_decision
        t = decision.decision_time
        if edge["status"] != "EXECUTABLE_RESEARCH":
            self.ledger.append(
                event_id=deterministic_identifier("EVT", f"{key}:REJECT"),
                aggregate_type="DECISION", aggregate_id=decision.decision_id,
                event_type="DECISION_REJECTED",
                payload={"decision": decision.as_dict(), "blockers": list(edge["blockers"]), "predicted_round_trip_cost_bps": research.round_trip_cost_bps},
                event_time=t, idempotency_key=key,
            )
            return EntrySubmissionV237("REJECTED", decision.decision_id, None, key, tuple(edge["blockers"]), research.round_trip_cost_bps)
        self.ledger.append(
            event_id=deterministic_identifier("EVT", f"{key}:ACCEPT"),
            aggregate_type="DECISION", aggregate_id=decision.decision_id,
            event_type="DECISION_ACCEPTED", payload={"decision": decision.as_dict(), "edge_decision": edge},
            event_time=t, idempotency_key=key,
        )
        order_id = deterministic_identifier("ORD", key)
        requested_qty = decision.target_notional / float(market_state.price)
        self.ledger.append(
            event_id=deterministic_identifier("EVT", f"{key}:ORDER"),
            aggregate_type="ORDER", aggregate_id=order_id, event_type="SHADOW_ORDER_CREATED",
            payload={
                "decision_id": decision.decision_id, "strategy_id": decision.strategy_id, "family": decision.family,
                "symbol": decision.symbol, "side": decision.side.value, "requested_notional": decision.target_notional,
                "requested_quantity": requested_qty, "gross_edge_bps": decision.gross_edge_bps,
                "predicted_round_trip_cost_bps": research.round_trip_cost_bps,
                "stop_loss_pct": decision.stop_loss_pct, "take_profit_pct": decision.take_profit_pct,
                "trailing_stop_pct": decision.trailing_stop_pct, "expected_horizon_bars": decision.expected_horizon_bars,
                "order_style": research.style_comparison.get("preferred_style", "MARKET"),
            },
            event_time=t, idempotency_key=key,
        )
        return EntrySubmissionV237("ORDER_CREATED", decision.decision_id, order_id, key, (), research.round_trip_cost_bps)

    def fill_entry(self, order_id: str, market_state, *, fill_time: str, force_fill_fraction: float | None = None):
        events = self.ledger.events(aggregate_type="ORDER", aggregate_id=order_id)
        state = reduce_order(events)
        if state.side != "BUY":
            raise ValueError("fill_entry requires BUY order")
        remaining_notional = max(state.requested_notional - state.filled_progress_notional, 0.0)
        if remaining_notional <= 1e-12:
            return state
        fill = deterministic_shadow_fill(
            order_id=order_id, symbol=state.symbol, side=ShadowSide.BUY,
            requested_notional=state.requested_notional, remaining_notional=remaining_notional,
            market_state=market_state, fill_time=fill_time,
            force_fill_fraction=force_fill_fraction,
        )
        self.ledger.append(
            event_id=fill.fill_id, aggregate_type="ORDER", aggregate_id=order_id,
            event_type="SHADOW_FILL_RECORDED", payload=fill.as_dict(), event_time=fill.fill_time,
        )
        position_id = deterministic_identifier("POS", order_id)
        position_events = self.ledger.events(aggregate_type="POSITION", aggregate_id=position_id)
        event_type = "POSITION_OPENED" if not position_events else "POSITION_INCREASED"
        self.ledger.append(
            event_id=deterministic_identifier("EVT", f"{fill.fill_id}:{event_type}"),
            aggregate_type="POSITION", aggregate_id=position_id, event_type=event_type,
            payload={
                "strategy_id": state.strategy_id, "family": state.family, "symbol": state.symbol,
                "quantity": fill.quantity, "entry_price": fill.fill_price, "reference_price": fill.reference_price,
                "entry_explicit_cost_amount": fill.explicit_cost_amount,
                "entry_implementation_shortfall_amount": fill.implicit_cost_amount + fill.explicit_cost_amount,
                "source_order_id": order_id,
            },
            event_time=fill.fill_time,
        )
        return reduce_order(self.ledger.events(aggregate_type="ORDER", aggregate_id=order_id))

    def mark_position(self, position_id: str, *, price: float, bars_held: int, mark_time: str):
        if price <= 0 or bars_held < 0:
            raise ValueError("invalid mark")
        self.ledger.append(
            event_id=deterministic_identifier("EVT", f"{position_id}:MARK:{mark_time}:{price}:{bars_held}"),
            aggregate_type="POSITION", aggregate_id=position_id, event_type="POSITION_MARK",
            payload={"price": float(price), "bars_held": int(bars_held)}, event_time=mark_time,
        )
        return reduce_position(self.ledger.events(aggregate_type="POSITION", aggregate_id=position_id))

    def evaluate_and_exit(
        self,
        position_id: str,
        market_state,
        *,
        bars_held: int,
        event_time: str,
        strategy_exit: bool = False,
        force_exit: bool = False,
    ):
        position = self.mark_position(position_id, price=float(market_state.price), bars_held=bars_held, mark_time=event_time)
        if position.status == "CLOSED":
            return position
        position_events = self.ledger.events(aggregate_type="POSITION", aggregate_id=position_id)
        opened_position = next(e for e in position_events if e.event_type == "POSITION_OPENED")
        entry_order_id = str(opened_position.payload["source_order_id"])
        opened_order = next(
            (e for e in self.ledger.events(aggregate_type="ORDER", aggregate_id=entry_order_id)
             if e.event_type == "SHADOW_ORDER_CREATED"),
            None,
        )
        if opened_order is None:
            raise ValueError("cannot resolve entry order metadata")
        op = opened_order.payload
        policy = ExitPolicyV237(
            stop_loss_pct=float(op.get("stop_loss_pct", 0.03)),
            take_profit_pct=op.get("take_profit_pct"),
            trailing_stop_pct=op.get("trailing_stop_pct"),
            max_holding_bars=int(op.get("expected_horizon_bars", 40)),
        )
        exit_decision = evaluate_exit(
            entry_price=position.average_entry_price, current_price=float(market_state.price),
            high_price=position.high_price, bars_held=bars_held, strategy_exit=strategy_exit, policy=policy,
        )
        reason = "FORCED_EXIT" if force_exit else exit_decision.reason
        if not force_exit and not exit_decision.should_exit:
            return position
        exit_key = f"{position_id}:{reason}"
        exit_order_id = deterministic_identifier("XORD", exit_key)
        existing = self.ledger.events(aggregate_type="ORDER", aggregate_id=exit_order_id)
        if existing:
            return reduce_position(self.ledger.events(aggregate_type="POSITION", aggregate_id=position_id))
        self.ledger.append(
            event_id=deterministic_identifier("EVT", f"{exit_key}:REQUEST"),
            aggregate_type="POSITION", aggregate_id=position_id, event_type="EXIT_REQUESTED",
            payload={"reason": reason}, event_time=event_time,
        )
        notional = position.quantity * float(market_state.price)
        estimate = estimate_execution_cost(
            OrderIntentV236(position.symbol, notional, Side.SELL, OrderStyle.MARKET, 1.0),
            market_state,
        )
        self.ledger.append(
            event_id=deterministic_identifier("EVT", f"{exit_key}:ORDER"),
            aggregate_type="ORDER", aggregate_id=exit_order_id, event_type="SHADOW_ORDER_CREATED",
            payload={
                "decision_id": f"EXIT:{position_id}", "strategy_id": position.strategy_id, "family": position.family,
                "symbol": position.symbol, "side": "SELL", "requested_notional": notional,
                "requested_quantity": position.quantity, "predicted_cost_bps": estimate.total_cost_bps,
                "predicted_round_trip_cost_bps": estimate.total_cost_bps, "order_style": "MARKET",
            },
            event_time=event_time, idempotency_key=exit_key,
        )
        fill = deterministic_shadow_fill(
            order_id=exit_order_id, symbol=position.symbol, side=ShadowSide.SELL,
            requested_notional=notional, remaining_notional=notional, target_quantity=position.quantity,
            market_state=market_state, fill_time=event_time, urgency=1.0, force_fill_fraction=1.0,
        )
        self.ledger.append(
            event_id=fill.fill_id, aggregate_type="ORDER", aggregate_id=exit_order_id,
            event_type="SHADOW_FILL_RECORDED", payload=fill.as_dict(), event_time=event_time,
        )
        self.ledger.append(
            event_id=deterministic_identifier("EVT", f"{fill.fill_id}:CLOSE"),
            aggregate_type="POSITION", aggregate_id=position_id, event_type="POSITION_CLOSED",
            payload={
                "quantity": position.quantity, "exit_price": fill.fill_price, "reference_price": fill.reference_price,
                "exit_explicit_cost_amount": fill.explicit_cost_amount,
                "exit_implementation_shortfall_amount": fill.implicit_cost_amount + fill.explicit_cost_amount,
                "reason": reason, "source_order_id": exit_order_id,
            },
            event_time=event_time,
        )
        return reduce_position(self.ledger.events(aggregate_type="POSITION", aggregate_id=position_id))

__all__ = ["EntrySubmissionV237", "ShadowLifecycleEngineV237"]
