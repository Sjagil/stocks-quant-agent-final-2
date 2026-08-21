import numpy as np
import pandas as pd

from stocks.research.technical_feature_families_v2_31 import (
    kaufman_efficiency_ratio,
    rolling_log_trend,
    build_technical_governance_features,
)


def test_trend_statistics_detect_smooth_positive_trend():
    close = pd.Series(np.exp(np.linspace(0, 1, 80)))
    stats = rolling_log_trend(close, window=20)
    assert stats["slope"].iloc[-1] > 0
    assert stats["r2"].iloc[-1] > 0.999
    assert stats["tstat"].iloc[-1] > 10


def test_kaufman_efficiency_is_one_for_monotonic_path():
    close = pd.Series(np.arange(1, 50, dtype=float))
    er = kaufman_efficiency_ratio(close, window=10)
    assert abs(er.iloc[-1] - 1.0) < 1e-12


def test_build_features_is_causal_at_tail():
    close = pd.Series(np.linspace(100, 140, 100))
    frame = pd.DataFrame({"close": close})
    out = build_technical_governance_features(frame)
    assert "trend_regression_tstat_20" in out
    assert "volatility_expansion_10_40" in out
    assert out.iloc[:19]["trend_regression_slope_20"].isna().all()
