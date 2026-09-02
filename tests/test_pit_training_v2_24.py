from __future__ import annotations

import numpy as np
import pandas as pd
from types import SimpleNamespace
from stocks.training.pit_dataset_v2_24 import (
    audit_pit_training_frame_v224,
    audit_rl_episode_v221_pit,
    build_forward_return_labels_v224,
    build_purged_walk_forward_splits_v224,
    pit_asof_join_v224,
)


def test_pit_asof_join_never_exposes_future_release() -> None:
    decisions = pd.DataFrame(
        {
            "symbol": ["AAA", "AAA", "AAA"],
            "decision_time": pd.to_datetime(
                ["2024-01-02T16:00Z", "2024-01-03T16:00Z", "2024-01-04T16:00Z"]
            ),
        }
    )
    features = pd.DataFrame(
        {
            "symbol": ["AAA", "AAA"],
            "event_time": pd.to_datetime(["2023-12-31T00:00Z", "2024-01-03T00:00Z"]),
            "available_at": pd.to_datetime(["2024-01-02T12:00Z", "2024-01-04T12:00Z"]),
            "value": [10.0, 20.0],
        }
    )
    joined = pit_asof_join_v224(decisions, features, value_columns=["value"], prefix="fund")
    assert joined["fund_value"].tolist() == [10.0, 10.0, 20.0]
    assert (joined["fund_available_at"] <= joined["decision_time"]).all()
    assert audit_pit_training_frame_v224(joined)["valid"] is True


def test_pit_audit_rejects_future_feature_availability() -> None:
    frame = pd.DataFrame(
        {
            "decision_time": pd.to_datetime(["2024-01-01T10:00Z"]),
            "macro_available_at": pd.to_datetime(["2024-01-01T11:00Z"]),
            "macro_value": [1.0],
        }
    )
    audit = audit_pit_training_frame_v224(frame)
    assert audit["valid"] is False
    assert "FUTURE_FEATURE_AVAILABILITY" in audit["errors"]


def test_labels_are_future_outcomes_not_input_availability() -> None:
    frame = pd.DataFrame(
        {
            "symbol": ["AAA"] * 5,
            "decision_time": pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC"),
            "close": [100.0, 101.0, 103.0, 102.0, 105.0],
        }
    )
    labeled = build_forward_return_labels_v224(frame, horizon_bars=2)
    assert np.isclose(labeled.loc[0, "forward_return"], 0.03)
    assert labeled.loc[0, "forward_return_available_at"] == labeled.loc[2, "decision_time"]


def test_purged_walk_forward_has_explicit_gaps() -> None:
    splits = build_purged_walk_forward_splits_v224(
        1000,
        train_size=400,
        validation_size=100,
        test_size=100,
        purge=20,
        embargo=15,
    )
    first = splits[0]
    assert first.validation_start - first.train_stop == 20
    assert first.test_start - first.validation_stop == 15


def test_existing_rl_v221_episode_passes_pit_contract() -> None:
    timestamps = np.arange(10).astype("timedelta64[h]") + np.datetime64("2024-01-01T00")
    episode = SimpleNamespace(
        timestamps=timestamps,
        feature_cutoffs=timestamps.copy(),
        steps=9,
    )

    class Bundle:
        dataset_hash = "a" * 64
        symbols = ("AAA", "BBB")
        timeframe = "1h"

        @staticmethod
        def manifest():
            return {
                "point_in_time": True,
                "feature_cutoff_at_or_before_decision": True,
                "forward_filled_bars": False,
                "execution_authority": "NONE",
            }

    bundle = Bundle()
    bundle.episode = episode
    audit = audit_rl_episode_v221_pit(bundle)
    assert audit["valid"] is True
    assert audit["point_in_time"] is True
