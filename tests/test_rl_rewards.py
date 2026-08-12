from stocks.rl.config import RewardConfig
from stocks.rl.rewards import calculate_reward


def test_turnover_is_penalized():
    cfg = RewardConfig(transaction_cost_bps=5, slippage_bps=5, turnover_penalty=0.2)
    no_trade = calculate_reward(
        gross_return=0.01,
        old_position=0.5,
        new_position=0.5,
        previous_equity=100.0,
        new_equity_before_penalties=101.0,
        peak_equity=100.0,
        cfg=cfg,
    )
    churn = calculate_reward(
        gross_return=0.01,
        old_position=0.0,
        new_position=1.0,
        previous_equity=100.0,
        new_equity_before_penalties=100.9,
        peak_equity=100.0,
        cfg=cfg,
    )
    assert churn.reward < no_trade.reward
    assert churn.cost > no_trade.cost


def test_drawdown_increment_is_penalized():
    cfg = RewardConfig(drawdown_penalty=1.0)
    result = calculate_reward(
        gross_return=-0.03,
        old_position=1.0,
        new_position=1.0,
        previous_equity=98.0,
        new_equity_before_penalties=95.0,
        peak_equity=100.0,
        cfg=cfg,
    )
    assert result.drawdown_penalty > 0
    assert result.reward < 0
