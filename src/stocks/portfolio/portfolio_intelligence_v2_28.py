from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

from stocks.quant.covariance import (
    portfolio_volatility,
    risk_contribution,
    shrink_covariance,
)

from .optimizer_v2_28 import (
    AUTHORITY_NONE,
    OptimizerConstraints,
    OptimizerResult,
    mean_cvar_weights,
    minimum_variance_weights,
    risk_budgeting_weights,
)


@dataclass(frozen=True)
class PortfolioChallengerSet:
    covariance_method: str
    covariance: pd.DataFrame
    challengers: Mapping[str, OptimizerResult]
    diagnostics: Mapping[str, Mapping[str, float]]
    execution_authority: str = AUTHORITY_NONE


def _diagnostics(result: OptimizerResult, covariance: pd.DataFrame) -> dict[str, float]:
    if not result.weights:
        return {"total_weight": 0.0, "portfolio_volatility": float("nan"), "max_risk_contribution": float("nan")}
    weights = pd.Series(result.weights, dtype=float).reindex(covariance.columns).fillna(0.0)
    rc = risk_contribution(weights, covariance)
    return {
        "total_weight": float(weights.sum()),
        "portfolio_volatility": portfolio_volatility(weights, covariance),
        "max_weight": float(weights.max()),
        "effective_positions": float(1.0 / np.square(weights / weights.sum()).sum()) if weights.sum() > 0 else 0.0,
        "max_risk_contribution": float(rc.max()) if len(rc) else float("nan"),
    }


def build_portfolio_challengers(
    historical_returns: pd.DataFrame,
    expected_returns: pd.Series,
    *,
    previous_weights: pd.Series | None = None,
    covariance_method: str = "ledoit_wolf",
    periods_per_year: float | None = None,
    constraints: OptimizerConstraints | None = None,
) -> PortfolioChallengerSet:
    cov = shrink_covariance(
        historical_returns,
        method=covariance_method,
        periods_per_year=periods_per_year,
    )
    active = constraints or OptimizerConstraints()
    minvar = minimum_variance_weights(cov, constraints=active)
    meancvar = mean_cvar_weights(
        expected_returns,
        historical_returns.reindex(columns=cov.columns),
        previous_weights=previous_weights,
        turnover_penalty=0.05 if previous_weights is not None else 0.0,
        constraints=active,
    )
    positive_alpha = pd.to_numeric(expected_returns, errors="coerce").reindex(cov.columns).fillna(0.0).clip(lower=0.0)
    budgets = np.exp(np.clip(positive_alpha.to_numpy(dtype=float) * 50.0, -20.0, 20.0))
    budgets = pd.Series(budgets, index=cov.columns)
    riskbudget = risk_budgeting_weights(cov, risk_budgets=budgets, constraints=active)
    challengers = {
        "MIN_VARIANCE": minvar,
        "MEAN_CVAR": meancvar,
        "RISK_BUDGETING_ALPHA_TILT": riskbudget,
    }
    diagnostics = {name: _diagnostics(result, cov) for name, result in challengers.items()}
    return PortfolioChallengerSet(
        covariance_method=covariance_method,
        covariance=cov,
        challengers=challengers,
        diagnostics=diagnostics,
    )
