from __future__ import annotations
import math, numpy as np


def validation_quality_score(*, psr: float, pbo: float, profit_factor: float, expectancy: float, wfe: float | None, parameter_robustness: float, max_drawdown: float, cost_stress_positive: bool) -> float:
    psr_q=float(np.clip(psr,0,1)); pbo_q=1-float(np.clip(pbo,0,1))
    pf_q=float(np.clip((profit_factor-1.0)/1.0,0,1)) if np.isfinite(profit_factor) else 1.0
    exp_q=float(1.0-math.exp(-max(0.0,expectancy)*100.0))
    wfe_q=0.5 if wfe is None or not np.isfinite(wfe) else float(np.clip(wfe,0,1))
    robust_q=float(np.clip(parameter_robustness,0,1)); dd_q=float(np.clip(1-max_drawdown/0.30,0,1))
    cost_q=1.0 if cost_stress_positive else 0.0
    score=0.20*psr_q+0.15*pbo_q+0.15*pf_q+0.10*exp_q+0.10*wfe_q+0.15*robust_q+0.10*dd_q+0.05*cost_q
    return float(np.clip(score,0,1))


__all__=["validation_quality_score"]
