#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from stocks.research.forecast_calibration_v2_30 import pinball_loss, quantile_coverage
from stocks.research.purged_walkforward_v2_30 import PurgedWalkForwardConfig
from stocks.research.walkforward_forecast_v2_30 import walkforward_quantile_forecast

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/research_runtime/forward_forecast_v2_30"


def main() -> int:
    rng = np.random.default_rng(23030)
    n = 900
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    noise = rng.normal(scale=0.01, size=n)
    target = pd.Series(0.01 * x1 - 0.005 * x2 + noise)
    features = pd.DataFrame({"x1": x1, "x2": x2})

    result = walkforward_quantile_forecast(
        features,
        target,
        label_horizon_bars=5,
        split_config=PurgedWalkForwardConfig(
            minimum_train_size=500,
            test_size=100,
            step_size=100,
            purge_bars=5,
        ),
    )
    predictions = result.predictions.dropna(subset=["label"])
    if result.folds < 1 or predictions.empty:
        raise AssertionError("walk-forward forecast produced no OOS predictions")
    if not ((predictions["q10"] <= predictions["q50"]) & (predictions["q50"] <= predictions["q90"])).all():
        raise AssertionError("quantile crossing detected after projection")

    payload = {
        "schema": "forward_forecast_selfcheck_v2_30",
        "folds": result.folds,
        "oos_rows": int(len(predictions)),
        "q10_coverage": quantile_coverage(predictions["label"], predictions["q10"]),
        "q90_coverage": quantile_coverage(predictions["label"], predictions["q90"]),
        "q50_pinball": pinball_loss(predictions["label"], predictions["q50"], quantile=0.50),
        "random_shuffle": False,
        "broker_submission_enabled": False,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    target_path = OUT / "selfcheck.json"
    target_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("FORWARD_FORECAST_V2_30_SELFCHECK OK")
    print("FOLDS", result.folds)
    print("OOS_ROWS", len(predictions))
    print("QUANTILE_CROSSING False")
    print("RANDOM_SHUFFLE False")
    print("BROKER_SUBMISSION_ENABLED False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT", target_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
