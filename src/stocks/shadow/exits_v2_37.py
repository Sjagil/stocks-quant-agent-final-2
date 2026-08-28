from __future__ import annotations
from dataclasses import asdict, dataclass
from .contracts_v2_37 import ExitPolicyV237

@dataclass(frozen=True)
class ExitDecisionV237:
    should_exit: bool
    reason: str | None
    stop_price: float
    take_profit_price: float | None
    trailing_stop_price: float | None
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def evaluate_exit(
    *,
    entry_price: float,
    current_price: float,
    high_price: float,
    bars_held: int,
    strategy_exit: bool = False,
    policy: ExitPolicyV237 | None = None,
) -> ExitDecisionV237:
    cfg = policy or ExitPolicyV237()
    stop = entry_price * (1.0 - cfg.stop_loss_pct)
    take = None if cfg.take_profit_pct is None else entry_price * (1.0 + cfg.take_profit_pct)
    trail = None if cfg.trailing_stop_pct is None else high_price * (1.0 - cfg.trailing_stop_pct)
    reason = None
    if current_price <= stop:
        reason = "STOP_LOSS"
    elif trail is not None and high_price > entry_price and current_price <= trail:
        reason = "TRAILING_STOP"
    elif take is not None and current_price >= take:
        reason = "TAKE_PROFIT"
    elif strategy_exit:
        reason = "STRATEGY_EXIT"
    elif bars_held >= cfg.max_holding_bars:
        reason = "TIME_EXIT"
    return ExitDecisionV237(reason is not None, reason, stop, take, trail)

__all__ = ["ExitDecisionV237", "evaluate_exit"]
