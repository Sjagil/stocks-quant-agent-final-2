from __future__ import annotations

from stocks.portfolio.opportunity_score_v2_30 import OpportunityInputs, opportunity_score


def test_opportunity_score_rewards_edge_and_penalizes_downside():
    good = OpportunityInputs(
        robust_expected_return=0.04,
        q10=-0.02,
        expected_cost=0.002,
        calibration_confidence=0.9,
        stability=0.9,
        regime_fit=0.9,
        liquidity=0.9,
    )
    risky = OpportunityInputs(
        robust_expected_return=0.04,
        q10=-0.10,
        expected_cost=0.002,
        calibration_confidence=0.9,
        stability=0.9,
        regime_fit=0.9,
        liquidity=0.9,
    )
    assert opportunity_score(good) > opportunity_score(risky)
