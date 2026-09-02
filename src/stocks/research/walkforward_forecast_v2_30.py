from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .forward_forecaster_v2_30 import ForwardForecastConfig, ForwardQuantileForecaster
from .purged_walkforward_v2_30 import (
    PurgedWalkForwardConfig,
    assert_no_label_overlap,
    purged_walkforward_splits,
)


@dataclass(frozen=True)
class WalkForwardForecastResult:
    predictions: pd.DataFrame
    folds: int
    execution_authority: str = "NONE"


def walkforward_quantile_forecast(
    features: pd.DataFrame,
    target: pd.Series,
    *,
    label_horizon_bars: int,
    split_config: PurgedWalkForwardConfig | None = None,
    model_config: ForwardForecastConfig | None = None,
) -> WalkForwardForecastResult:
    if len(features) != len(target):
        target = target.reindex(features.index)
    active_split = split_config or PurgedWalkForwardConfig(purge_bars=label_horizon_bars)
    if active_split.purge_bars < label_horizon_bars:
        raise ValueError("purge_bars must be >= label_horizon_bars")
    splits = purged_walkforward_splits(len(features), config=active_split)
    outputs: list[pd.DataFrame] = []
    for fold, (train_idx, test_idx) in enumerate(splits):
        assert_no_label_overlap(train_idx, test_idx, label_horizon_bars=label_horizon_bars)
        model = ForwardQuantileForecaster(model_config)
        model.fit(features.iloc[train_idx], target.iloc[train_idx])
        pred = model.predict(features.iloc[test_idx])
        pred["fold"] = fold
        pred["label"] = pd.to_numeric(target.iloc[test_idx], errors="coerce").to_numpy()
        pred["decision_index"] = test_idx
        outputs.append(pred)
    combined = pd.concat(outputs).sort_index() if outputs else pd.DataFrame()
    return WalkForwardForecastResult(predictions=combined, folds=len(outputs))
