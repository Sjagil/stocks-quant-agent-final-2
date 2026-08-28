from __future__ import annotations

import math

import numpy as np
import pandas as pd

from stocks.research.feature_ic_v2_28 import (
    cross_sectional_ic_series,
    feature_decay,
    feature_redundancy,
    summarize_ic,
)
from stocks.research.forward_return_labels_v2_28 import (
    ForwardLabelSpec,
    build_forward_return_labels,
    forward_distribution_summary,
    quantile_opportunity_score,
    robust_expected_return,
)


def test_forward_labels_are_t_plus_h_and_tail_is_unavailable():
    frame = pd.DataFrame({"close": np.arange(100.0, 120.0)})
    labels = build_forward_return_labels(frame, spec=ForwardLabelSpec(horizons=(2, 5)))
    expected = frame["close"].iloc[2] / frame["close"].iloc[0] - 1
    assert math.isclose(labels["fwd_return_2"].iloc[0], expected)
    assert labels["fwd_return_2"].iloc[-2:].isna().all()
    assert labels["fwd_return_5"].iloc[-5:].isna().all()


def test_forward_distribution_and_robust_mean():
    values = pd.Series([-0.1, -0.02, 0.01, 0.03, 0.05, 0.1])
    summary = forward_distribution_summary(values)
    assert summary["observations"] == 6
    assert 0 < summary["probability_positive"] < 1
    assert math.isclose(robust_expected_return(mean_return=0.05, estimation_uncertainty=0.02), 0.03)
    assert quantile_opportunity_score(
        median_return=0.04,
        lower_quantile_return=-0.02,
        expected_cost=0.005,
    ) > 1


def test_cross_sectional_rank_ic_is_one_for_perfect_ranking():
    rows = []
    for day in range(8):
        for symbol, value in zip("ABCDE", range(5)):
            rows.append({
                "day": day,
                "symbol": symbol,
                "feature": float(value),
                "forward": float(value * 2 + day),
            })
    frame = pd.DataFrame(rows)
    ic = cross_sectional_ic_series(
        frame,
        date_column="day",
        feature_column="feature",
        target_column="forward",
        rank=True,
    )
    report = summarize_ic(ic)
    assert np.allclose(ic.dropna(), 1.0)
    assert math.isclose(report.mean_ic, 1.0)


def test_feature_decay_and_redundancy():
    x = pd.Series(np.arange(100.0))
    frame = pd.DataFrame({
        "feature": x,
        "fwd1": x + 1,
        "fwd2": -x,
        "clone": x * 2,
        "noise": np.sin(x),
    })
    decay = feature_decay(
        frame,
        feature_column="feature",
        forward_columns=("fwd1", "fwd2"),
    )
    assert decay["fwd1"] > 0.99
    assert decay["fwd2"] < -0.99
    redundancy = feature_redundancy(frame[["feature", "clone", "noise"]])
    assert redundancy["feature"] > 0.99
