from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from stocks.agents.feature_fabric import build_current_context_snapshot
from stocks.agents.feature_views import ROLE_COLUMNS, select_role_features
from stocks.rl.features import build_rl_features


def sample_frame(rows: int = 1000) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=rows, freq="h", tz="UTC")
    trend = np.linspace(100.0, 140.0, rows)
    wave = np.sin(np.linspace(0.0, 25.0, rows))
    close = trend + wave
    return pd.DataFrame(
        {
            "open": close - 0.15,
            "high": close + 0.70,
            "low": close - 0.65,
            "close": close,
            "volume": np.linspace(1000.0, 2500.0, rows),
        },
        index=index,
    )


def test_feature_bank_is_broad():
    features = build_rl_features(sample_frame())
    required = {
        "rsi_2",
        "rsi_14",
        "macd_hist_pct",
        "adx_14",
        "atr_pct",
        "bb_z_20",
        "mfi_14",
        "cci_20",
        "stoch_k_14",
        "obv_slope_10",
        "cmf_20",
        "rolling_vwap20_dist",
        "donchian_high_dist_20",
    }
    assert required.issubset(features.columns)
    assert features.shape[1] >= 45


def test_future_append_does_not_change_past_features():
    frame = sample_frame()
    base = build_rl_features(frame.iloc[:-1])
    extended = build_rl_features(frame)
    common = base.dropna().index
    pd.testing.assert_frame_equal(
        base.loc[common],
        extended.loc[common, base.columns],
        check_exact=False,
        rtol=1e-12,
        atol=1e-12,
    )


def test_role_views_are_strict_subsets():
    bank = build_rl_features(sample_frame())
    for role, columns in ROLE_COLUMNS.items():
        view = select_role_features(bank, role)
        assert list(view.columns) == list(columns)
        assert view.shape[1] < bank.shape[1]


def test_optional_external_context_fails_neutral(tmp_path: Path):
    snapshot = build_current_context_snapshot(tmp_path, "TEST", "1h")
    assert snapshot.modifier == 1.0
    assert snapshot.execution_authority == "NONE"
    assert all(item.training_safe is False for item in snapshot.modalities)


def test_role_views_have_usable_rows():
    bank = build_rl_features(sample_frame())
    for role in ROLE_COLUMNS:
        view = select_role_features(bank, role)
        assert len(view.dropna()) > 500
