from __future__ import annotations
import math
from statistics import NormalDist
import numpy as np

from stocks.quant.portfolio_metrics import sharpe_ratio
from stocks.quant.statistical_validation import minimum_track_record_length, probabilistic_sharpe_ratio
from .return_distribution_v2_33 import clean_returns, kurtosis, skewness

_NORMAL = NormalDist()
_EULER_GAMMA = 0.5772156649015329


def sample_sharpe_statistics(returns) -> dict[str, float | int]:
    x = clean_returns(returns)
    sr = sharpe_ratio(x)
    sk = skewness(x); ku = kurtosis(x)
    psr = probabilistic_sharpe_ratio(sr, 0.0, len(x), skewness=sk, kurtosis=ku) if len(x) >= 2 and np.isfinite(sr) else float("nan")
    mintrl = minimum_track_record_length(sr, 0.0, skewness=sk, kurtosis=ku) if np.isfinite(sr) else float("inf")
    return {"observations": int(len(x)), "sharpe_per_period": float(sr), "skewness": float(sk), "kurtosis": float(ku), "psr_vs_zero": float(psr), "minimum_track_record": float(mintrl)}


def expected_maximum_sharpe(trial_sharpes) -> float:
    s = clean_returns(trial_sharpes)
    n = len(s)
    if n <= 1:
        return 0.0
    sigma = float(np.std(s, ddof=1))
    if sigma <= 1e-15:
        return float(np.mean(s))
    z1 = _NORMAL.inv_cdf(max(1e-12, 1.0 - 1.0 / n))
    z2 = _NORMAL.inv_cdf(max(1e-12, 1.0 - 1.0 / (n * math.e)))
    expected_z = (1.0 - _EULER_GAMMA) * z1 + _EULER_GAMMA * z2
    return float(np.mean(s) + sigma * expected_z)


def deflated_sharpe_probability(returns, trial_sharpes) -> dict[str, float]:
    stats = sample_sharpe_statistics(returns)
    benchmark = expected_maximum_sharpe(trial_sharpes)
    psr = probabilistic_sharpe_ratio(
        float(stats["sharpe_per_period"]), benchmark, int(stats["observations"]),
        skewness=float(stats["skewness"]), kurtosis=float(stats["kurtosis"]),
    )
    return {"benchmark_sharpe_multiple_testing": benchmark, "deflated_sharpe_probability": float(psr)}


__all__ = ["deflated_sharpe_probability", "expected_maximum_sharpe", "sample_sharpe_statistics"]
