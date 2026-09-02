from __future__ import annotations

import math

import numpy as np
import pandas as pd

from stocks.data.reconciliation_v2_29 import cross_provider_disagreement
from stocks.providers.health_v2_29 import provider_health_table, provider_reliability_score


def _frame(multiplier=1.0):
    idx = pd.date_range("2026-01-01", periods=50, freq="h", tz="UTC")
    close = (100 + np.linspace(0, 4, 50)) * multiplier
    return pd.DataFrame({
        "open": close,
        "high": close * 1.001,
        "low": close * 0.999,
        "close": close,
        "volume": np.full(50, 1000.0),
    }, index=idx)


def test_cross_provider_disagreement_zero_for_identical_data():
    left = _frame()
    report = cross_provider_disagreement(left, left.copy(), left_name="a", right_name="b")
    assert report["overlap_rows"] == 50
    assert math.isclose(report["close_median_disagreement_bps"], 0.0, abs_tol=1e-12)


def test_cross_provider_disagreement_detects_price_shift():
    report = cross_provider_disagreement(_frame(), _frame(1.01))
    assert report["close_median_disagreement_bps"] > 90


def test_provider_reliability_and_ranking():
    healthy = provider_reliability_score({"OK": 10})
    weak = provider_reliability_score({"OK": 1, "ERROR": 9})
    assert healthy["status"] == "HEALTHY"
    assert weak["reliability_score"] < healthy["reliability_score"]
    table = provider_health_table({
        "good": {"OK": 10},
        "mixed": {"OK": 5, "EMPTY": 5},
        "bad": {"ERROR": 10},
    })
    assert [row["provider"] for row in table] == ["good", "mixed", "bad"]
