from __future__ import annotations

import numpy as np
import pandas as pd

from stocks.research.forward_forecaster_v2_30 import ForwardForecastConfig, ForwardQuantileForecaster
from stocks.research.purged_walkforward_v2_30 import PurgedWalkForwardConfig
from stocks.research.walkforward_forecast_v2_30 import walkforward_quantile_forecast


def test_forecaster_quantiles_are_monotonic():
    rng = np.random.default_rng(123)
    n = 250
    x = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n)})
    y = 0.02 * x["a"] - 0.01 * x["b"] + rng.normal(scale=0.01, size=n)
    model = ForwardQuantileForecaster(ForwardForecastConfig(max_iter=60)).fit(x.iloc[:180], y.iloc[:180])
    pred = model.predict(x.iloc[180:])
    assert ((pred["q10"] <= pred["q50"]) & (pred["q50"] <= pred["q90"])).all()
    assert pred["interval_width"].ge(0).all()


def test_walkforward_is_oos_and_purged():
    rng = np.random.default_rng(321)
    n = 420
    x = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n)})
    y = pd.Series(0.01 * x["a"] + rng.normal(scale=0.02, size=n))
    result = walkforward_quantile_forecast(
        x,
        y,
        label_horizon_bars=5,
        split_config=PurgedWalkForwardConfig(
            minimum_train_size=200,
            test_size=50,
            step_size=50,
            purge_bars=5,
        ),
        model_config=ForwardForecastConfig(max_iter=40),
    )
    assert result.folds >= 3
    assert result.execution_authority == "NONE"
    assert not result.predictions.empty
