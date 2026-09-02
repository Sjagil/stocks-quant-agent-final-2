from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import pandas as pd
from .contracts_v2_37 import ShadowDecisionV237, ShadowSide
from .idempotency_v2_37 import deterministic_identifier

@dataclass(frozen=True)
class PortfolioShadowPlanV237:
    status: str
    decisions: tuple[ShadowDecisionV237, ...]
    blockers: tuple[str, ...]
    execution_authority: str = "NONE"
    def as_dict(self):
        return {
            "status": self.status,
            "decisions": [d.as_dict() for d in self.decisions],
            "blockers": list(self.blockers),
            "execution_authority": self.execution_authority,
        }

def build_shadow_plan_from_rebalance(
    current_weights: pd.Series,
    target_weights: pd.Series,
    *,
    portfolio_value: float,
    rebalance_projection,
    strategy_id_by_symbol: dict[str, str],
    family_by_symbol: dict[str, str],
    gross_edge_bps_by_symbol: dict[str, float],
    decision_time: str,
    min_trade_notional: float = 5.0,
) -> PortfolioShadowPlanV237:
    if rebalance_projection.status != "REBALANCE_SHADOW_NET_POSITIVE":
        return PortfolioShadowPlanV237("HOLD_SHADOW", (), tuple(rebalance_projection.blockers))
    idx = current_weights.index.union(target_weights.index)
    cur = current_weights.reindex(idx).fillna(0.0)
    tar = target_weights.reindex(idx).fillna(0.0)
    rows = []
    blockers = []
    for symbol in idx:
        delta = float(tar[symbol] - cur[symbol])
        notional = abs(delta) * float(portfolio_value)
        if notional < min_trade_notional:
            continue
        symbol = str(symbol).upper()
        strategy = strategy_id_by_symbol.get(symbol)
        family = family_by_symbol.get(symbol)
        if not strategy or not family:
            blockers.append(f"MISSING_STRATEGY_METADATA:{symbol}")
            continue
        side = ShadowSide.BUY if delta > 0 else ShadowSide.SELL
        raw_key = f"{strategy}:{symbol}:{decision_time}:{side.value}:PORTFOLIO_REBALANCE"
        rows.append(ShadowDecisionV237(
            deterministic_identifier("DEC", raw_key), strategy, family, symbol, side,
            notional, float(gross_edge_bps_by_symbol.get(symbol, 0.0)), decision_time,
            intent="PORTFOLIO_REBALANCE",
        ))
    return PortfolioShadowPlanV237("PLAN_READY" if rows and not blockers else "PLAN_PARTIAL" if rows else "HOLD_SHADOW", tuple(rows), tuple(blockers))

__all__ = ["PortfolioShadowPlanV237", "build_shadow_plan_from_rebalance"]
