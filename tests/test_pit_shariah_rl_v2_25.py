from __future__ import annotations

import numpy as np
import pandas as pd

from stocks.rl.contracts_v2_21 import PortfolioEpisodeV221
from stocks.rl.dataset_v2_21 import PortfolioDatasetBundleV221
from stocks.rl.pit_shariah_dataset_v2_25 import apply_pit_shariah_mask_v225
from stocks.rl.pit_shariah_pipeline_v2_25 import run_pit_shariah_rl_marl_pipeline_v225


def test_pit_shariah_mask_never_exposes_future_or_unknown_assets() -> None:
    timestamps = np.array(
        [
            "2024-01-01T00:00:00",
            "2024-01-02T00:00:00",
            "2024-01-03T00:00:00",
            "2024-01-04T00:00:00",
        ],
        dtype="datetime64[ns]",
    )
    episode = PortfolioEpisodeV221(
        local_observations=np.zeros((4, 2, 1), dtype=np.float32),
        global_observations=np.zeros((4, 1), dtype=np.float32),
        asset_returns=np.zeros((3, 2), dtype=np.float64),
        benchmark_returns=np.zeros(3, dtype=np.float64),
        tradable_mask=np.ones((4, 2), dtype=bool),
        timestamps=timestamps,
        feature_cutoffs=timestamps.copy(),
    )
    bundle = PortfolioDatasetBundleV221(
        episode=episode,
        symbols=("AAA", "BBB"),
        timeframe="1h",
        dataset_hash="a" * 64,
        source_files=(),
        source_hashes=(),
    )
    ledger = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "decision_time": "2024-01-02T00:00:00Z",
                "status": "SHARIAH_ELIGIBLE_VERIFIED",
                "trade_eligible": True,
            }
        ]
    )
    masked, audit = apply_pit_shariah_mask_v225(bundle, ledger)
    expected = np.array(
        [
            [False, False],
            [True, False],
            [True, False],
            [True, False],
        ],
        dtype=bool,
    )
    assert np.array_equal(masked.episode.tradable_mask, expected)
    assert audit["point_in_time"] is True
    assert audit["unknown_is_ineligible"] is True
    assert audit["shariah_mask_never_widens_base"] is True
    assert masked.dataset_hash != bundle.dataset_hash


def test_masked_training_runner_is_available() -> None:
    assert callable(run_pit_shariah_rl_marl_pipeline_v225)
