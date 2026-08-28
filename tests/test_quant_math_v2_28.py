from __future__ import annotations

import math

import numpy as np
import pandas as pd

from stocks.quant.covariance import (
    effective_number_of_positions,
    entropy_effective_number,
    portfolio_volatility,
    risk_contribution,
    shrink_covariance,
)
from stocks.quant.drawdown import drawdown_series, max_drawdown, ulcer_index
from stocks.quant.normalization import robust_zscore
from stocks.quant.portfolio_metrics import profit_factor, trade_expectancy, one_way_turnover
from stocks.quant.position_sizing import (
    fixed_fractional_risk_budget,
    portfolio_heat,
    stop_based_quantity,
)
from stocks.quant.returns import (
    cumulative_return,
    forward_simple_returns,
    log_returns,
    simple_returns,
    wealth_index,
)
from stocks.quant.statistical_validation import (
    minimum_track_record_length,
    probabilistic_sharpe_ratio,
)
from stocks.quant.tail_risk import expected_shortfall, historical_var
from stocks.quant.volatility import atr, garman_klass_volatility, parkinson_volatility


def test_return_identities_and_forward_tail():
    prices = pd.Series([100.0, 101.0, 99.0, 103.0, 104.0, 108.0])
    simple = simple_returns(prices)
    logs = log_returns(prices)
    assert np.allclose(np.log1p(simple.dropna()), logs.dropna())
    assert math.isclose(cumulative_return(simple), 0.08, rel_tol=0, abs_tol=1e-12)
    forward = forward_simple_returns(prices, [2])
    assert math.isclose(forward["fwd_return_2"].iloc[0], -0.01, abs_tol=1e-12)
    assert forward["fwd_return_2"].iloc[-2:].isna().all()


def test_wealth_drawdown_and_ulcer():
    wealth = pd.Series([100.0, 110.0, 99.0, 105.0, 88.0, 120.0])
    dd = drawdown_series(wealth)
    assert math.isclose(dd.iloc[2], 0.10, abs_tol=1e-12)
    assert math.isclose(max_drawdown(wealth), 0.20, abs_tol=1e-12)
    assert ulcer_index(wealth) > 0


def test_tail_risk_is_positive_loss_measure():
    returns = pd.Series([-0.10, -0.05, -0.02, 0.0, 0.01, 0.02, 0.03] * 20)
    var = historical_var(returns, alpha=0.95)
    es = expected_shortfall(returns, alpha=0.95)
    assert var >= 0
    assert es >= var


def test_range_volatility_and_atr():
    frame = pd.DataFrame({
        "open": [100, 102, 101, 104, 105] * 4,
        "high": [103, 104, 105, 107, 108] * 4,
        "low": [99, 100, 100, 102, 103] * 4,
        "close": [102, 101, 104, 105, 107] * 4,
    })
    assert atr(frame, 3).dropna().gt(0).all()
    assert parkinson_volatility(frame) > 0
    assert garman_klass_volatility(frame) >= 0


def test_covariance_risk_contribution_identity():
    rng = np.random.default_rng(42)
    returns = pd.DataFrame(rng.normal(size=(400, 4)) * 0.01, columns=list("ABCD"))
    cov = shrink_covariance(returns, method="ledoit_wolf")
    weights = pd.Series([0.15, 0.15, 0.15, 0.15], index=cov.columns)
    vol = portfolio_volatility(weights, cov)
    rc = risk_contribution(weights, cov)
    assert math.isclose(float(rc.sum()), vol, rel_tol=1e-8, abs_tol=1e-10)
    assert math.isclose(effective_number_of_positions(weights), 4.0, abs_tol=1e-10)
    assert math.isclose(entropy_effective_number(weights), 4.0, abs_tol=1e-10)


def test_sizing_and_heat():
    assert fixed_fractional_risk_budget(10_000, 0.007) == 70.0
    assert stop_based_quantity(
        equity=10_000,
        risk_fraction=0.007,
        entry_price=100,
        stop_price=96,
    ) == 17
    assert math.isclose(portfolio_heat(equity=10_000, position_risks=[70, 50, 30]), 0.015)


def test_robust_zscore_resists_outlier_centering():
    values = pd.Series([1, 1, 2, 2, 3, 100], dtype=float)
    z = robust_zscore(values)
    assert abs(float(z.iloc[1])) < 1.0
    assert z.iloc[-1] > 10


def test_trade_metrics_and_turnover():
    trades = pd.Series([0.05, -0.02, 0.03, -0.01])
    assert profit_factor(trades) > 2.0
    assert math.isclose(trade_expectancy(trades), 0.0125)
    assert math.isclose(one_way_turnover([0.2, 0.2], [0.3, 0.1]), 0.1)


def test_psr_and_min_track_record_are_monotonic():
    low = probabilistic_sharpe_ratio(0.5, 0.0, 100)
    high = probabilistic_sharpe_ratio(1.0, 0.0, 100)
    assert high > low > 0.5
    assert minimum_track_record_length(1.0, 0.0) < minimum_track_record_length(0.5, 0.0)
