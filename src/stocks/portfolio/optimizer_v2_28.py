from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

AUTHORITY_NONE = "NONE"


@dataclass(frozen=True)
class OptimizerConstraints:
    max_total_weight: float = 0.60
    max_position_weight: float = 0.30
    minimum_weight: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 < self.max_total_weight <= 1.0:
            raise ValueError("max_total_weight must be in (0,1]")
        if not 0.0 < self.max_position_weight <= self.max_total_weight:
            raise ValueError("max_position_weight must be in (0,max_total_weight]")
        if not 0.0 <= self.minimum_weight < self.max_position_weight:
            raise ValueError("minimum_weight must be in [0,max_position_weight)")


@dataclass(frozen=True)
class OptimizerResult:
    method: str
    weights: Mapping[str, float]
    objective_value: float | None
    status: str
    execution_authority: str = AUTHORITY_NONE


def _require_cvxpy():
    try:
        import cvxpy as cp
    except Exception as exc:  # pragma: no cover
        raise ImportError("cvxpy is required for portfolio optimizer challengers") from exc
    return cp


def _covariance(covariance: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(covariance, pd.DataFrame) or covariance.empty:
        raise ValueError("covariance must be a non-empty DataFrame")
    if list(covariance.index) != list(covariance.columns):
        raise ValueError("covariance index/columns must match in order")
    values = covariance.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("covariance must be finite")
    values = 0.5 * (values + values.T)
    eigenvalues = np.linalg.eigvalsh(values)
    if eigenvalues.min() < -1e-8:
        raise ValueError("covariance must be positive semidefinite")
    if eigenvalues.min() < 1e-10:
        values = values + np.eye(len(values)) * (1e-10 - eigenvalues.min())
    return pd.DataFrame(values, index=covariance.index, columns=covariance.columns)


def _base_constraints(cp, w, constraints: OptimizerConstraints):
    return [
        w >= constraints.minimum_weight,
        w <= constraints.max_position_weight,
        cp.sum(w) <= constraints.max_total_weight,
    ]


def minimum_variance_weights(
    covariance: pd.DataFrame,
    *,
    constraints: OptimizerConstraints | None = None,
) -> OptimizerResult:
    cp = _require_cvxpy()
    active = constraints or OptimizerConstraints()
    cov = _covariance(covariance)
    n = len(cov)
    w = cp.Variable(n)
    objective = cp.Minimize(cp.quad_form(w, cov.to_numpy(dtype=float)))
    problem = cp.Problem(objective, _base_constraints(cp, w, active) + [cp.sum(w) == active.max_total_weight])
    problem.solve()
    if w.value is None:
        return OptimizerResult("MIN_VARIANCE", {}, None, str(problem.status))
    weights = {name: max(0.0, float(value)) for name, value in zip(cov.columns, np.asarray(w.value).reshape(-1))}
    return OptimizerResult("MIN_VARIANCE", weights, None if problem.value is None else float(problem.value), str(problem.status))


def mean_cvar_weights(
    expected_returns: pd.Series,
    scenario_returns: pd.DataFrame,
    *,
    alpha: float = 0.95,
    cvar_penalty: float = 3.0,
    turnover_penalty: float = 0.0,
    previous_weights: pd.Series | None = None,
    constraints: OptimizerConstraints | None = None,
) -> OptimizerResult:
    cp = _require_cvxpy()
    if not 0.5 < alpha < 1.0:
        raise ValueError("alpha must be in (0.5,1)")
    if cvar_penalty < 0 or turnover_penalty < 0:
        raise ValueError("penalties must be non-negative")
    active = constraints or OptimizerConstraints()
    scenarios = scenario_returns.apply(pd.to_numeric, errors="coerce").dropna(how="any")
    columns = scenarios.columns
    mu = pd.to_numeric(expected_returns, errors="coerce").reindex(columns)
    if scenarios.empty or mu.isna().any():
        raise ValueError("scenario/expected return inputs are incomplete")
    n = len(columns)
    t = len(scenarios)
    w = cp.Variable(n)
    zeta = cp.Variable()
    u = cp.Variable(t, nonneg=True)
    losses = -(scenarios.to_numpy(dtype=float) @ w)
    cvar = zeta + cp.sum(u) / ((1.0 - alpha) * t)
    objective_value = mu.to_numpy(dtype=float) @ w - cvar_penalty * cvar
    if previous_weights is not None and turnover_penalty > 0:
        previous = pd.to_numeric(previous_weights, errors="coerce").reindex(columns).fillna(0.0).to_numpy(dtype=float)
        objective_value -= turnover_penalty * cp.norm1(w - previous)
    constraints_list = _base_constraints(cp, w, active) + [u >= losses - zeta]
    problem = cp.Problem(cp.Maximize(objective_value), constraints_list)
    problem.solve()
    if w.value is None:
        return OptimizerResult("MEAN_CVAR", {}, None, str(problem.status))
    weights = {name: max(0.0, float(value)) for name, value in zip(columns, np.asarray(w.value).reshape(-1))}
    return OptimizerResult("MEAN_CVAR", weights, None if problem.value is None else float(problem.value), str(problem.status))


def risk_budgeting_weights(
    covariance: pd.DataFrame,
    *,
    risk_budgets: pd.Series | None = None,
    constraints: OptimizerConstraints | None = None,
) -> OptimizerResult:
    """Convex risk-budgeting challenger.

    Solves min 0.5*x'Σx - b'log(x), then normalizes and applies deterministic
    long-only caps. The final hard production constraints still belong to the
    deterministic allocator.
    """
    cp = _require_cvxpy()
    active = constraints or OptimizerConstraints()
    cov = _covariance(covariance)
    n = len(cov)
    if risk_budgets is None:
        budgets = np.full(n, 1.0 / n)
    else:
        budgets = pd.to_numeric(risk_budgets, errors="coerce").reindex(cov.columns).to_numpy(dtype=float)
        if not np.isfinite(budgets).all() or (budgets <= 0).any():
            raise ValueError("risk budgets must be positive and complete")
        budgets = budgets / budgets.sum()
    x = cp.Variable(n, pos=True)
    objective = cp.Minimize(0.5 * cp.quad_form(x, cov.to_numpy(dtype=float)) - budgets @ cp.log(x))
    problem = cp.Problem(objective, [x >= 1e-9])
    problem.solve()
    if x.value is None:
        return OptimizerResult("RISK_BUDGETING", {}, None, str(problem.status))
    raw = np.asarray(x.value, dtype=float).reshape(-1)
    raw = np.maximum(raw, 0.0)
    raw = raw / max(raw.sum(), 1e-15) * active.max_total_weight
    # Deterministic cap-and-redistribute.
    capped = np.zeros_like(raw)
    remaining = active.max_total_weight
    active_idx = list(range(n))
    while active_idx and remaining > 1e-12:
        mass = raw[active_idx].sum()
        if mass <= 0:
            break
        hit = []
        for idx in active_idx:
            share = remaining * raw[idx] / mass
            capacity = active.max_position_weight - capped[idx]
            if share >= capacity - 1e-12:
                alloc = max(0.0, capacity)
                capped[idx] += alloc
                remaining -= alloc
                hit.append(idx)
        if not hit:
            for idx in active_idx:
                capped[idx] += remaining * raw[idx] / mass
            remaining = 0.0
        else:
            active_idx = [idx for idx in active_idx if idx not in hit]
    weights = {name: float(value) for name, value in zip(cov.columns, capped) if value > 1e-12}
    return OptimizerResult("RISK_BUDGETING", weights, None if problem.value is None else float(problem.value), str(problem.status))
