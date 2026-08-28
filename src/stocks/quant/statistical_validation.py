from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np


_NORMAL = NormalDist()


def probabilistic_sharpe_ratio(
    estimated_sharpe: float,
    benchmark_sharpe: float,
    observations: int,
    *,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    if observations < 2:
        raise ValueError("observations must be >= 2")
    sr = float(estimated_sharpe)
    benchmark = float(benchmark_sharpe)
    denominator_sq = 1.0 - float(skewness) * sr + ((float(kurtosis) - 1.0) / 4.0) * sr * sr
    if denominator_sq <= 0:
        return float("nan")
    z = (sr - benchmark) * math.sqrt(observations - 1.0) / math.sqrt(denominator_sq)
    return float(_NORMAL.cdf(z))


def minimum_track_record_length(
    estimated_sharpe: float,
    benchmark_sharpe: float,
    *,
    confidence: float = 0.95,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    if not 0.5 < confidence < 1.0:
        raise ValueError("confidence must be in (0.5, 1)")
    gap = float(estimated_sharpe) - float(benchmark_sharpe)
    if gap <= 0:
        return float("inf")
    sr = float(estimated_sharpe)
    correction = 1.0 - float(skewness) * sr + ((float(kurtosis) - 1.0) / 4.0) * sr * sr
    if correction <= 0:
        return float("nan")
    z = _NORMAL.inv_cdf(confidence)
    return float(1.0 + correction * (z / gap) ** 2)
