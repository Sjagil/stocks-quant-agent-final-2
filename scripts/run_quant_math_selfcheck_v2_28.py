#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from stocks.portfolio.expected_returns_v2_28 import ForwardDistribution
from stocks.quant.covariance import (
    effective_number_of_positions,
    portfolio_volatility,
    risk_contribution,
    shrink_covariance,
)
from stocks.quant.drawdown import max_drawdown
from stocks.quant.position_sizing import fixed_fractional_risk_budget, stop_based_quantity
from stocks.quant.returns import forward_simple_returns, wealth_index
from stocks.quant.tail_risk import expected_shortfall

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/research_runtime/quant_math_v2_28"


def main() -> int:
    rng = np.random.default_rng(2801)
    returns = pd.DataFrame(
        rng.normal(
            loc=[0.0004, 0.0003, 0.0002],
            scale=[0.012, 0.009, 0.007],
            size=(800, 3),
        ),
        columns=["ALPHA", "BETA", "GAMMA"],
    )
    covariance = shrink_covariance(returns, method="ledoit_wolf", periods_per_year=252)
    weights = pd.Series({"ALPHA": 0.20, "BETA": 0.20, "GAMMA": 0.20})
    vol = portfolio_volatility(weights, covariance)
    contributions = risk_contribution(weights, covariance)
    if abs(float(contributions.sum()) - vol) > 1e-10:
        raise AssertionError("risk contributions do not sum to portfolio volatility")

    equity_curve = wealth_index(returns["ALPHA"])
    prices = 100.0 * wealth_index(returns["ALPHA"])
    labels = forward_simple_returns(prices, [4, 8, 16])
    if labels["fwd_return_4"].iloc[-4:].notna().any():
        raise AssertionError("forward labels leak beyond available horizon")

    distribution = ForwardDistribution(
        mean=0.03,
        uncertainty=0.01,
        q10=-0.04,
        q50=0.025,
        q90=0.10,
        expected_cost=0.002,
        calibration_confidence=0.8,
        stability=0.8,
        regime_fit=0.9,
        liquidity=0.95,
    )

    payload = {
        "schema": "quant_math_selfcheck_v2_28",
        "portfolio_volatility": vol,
        "risk_contribution_sum": float(contributions.sum()),
        "effective_positions": effective_number_of_positions(weights),
        "max_drawdown": max_drawdown(equity_curve),
        "expected_shortfall_95": expected_shortfall(returns["ALPHA"], alpha=0.95),
        "risk_budget_0_70pct_on_10k": fixed_fractional_risk_budget(10000.0, 0.007),
        "stop_based_quantity": stop_based_quantity(
            equity=10000.0,
            risk_fraction=0.007,
            entry_price=100.0,
            stop_price=96.0,
        ),
        "robust_expected_return": distribution.robust_mean(),
        "opportunity_score": distribution.opportunity_score(),
        "forward_label_columns": list(labels.columns),
        "broker_submission_enabled": False,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "selfcheck.json"
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("QUANT_MATH_V2_28_SELFCHECK OK")
    print("PORTFOLIO_VOLATILITY", round(vol, 8))
    print("RISK_CONTRIBUTION_IDENTITY", True)
    print("FORWARD_LABEL_TAIL_NAN", True)
    print("BROKER_SUBMISSION_ENABLED False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT", target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
