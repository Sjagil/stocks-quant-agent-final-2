from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

import numpy as np


def fixed_fractional_risk_budget(equity: float, risk_fraction: float) -> float:
    if not math.isfinite(equity) or equity <= 0:
        raise ValueError("equity must be positive")
    if not math.isfinite(risk_fraction) or not 0.0 <= risk_fraction <= 1.0:
        raise ValueError("risk_fraction must be in [0, 1]")
    return float(equity * risk_fraction)


def stop_based_quantity(
    *,
    equity: float,
    risk_fraction: float,
    entry_price: float,
    stop_price: float,
    contract_multiplier: float = 1.0,
) -> int:
    risk_budget = fixed_fractional_risk_budget(equity, risk_fraction)
    distance = abs(float(entry_price) - float(stop_price)) * float(contract_multiplier)
    if not math.isfinite(distance) or distance <= 0:
        raise ValueError("entry/stop distance must be positive")
    return max(0, int(math.floor(risk_budget / distance)))


def volatility_target_weight(
    *,
    asset_volatility: float,
    target_volatility: float,
    max_weight: float = 1.0,
) -> float:
    if asset_volatility <= 0 or target_volatility < 0 or max_weight < 0:
        raise ValueError("invalid volatility/weight inputs")
    return float(min(max_weight, target_volatility / asset_volatility))


def hybrid_weight_cap(*weights: float) -> float:
    values = [float(value) for value in weights]
    if not values:
        raise ValueError("at least one weight is required")
    if any((not math.isfinite(value) or value < 0) for value in values):
        raise ValueError("weights must be finite and non-negative")
    return float(min(values))


def portfolio_heat(
    *,
    equity: float,
    position_risks: Iterable[float],
) -> float:
    if equity <= 0:
        raise ValueError("equity must be positive")
    risks = np.asarray(list(position_risks), dtype=float)
    if (risks < 0).any() or not np.isfinite(risks).all():
        raise ValueError("position risks must be finite and non-negative")
    return float(risks.sum() / equity)


def cluster_heat(
    *,
    equity: float,
    position_risk_by_symbol: Mapping[str, float],
    cluster_by_symbol: Mapping[str, str],
) -> dict[str, float]:
    if equity <= 0:
        raise ValueError("equity must be positive")
    totals: dict[str, float] = {}
    for symbol, risk in position_risk_by_symbol.items():
        value = float(risk)
        if not math.isfinite(value) or value < 0:
            raise ValueError("position risk must be finite and non-negative")
        cluster = str(cluster_by_symbol.get(symbol, "UNCLASSIFIED"))
        totals[cluster] = totals.get(cluster, 0.0) + value
    return {cluster: total / equity for cluster, total in totals.items()}
