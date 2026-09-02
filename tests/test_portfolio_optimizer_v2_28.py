from __future__ import annotations

import importlib.util
import math

import numpy as np
import pandas as pd
import pytest

from stocks.portfolio.expected_returns_v2_28 import ForwardDistribution
from stocks.portfolio.optimizer_v2_28 import (
    OptimizerConstraints,
    mean_cvar_weights,
    minimum_variance_weights,
    risk_budgeting_weights,
)
from stocks.quant.covariance import shrink_covariance


CVXPY_AVAILABLE = importlib.util.find_spec("cvxpy") is not None
pytestmark = pytest.mark.skipif(not CVXPY_AVAILABLE, reason="cvxpy optional dependency not installed")


def _data():
    rng = np.random.default_rng(9)
    returns = pd.DataFrame(
        rng.normal(
            loc=[0.0005, 0.00035, 0.0002],
            scale=[0.015, 0.010, 0.006],
            size=(500, 3),
        ),
        columns=["A", "B", "C"],
    )
    return returns


def _assert_feasible(result, constraints):
    weights = pd.Series(result.weights, dtype=float)
    assert result.execution_authority == "NONE"
    assert weights.ge(-1e-8).all()
    assert weights.le(constraints.max_position_weight + 1e-6).all()
    assert weights.sum() <= constraints.max_total_weight + 1e-6


def test_minvar_mean_cvar_and_risk_budgeting_are_feasible():
    returns = _data()
    cov = shrink_covariance(returns)
    constraints = OptimizerConstraints(max_total_weight=0.60, max_position_weight=0.30)
    minvar = minimum_variance_weights(cov, constraints=constraints)
    meancvar = mean_cvar_weights(
        pd.Series({"A": 0.03, "B": 0.025, "C": 0.015}),
        returns,
        constraints=constraints,
    )
    riskbudget = risk_budgeting_weights(cov, constraints=constraints)
    for result in (minvar, meancvar, riskbudget):
        assert "optimal" in result.status.lower()
        _assert_feasible(result, constraints)


def test_forward_distribution_score_penalizes_uncertainty_and_downside():
    stable = ForwardDistribution(
        mean=0.04, uncertainty=0.01, q10=-0.02, q50=0.035, q90=0.09,
        expected_cost=0.002, calibration_confidence=0.9, stability=0.9,
        regime_fit=0.9, liquidity=0.9,
    )
    noisy = ForwardDistribution(
        mean=0.04, uncertainty=0.03, q10=-0.08, q50=0.035, q90=0.15,
        expected_cost=0.002, calibration_confidence=0.9, stability=0.9,
        regime_fit=0.9, liquidity=0.9,
    )
    assert stable.opportunity_score() > noisy.opportunity_score()
