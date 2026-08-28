from __future__ import annotations

import numpy as np
import pandas as pd


def brier_score(probability: pd.Series, outcome: pd.Series) -> float:
    frame = pd.concat(
        [
            pd.to_numeric(probability, errors="coerce").rename("p"),
            pd.to_numeric(outcome, errors="coerce").rename("y"),
        ],
        axis=1,
    ).dropna()
    if frame.empty:
        return float("nan")
    if ((frame["p"] < 0) | (frame["p"] > 1)).any():
        raise ValueError("probabilities must be in [0,1]")
    return float(np.mean(np.square(frame["p"] - frame["y"])))


def pinball_loss(actual: pd.Series, forecast: pd.Series, *, quantile: float) -> float:
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must be in (0,1)")
    frame = pd.concat(
        [
            pd.to_numeric(actual, errors="coerce").rename("y"),
            pd.to_numeric(forecast, errors="coerce").rename("q"),
        ],
        axis=1,
    ).dropna()
    if frame.empty:
        return float("nan")
    error = frame["y"] - frame["q"]
    return float(np.mean(np.maximum(quantile * error, (quantile - 1.0) * error)))


def quantile_coverage(actual: pd.Series, forecast: pd.Series) -> float:
    frame = pd.concat(
        [
            pd.to_numeric(actual, errors="coerce").rename("y"),
            pd.to_numeric(forecast, errors="coerce").rename("q"),
        ],
        axis=1,
    ).dropna()
    return float("nan") if frame.empty else float((frame["y"] <= frame["q"]).mean())


def expected_calibration_error(
    probability: pd.Series,
    outcome: pd.Series,
    *,
    bins: int = 10,
) -> float:
    if bins < 2:
        raise ValueError("bins must be >= 2")
    frame = pd.concat(
        [
            pd.to_numeric(probability, errors="coerce").rename("p"),
            pd.to_numeric(outcome, errors="coerce").rename("y"),
        ],
        axis=1,
    ).dropna()
    if frame.empty:
        return float("nan")
    if ((frame["p"] < 0) | (frame["p"] > 1)).any():
        raise ValueError("probabilities must be in [0,1]")
    edges = np.linspace(0.0, 1.0, bins + 1)
    bucket = np.minimum(np.digitize(frame["p"], edges[1:-1], right=False), bins - 1)
    total = len(frame)
    error = 0.0
    for idx in range(bins):
        mask = bucket == idx
        if not np.any(mask):
            continue
        observed = float(frame.loc[mask, "y"].mean())
        predicted = float(frame.loc[mask, "p"].mean())
        error += float(mask.sum()) / total * abs(observed - predicted)
    return float(error)
