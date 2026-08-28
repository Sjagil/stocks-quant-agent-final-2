from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Mapping
import pandas as pd

from stocks.execution.cost_contracts_v2_36 import MarketStateV236, OrderIntentV236, Side
from stocks.execution.transaction_cost_model_v2_36 import estimate_execution_cost
from stocks.quant.portfolio_metrics import one_way_turnover

@dataclass(frozen=True)
class RebalanceCostProjectionV236:
    turnover: float
    traded_notional: float
    estimated_cost_amount: float
    estimated_cost_bps_of_portfolio: float
    pre_cost_utility_improvement: float
    post_cost_utility_improvement: float
    status: str
    blockers: tuple[str, ...]
    trades: tuple[dict[str, object], ...]
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def project_rebalance_costs(
    current_weights: pd.Series,
    target_weights: pd.Series,
    *,
    portfolio_value: float,
    market_states: Mapping[str, MarketStateV236],
    pre_cost_utility_improvement: float,
) -> RebalanceCostProjectionV236:
    if portfolio_value <= 0:
        raise ValueError("portfolio_value positive")
    idx = current_weights.index.union(target_weights.index)
    current = current_weights.reindex(idx).fillna(0.0)
    target = target_weights.reindex(idx).fillna(0.0)
    turnover = float(one_way_turnover(current, target))
    total_cost = 0.0
    traded_notional = 0.0
    rows = []
    blockers = []
    for symbol in idx:
        delta = float(target[symbol] - current[symbol])
        if abs(delta) <= 1e-12:
            continue
        state = market_states.get(str(symbol))
        if state is None:
            blockers.append(f"MISSING_MARKET_STATE:{symbol}")
            continue
        notional = abs(delta) * portfolio_value
        estimate = estimate_execution_cost(
            OrderIntentV236(
                str(symbol),
                notional,
                Side.BUY if delta > 0 else Side.SELL,
            ),
            state,
        )
        total_cost += estimate.total_cost_amount
        traded_notional += notional
        if estimate.blockers:
            blockers.extend(f"{symbol}:{blocker}" for blocker in estimate.blockers)
        rows.append({
            "symbol": str(symbol),
            "delta_weight": delta,
            "notional": notional,
            "cost_bps": estimate.total_cost_bps,
            "cost_amount": estimate.total_cost_amount,
        })
    cost_bps_portfolio = total_cost / portfolio_value * 10000.0
    post_cost_utility = float(pre_cost_utility_improvement) - total_cost / portfolio_value
    if post_cost_utility <= 0:
        blockers.append("POST_COST_UTILITY_NOT_IMPROVED")
    status = "REBALANCE_SHADOW_NET_POSITIVE" if not blockers else "HOLD_SHADOW_COST_BLOCKED"
    return RebalanceCostProjectionV236(
        turnover,
        traded_notional,
        total_cost,
        cost_bps_portfolio,
        float(pre_cost_utility_improvement),
        post_cost_utility,
        status,
        tuple(dict.fromkeys(blockers)),
        tuple(rows),
    )

__all__ = ["RebalanceCostProjectionV236", "project_rebalance_costs"]
