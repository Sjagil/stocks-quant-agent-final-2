from __future__ import annotations

import math

import numpy as np
import pandas as pd

from stocks.quant.factors import (
    average_pairwise_correlation,
    factor_beta,
    residual_returns,
)
from stocks.quant.kelly import (
    binary_kelly,
    continuous_kelly,
    fractional_kelly,
    multi_asset_kelly,
)
from stocks.quant.liquidity import (
    amihud_illiquidity,
    implementation_shortfall,
    participation_rate,
    square_root_impact,
)
from stocks.quant.portfolio_utility import UtilityPenalties, portfolio_utility


def test_liquidity_and_impact_primitives():
    returns = pd.Series([0.01, -0.02, 0.005])
    dv = pd.Series([1_000_000, 2_000_000, 1_500_000])
    assert amihud_illiquidity(returns, dv) > 0
    assert math.isclose(participation_rate(1000, 100_000), 0.01)
    assert square_root_impact(volatility=0.02, order_volume=1000, market_volume=100_000) > 0
    assert implementation_shortfall(
        decision_price=100,
        execution_price=100.2,
        side="BUY",
    ) > 0


def test_factor_beta_and_residuals():
    factor = pd.Series(np.linspace(-0.02, 0.02, 100))
    asset = 1.5 * factor + 0.001
    assert math.isclose(factor_beta(asset, factor), 1.5, rel_tol=1e-10)
    residual = residual_returns(asset, pd.DataFrame({"market": factor}))
    assert residual.dropna().abs().max() < 1e-10
    frame = pd.DataFrame({"a": factor, "b": factor * 2, "c": -factor})
    assert average_pairwise_correlation(frame) < 1.0


def test_kelly_primitives_are_fractional_and_bounded():
    full = binary_kelly(win_probability=0.55, payoff_ratio=1.5)
    assert full > 0
    assert math.isclose(fractional_kelly(full, multiplier=0.25), 0.25 * full)
    assert continuous_kelly(expected_excess_return=0.02, variance=0.04) == 0.5
    cov = pd.DataFrame([[0.04, 0.0], [0.0, 0.01]], index=["A", "B"], columns=["A", "B"])
    weights = multi_asset_kelly(pd.Series({"A": 0.02, "B": 0.01}), cov, fraction=0.25, max_total_weight=0.6)
    assert weights.ge(0).all()
    assert weights.sum() <= 0.6 + 1e-12


def test_portfolio_utility_penalizes_concentration_and_risk():
    cov = pd.DataFrame([[0.04, 0.01], [0.01, 0.02]], index=["A", "B"], columns=["A", "B"])
    mu = pd.Series({"A": 0.05, "B": 0.04})
    diversified = pd.Series({"A": 0.3, "B": 0.3})
    concentrated = pd.Series({"A": 0.6, "B": 0.0})
    penalties = UtilityPenalties(variance=1.0, concentration=0.2)
    assert portfolio_utility(
        weights=diversified, expected_net_returns=mu, covariance=cov, penalties=penalties
    ) > portfolio_utility(
        weights=concentrated, expected_net_returns=mu, covariance=cov, penalties=penalties
    )
