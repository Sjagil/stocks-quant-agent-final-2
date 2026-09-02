from __future__ import annotations
from typing import Mapping
import numpy as np
import pandas as pd

from stocks.execution.break_even_v2_36 import executable_edge_gate
from stocks.execution.cost_contracts_v2_36 import MarketStateV236, OrderIntentV236
from stocks.execution.transaction_cost_model_v2_36 import estimate_execution_cost

def apply_execution_economics_to_gems(
    shortlist: pd.DataFrame,
    market_states: Mapping[str, MarketStateV236],
    *,
    research_notional: float = 10_000.0,
) -> pd.DataFrame:
    frame = shortlist.copy()
    rows = []
    for _, row in frame.iterrows():
        symbol = str(row["symbol"]).upper()
        state = market_states.get(symbol)
        if state is None:
            rows.append({
                "execution_cost_bps": np.nan, "gross_forecast_edge_bps": np.nan,
                "net_edge_bps": np.nan, "execution_status": "MISSING_MARKET_STATE",
                "execution_blockers": "MISSING_MARKET_STATE",
            })
            continue
        gross = float(row.get("forecast_mean", np.nan)) * 10000.0
        if not np.isfinite(gross):
            rows.append({
                "execution_cost_bps": np.nan, "gross_forecast_edge_bps": np.nan,
                "net_edge_bps": np.nan, "execution_status": "MISSING_FORECAST",
                "execution_blockers": "MISSING_FORECAST",
            })
            continue
        notional = min(float(research_notional), state.adv20_notional * 0.025)
        estimate = estimate_execution_cost(OrderIntentV236(symbol, notional), state)
        round_trip_cost = estimate.total_cost_bps * 2.0
        decision = executable_edge_gate(
            gross_edge_bps=gross,
            expected_cost_bps=round_trip_cost,
            hard_blockers=estimate.blockers,
        )
        rows.append({
            "execution_cost_bps": round_trip_cost,
            "gross_forecast_edge_bps": gross,
            "net_edge_bps": decision.net_edge_bps,
            "execution_status": decision.status,
            "execution_blockers": "|".join(decision.blockers),
        })
    extra = pd.DataFrame(rows, index=frame.index)
    out = pd.concat([frame, extra], axis=1)
    if "gem_score" in out.columns:
        net_rank = out["net_edge_bps"].rank(pct=True).fillna(0.0)
        status_multiplier = out["execution_status"].eq("EXECUTABLE_RESEARCH").map({True: 1.0, False: 0.35})
        out["execution_adjusted_gem_score"] = (
            out["gem_score"] * (0.70 + 0.30 * net_rank) * status_multiplier
        )
        out = out.sort_values(
            ["execution_status", "execution_adjusted_gem_score", "symbol"],
            ascending=[True, False, True],
        ).reset_index(drop=True)
    return out

__all__ = ["apply_execution_economics_to_gems"]
