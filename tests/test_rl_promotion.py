from stocks.rl.promotion import (
    evaluate_promotion,
)


PROMOTION = {
    "minimum_closed_forward_episodes": 500,
    "minimum_oos_profit_factor": 1.15,
    "maximum_oos_drawdown": 0.15,
}


def test_absolute_edge_without_benchmark_edge_is_not_candidate():
    row = {
        "algorithm": "SAC",
        "symbol": "SPY",
        "timeframe": "1h",
        "median_rl_return": 0.07,
        "median_rl_sharpe": 1.12,
        "worst_rl_drawdown": 0.10,
        "positive_fold_ratio": 1.0,
        "beat_buy_hold_return_ratio": 0.0,
        "beat_buy_hold_sharpe_ratio": 0.0,
    }

    decision = evaluate_promotion(
        row,
        PROMOTION,
    )

    assert decision.absolute_edge_gate
    assert not decision.benchmark_edge_gate
    assert not decision.research_candidate
    assert not decision.promotion_ready


def test_research_candidate_is_not_live_promotion():
    row = {
        "algorithm": "PPO",
        "symbol": "AMD",
        "timeframe": "1h",
        "median_rl_return": 0.01,
        "median_rl_sharpe": 0.75,
        "worst_rl_drawdown": 0.01,
        "positive_fold_ratio": 1.0,
        "beat_buy_hold_return_ratio": 0.5,
        "beat_buy_hold_sharpe_ratio": 0.5,
    }

    decision = evaluate_promotion(
        row,
        PROMOTION,
    )

    assert decision.research_candidate
    assert not decision.promotion_ready
    assert (
        "INSUFFICIENT_FORWARD_EPISODES"
        in decision.reasons
    )
