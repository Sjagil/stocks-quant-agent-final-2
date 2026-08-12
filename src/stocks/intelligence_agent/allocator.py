from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

try:
    import cvxpy as cp
except Exception:  # pragma: no cover - exercised when optional optimizer is absent
    cp = None

from .config import AgentConfig
from .models import AllocationTarget, AssetClass, AssetView


@dataclass(frozen=True)
class AllocationResult:
    targets: tuple[AllocationTarget, ...]
    cash_weight: float
    solver_status: str


class ConstrainedAllocator:
    """Long-only, no-leverage allocator with concentration and turnover control.

    CVXPY is the preferred solver. A deterministic projection fallback keeps the
    agent operational for research/test environments where CVXPY is unavailable.
    """

    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    def allocate(
        self,
        *,
        views: list[AssetView],
        covariance: pd.DataFrame,
        current_weights: dict[str, float],
        equity: float,
    ) -> AllocationResult:
        if equity <= 0:
            raise ValueError("equity must be positive")
        eligible = [v for v in views if v.alpha_score > 0 and v.confidence >= 0.40]
        eligible.sort(key=lambda v: (v.expected_return, v.confidence), reverse=True)
        eligible = eligible[: self.config.max_positions]
        if not eligible:
            return AllocationResult((), 1.0, "NO_LONG_ALPHA")

        dynamic_min = max(self.config.min_position_weight, self.config.min_position_notional / equity)
        if dynamic_min >= 1.0 - self.config.cash_floor:
            return AllocationResult((), 1.0, "MIN_POSITION_TOO_LARGE")

        max_by_min = max(1, int((1.0 - self.config.cash_floor) / dynamic_min))
        eligible = eligible[:max_by_min]
        symbols = [v.symbol for v in eligible]
        cov = covariance.reindex(index=symbols, columns=symbols).fillna(0.0).to_numpy(dtype=float)
        cov = (cov + cov.T) / 2.0 + np.eye(len(symbols)) * 1e-8
        mu = np.array([v.expected_return for v in eligible], dtype=float)
        current = np.array([max(0.0, current_weights.get(s, 0.0)) for s in symbols], dtype=float)

        if cp is not None:
            raw, status = self._solve_cvxpy(eligible, cov, mu, current)
        else:
            raw, status = self._solve_projection(eligible, cov, mu, current)

        raw = self._apply_hard_constraints(raw, eligible, dynamic_min)
        return self._to_result(eligible, raw, current_weights, equity, status)

    def _solve_cvxpy(self, eligible, cov, mu, current) -> tuple[np.ndarray, str]:
        w = cp.Variable(len(eligible), nonneg=True)
        risk = cp.quad_form(w, cp.psd_wrap(cov))
        turnover = cp.norm1(w - current)
        objective = cp.Maximize(mu @ w - self.config.risk_aversion * risk - self.config.turnover_penalty * turnover)
        constraints = [cp.sum(w) <= 1.0 - self.config.cash_floor, w <= self.config.max_single_weight]
        for asset_class, cap in (
            (AssetClass.STOCK, self.config.max_stock_weight),
            (AssetClass.ETF, self.config.max_etf_weight),
            (AssetClass.COMMODITY, self.config.max_commodity_weight),
        ):
            idx = [i for i, v in enumerate(eligible) if v.asset_class == asset_class]
            if idx:
                constraints.append(cp.sum(w[idx]) <= cap)
        problem = cp.Problem(objective, constraints)
        try:
            problem.solve(solver=cp.CLARABEL, verbose=False)
        except Exception:
            problem.solve(solver=cp.SCS, verbose=False)
        if w.value is None:
            return np.zeros(len(eligible)), str(problem.status)
        return np.maximum(np.asarray(w.value).reshape(-1), 0.0), str(problem.status)

    def _solve_projection(self, eligible, cov, mu, current) -> tuple[np.ndarray, str]:
        variance = np.clip(np.diag(cov), 1e-6, None)
        desirability = np.clip(mu / np.sqrt(variance), 0.0, None)
        if desirability.sum() <= 0:
            return np.zeros(len(eligible)), "FALLBACK_NO_DESIRABILITY"
        target_total = 1.0 - self.config.cash_floor
        raw = desirability / desirability.sum() * target_total
        # Mild turnover pull toward current weights.
        blend = 1.0 / (1.0 + max(self.config.turnover_penalty, 0.0))
        raw = blend * raw + (1.0 - blend) * current
        return raw, "FALLBACK_PROJECTED"

    def _apply_hard_constraints(self, raw, eligible, dynamic_min) -> np.ndarray:
        raw = np.maximum(np.asarray(raw, dtype=float), 0.0)
        raw = np.minimum(raw, self.config.max_single_weight)

        for asset_class, cap in (
            (AssetClass.STOCK, self.config.max_stock_weight),
            (AssetClass.ETF, self.config.max_etf_weight),
            (AssetClass.COMMODITY, self.config.max_commodity_weight),
        ):
            idx = np.array([i for i, v in enumerate(eligible) if v.asset_class == asset_class], dtype=int)
            if len(idx) and raw[idx].sum() > cap:
                raw[idx] *= cap / raw[idx].sum()

        raw[raw < dynamic_min] = 0.0
        total_cap = 1.0 - self.config.cash_floor
        if raw.sum() > total_cap and raw.sum() > 0:
            raw *= total_cap / raw.sum()
        # Scaling can theoretically create dust. Drop it once more instead of inflating it.
        raw[raw < dynamic_min] = 0.0
        return raw

    def _to_result(self, eligible, raw, current_weights, equity, status) -> AllocationResult:
        targets: list[AllocationTarget] = []
        for view, weight in zip(eligible, raw, strict=True):
            current_weight = max(0.0, current_weights.get(view.symbol, 0.0))
            delta = float(weight - current_weight)
            if weight <= 0 and current_weight <= 0:
                continue
            action = "INCREASE" if delta > 0.0025 else "DECREASE" if delta < -0.0025 else "HOLD"
            targets.append(
                AllocationTarget(
                    symbol=view.symbol,
                    asset_class=view.asset_class,
                    current_weight=current_weight,
                    target_weight=float(weight),
                    delta_weight=delta,
                    target_notional=float(weight * equity),
                    action=action,
                    confidence=view.confidence,
                    rationale=view.rationale,
                )
            )
        cash = float(max(0.0, 1.0 - sum(t.target_weight for t in targets)))
        return AllocationResult(tuple(targets), cash, status)
