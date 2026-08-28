from __future__ import annotations
from dataclasses import replace
from .cost_contracts_v2_36 import MarketStateV236

def execution_stress_states(state: MarketStateV236) -> dict[str, MarketStateV236]:
    return {
        "BASE": state,
        "WIDE_SPREAD": replace(state, spread_bps=state.spread_bps * 2.0),
        "HIGH_VOL": replace(state, daily_volatility=min(state.daily_volatility * 1.75, 5.0)),
        "OPEN_CLOSE": replace(state, time_of_day_factor=state.time_of_day_factor * 1.50),
        "LIQUIDITY_SHOCK": replace(
            state,
            spread_bps=state.spread_bps * 2.5,
            daily_volatility=min(state.daily_volatility * 1.5, 5.0),
            liquidity_score=max(0.0, state.liquidity_score * 0.60),
            time_of_day_factor=state.time_of_day_factor * 1.35,
        ),
    }

__all__ = ["execution_stress_states"]
