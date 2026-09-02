from __future__ import annotations
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class ShadowFeedbackV237:
    position_id: str
    strategy_id: str
    symbol: str
    forecast_gross_edge_bps: float
    realized_gross_return_bps: float
    realized_net_return_bps: float
    forecast_error_bps: float
    predicted_round_trip_cost_bps: float
    realized_cost_bps: float
    cost_prediction_error_bps: float
    mfe_bps: float
    mae_bps: float
    bars_held: int
    exit_reason: str
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def build_shadow_feedback(
    attribution,
    *,
    forecast_gross_edge_bps: float,
    predicted_round_trip_cost_bps: float,
) -> ShadowFeedbackV237:
    realized_cost_bps = float(attribution.implementation_shortfall_bps)
    return ShadowFeedbackV237(
        attribution.position_id, attribution.strategy_id, attribution.symbol,
        float(forecast_gross_edge_bps), float(attribution.gross_return_bps),
        float(attribution.net_return_bps),
        float(attribution.gross_return_bps - forecast_gross_edge_bps),
        float(predicted_round_trip_cost_bps), float(realized_cost_bps),
        float(realized_cost_bps - predicted_round_trip_cost_bps),
        float(attribution.mfe_bps), float(attribution.mae_bps),
        int(attribution.bars_held), attribution.exit_reason,
    )

__all__ = ["ShadowFeedbackV237", "build_shadow_feedback"]
