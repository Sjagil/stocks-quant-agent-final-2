from __future__ import annotations

import math

import pandas as pd

from stocks.research.forecast_calibration_v2_30 import (
    brier_score,
    expected_calibration_error,
    pinball_loss,
    quantile_coverage,
)


def test_calibration_metrics_perfect_probabilities():
    p = pd.Series([0.0, 1.0, 0.0, 1.0])
    y = pd.Series([0, 1, 0, 1])
    assert math.isclose(brier_score(p, y), 0.0)
    assert math.isclose(expected_calibration_error(p, y, bins=5), 0.0)


def test_quantile_metrics():
    actual = pd.Series([1.0, 2.0, 3.0, 4.0])
    q = pd.Series([1.5, 2.5, 3.5, 4.5])
    assert quantile_coverage(actual, q) == 1.0
    assert pinball_loss(actual, q, quantile=0.5) > 0
