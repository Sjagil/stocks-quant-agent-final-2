from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .feature_ic_v2_28 import cross_sectional_ic_series, summarize_ic


@dataclass(frozen=True)
class RegimeFeatureValue:
    feature_id: str
    regime: str
    regime_periods: int
    global_mean_ic: float
    regime_mean_ic: float
    shrunk_mean_ic: float
    confidence: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def regime_conditioned_feature_value(
    panel: pd.DataFrame,
    *,
    feature_id: str,
    date_column: str,
    target_column: str,
    regime_column: str,
    shrinkage_periods: float = 20.0,
) -> tuple[RegimeFeatureValue, ...]:
    required = {feature_id, date_column, target_column, regime_column}
    missing = required.difference(panel.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    if shrinkage_periods <= 0:
        raise ValueError("shrinkage_periods must be positive")

    global_ic = cross_sectional_ic_series(
        panel,
        date_column=date_column,
        feature_column=feature_id,
        target_column=target_column,
        rank=True,
    )
    global_summary = summarize_ic(global_ic)
    global_mean = float(global_summary.mean_ic) if np.isfinite(global_summary.mean_ic) else 0.0

    outputs: list[RegimeFeatureValue] = []
    for regime, subset in panel.groupby(regime_column, sort=True):
        ic = cross_sectional_ic_series(
            subset,
            date_column=date_column,
            feature_column=feature_id,
            target_column=target_column,
            rank=True,
        )
        summary = summarize_ic(ic)
        n = int(summary.periods)
        regime_mean = float(summary.mean_ic) if np.isfinite(summary.mean_ic) else 0.0
        weight = n / (n + shrinkage_periods)
        shrunk = weight * regime_mean + (1.0 - weight) * global_mean
        confidence = float(np.clip(weight * max(summary.positive_fraction, 1.0 - summary.positive_fraction), 0.0, 1.0)) if n else 0.0
        outputs.append(
            RegimeFeatureValue(
                feature_id=feature_id,
                regime=str(regime),
                regime_periods=n,
                global_mean_ic=global_mean,
                regime_mean_ic=regime_mean,
                shrunk_mean_ic=float(shrunk),
                confidence=confidence,
            )
        )
    return tuple(outputs)


def current_regime_multiplier(
    values: tuple[RegimeFeatureValue, ...] | list[RegimeFeatureValue],
    *,
    current_regime: str,
    scale: float = 10.0,
) -> float:
    match = next((row for row in values if row.regime == str(current_regime)), None)
    if match is None:
        return 0.5
    signed_strength = abs(match.shrunk_mean_ic) * float(scale)
    return float(np.clip(match.confidence * min(1.0, signed_strength), 0.0, 1.0))


__all__ = ["RegimeFeatureValue", "current_regime_multiplier", "regime_conditioned_feature_value"]
