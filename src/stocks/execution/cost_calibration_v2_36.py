from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class CostCalibrationV236:
    observations: int
    scale: float
    bias_bps: float
    mae_bps: float
    rmse_bps: float
    median_absolute_percentage_error: float
    status: str
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def calibrate_cost_scale(
    predicted_bps,
    observed_bps,
    *,
    min_observations: int = 20,
) -> CostCalibrationV236:
    frame = pd.DataFrame({
        "predicted": pd.to_numeric(pd.Series(predicted_bps), errors="coerce"),
        "observed": pd.to_numeric(pd.Series(observed_bps), errors="coerce"),
    }).replace([np.inf, -np.inf], np.nan).dropna()
    frame = frame[(frame.predicted > 0) & (frame.observed >= 0)]
    observations = len(frame)
    if observations == 0:
        return CostCalibrationV236(
            0, 1.0, float("nan"), float("nan"), float("nan"), float("nan"), "NO_OBSERVATIONS"
        )
    ratios = (frame.observed / frame.predicted).clip(0.25, 4.0)
    scale = float(ratios.median())
    calibrated = frame.predicted * scale
    error = frame.observed - calibrated
    bias = float(error.mean())
    mae = float(error.abs().mean())
    rmse = float(np.sqrt(np.mean(np.square(error))))
    denominator = frame.observed.replace(0, np.nan)
    mape_series = (error.abs() / denominator).dropna()
    mape = float(mape_series.median()) if not mape_series.empty else float("nan")
    status = "CALIBRATED" if observations >= min_observations else "CALIBRATION_PENDING"
    return CostCalibrationV236(observations, scale, bias, mae, rmse, mape, status)

__all__ = ["CostCalibrationV236", "calibrate_cost_scale"]
