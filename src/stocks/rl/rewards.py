from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .config import RewardConfig


@dataclass(frozen=True)
class RewardBreakdown:
    reward: float
    net_log_return: float
    cost: float
    turnover_penalty: float
    downside_penalty: float
    drawdown_penalty: float


def calculate_reward(
    *,
    gross_return: float,
    old_position: float,
    new_position: float,
    previous_equity: float,
    new_equity_before_penalties: float,
    peak_equity: float,
    cfg: RewardConfig,
) -> RewardBreakdown:
    """Risk-aware step reward for long-only swing trading.

    The market return earned during the step is already position-weighted by the
    environment. Trading costs are charged on absolute position turnover.
    """
    if previous_equity <= 0 or new_equity_before_penalties <= 0 or peak_equity <= 0:
        raise ValueError("equity values must be positive")

    turnover = abs(float(new_position) - float(old_position))
    one_way_cost_rate = (cfg.transaction_cost_bps + cfg.slippage_bps) / 10_000.0
    cost = turnover * one_way_cost_rate

    net_simple_return = float(gross_return) - cost
    net_log_return = math.log(max(1e-12, 1.0 + net_simple_return))

    turnover_term = cfg.turnover_penalty * turnover
    downside_term = cfg.downside_penalty * max(0.0, -net_simple_return)

    previous_dd = max(0.0, 1.0 - previous_equity / peak_equity)
    new_dd = max(0.0, 1.0 - new_equity_before_penalties / peak_equity)
    dd_increment = max(0.0, new_dd - previous_dd)
    drawdown_term = cfg.drawdown_penalty * dd_increment

    reward = net_log_return - turnover_term - downside_term - drawdown_term
    reward = float(np.clip(reward, -cfg.reward_clip, cfg.reward_clip))

    return RewardBreakdown(
        reward=reward,
        net_log_return=net_log_return,
        cost=cost,
        turnover_penalty=turnover_term,
        downside_penalty=downside_term,
        drawdown_penalty=drawdown_term,
    )
