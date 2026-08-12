import numpy as np
import pandas as pd

from stocks.rl.features import build_rl_features


def test_features_keep_same_index_and_are_causal_shape():
    n = 120
    idx = pd.date_range("2025-01-01", periods=n, freq="D", tz="UTC")
    close = pd.Series(np.linspace(100, 130, n), index=idx)
    frame = pd.DataFrame(
        {
            "open": close * 0.999,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": np.linspace(1_000, 2_000, n),
        },
        index=idx,
    )
    features = build_rl_features(frame)
    assert features.index.equals(frame.index)
    assert "log_ret_1" in features
    assert "volume_robust_z" in features
