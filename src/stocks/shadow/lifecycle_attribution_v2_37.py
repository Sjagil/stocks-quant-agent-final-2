from __future__ import annotations
from .attribution_v2_37 import attribute_closed_position
from .feedback_v2_37 import build_shadow_feedback
from .position_state_v2_37 import reduce_position

def closed_trade_feedback(
    ledger,
    position_id: str,
    *,
    forecast_gross_edge_bps: float,
    predicted_round_trip_cost_bps: float,
):
    state = reduce_position(ledger.events(aggregate_type="POSITION", aggregate_id=position_id))
    attribution = attribute_closed_position(state)
    feedback = build_shadow_feedback(
        attribution,
        forecast_gross_edge_bps=forecast_gross_edge_bps,
        predicted_round_trip_cost_bps=predicted_round_trip_cost_bps,
    )
    return attribution, feedback

__all__ = ["closed_trade_feedback"]
