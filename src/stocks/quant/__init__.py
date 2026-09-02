"""Canonical quantitative-finance primitives.

All functions in this package are research/shadow only and grant no execution authority.
"""

from .returns import (
    simple_returns,
    log_returns,
    forward_simple_returns,
    wealth_index,
    cumulative_return,
    cagr_from_wealth,
)
from .volatility import (
    annualized_volatility,
    ewma_volatility,
    true_range,
    atr,
    parkinson_volatility,
    garman_klass_volatility,
    rogers_satchell_volatility,
)
from .drawdown import (
    drawdown_series,
    max_drawdown,
    ulcer_index,
    pain_index,
    drawdown_velocity,
    recovery_ratio,
)
from .tail_risk import (
    historical_var,
    expected_shortfall,
    downside_deviation,
    lower_partial_moment,
    omega_ratio,
)
from .covariance import (
    sample_covariance,
    ewma_covariance,
    shrink_covariance,
    portfolio_volatility,
    marginal_risk_contribution,
    risk_contribution,
    diversification_ratio,
    effective_number_of_positions,
    entropy_effective_number,
)
from .position_sizing import (
    fixed_fractional_risk_budget,
    stop_based_quantity,
    volatility_target_weight,
    hybrid_weight_cap,
    portfolio_heat,
)
from .portfolio_metrics import (
    sharpe_ratio,
    sortino_ratio,
    calmar_ratio,
    tracking_error,
    information_ratio,
    profit_factor,
    trade_expectancy,
    payoff_ratio,
    one_way_turnover,
)
from .statistical_validation import (
    probabilistic_sharpe_ratio,
    minimum_track_record_length,
)

from .liquidity import (
    dollar_volume,
    amihud_illiquidity,
    participation_rate,
    square_root_impact,
    implementation_shortfall,
)
from .factors import (
    factor_beta,
    rolling_beta,
    residual_returns,
    residual_momentum,
    cross_sectional_dispersion,
    average_pairwise_correlation,
)
from .kelly import (
    binary_kelly,
    continuous_kelly,
    fractional_kelly,
    multi_asset_kelly,
)
from .portfolio_utility import (
    UtilityPenalties,
    concentration_hhi,
    portfolio_utility,
)

AUTHORITY_NONE = "NONE"

__all__ = [
    "AUTHORITY_NONE",
    "simple_returns", "log_returns", "forward_simple_returns", "wealth_index",
    "cumulative_return", "cagr_from_wealth", "annualized_volatility",
    "ewma_volatility", "true_range", "atr", "parkinson_volatility",
    "garman_klass_volatility", "rogers_satchell_volatility", "drawdown_series",
    "max_drawdown", "ulcer_index", "pain_index", "drawdown_velocity",
    "recovery_ratio", "historical_var", "expected_shortfall",
    "downside_deviation", "lower_partial_moment", "omega_ratio",
    "sample_covariance", "ewma_covariance", "shrink_covariance",
    "portfolio_volatility", "marginal_risk_contribution", "risk_contribution",
    "diversification_ratio", "effective_number_of_positions",
    "entropy_effective_number", "fixed_fractional_risk_budget",
    "stop_based_quantity", "volatility_target_weight", "hybrid_weight_cap",
    "portfolio_heat", "sharpe_ratio", "sortino_ratio", "calmar_ratio",
    "tracking_error", "information_ratio", "profit_factor",
    "trade_expectancy", "payoff_ratio", "one_way_turnover",
    "probabilistic_sharpe_ratio", "minimum_track_record_length",
    "dollar_volume", "amihud_illiquidity", "participation_rate",
    "square_root_impact", "implementation_shortfall", "factor_beta",
    "rolling_beta", "residual_returns", "residual_momentum",
    "cross_sectional_dispersion", "average_pairwise_correlation",
    "binary_kelly", "continuous_kelly", "fractional_kelly",
    "multi_asset_kelly", "UtilityPenalties", "concentration_hhi",
    "portfolio_utility",
]
