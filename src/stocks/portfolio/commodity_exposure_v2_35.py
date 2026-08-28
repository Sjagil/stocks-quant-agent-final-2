from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import numpy as np

@dataclass(frozen=True)
class CommodityCurveMetrics:
    commodity: str
    front_price: float
    second_price: float
    days_between_contracts: float
    curve_slope: float
    annualized_roll_yield: float
    backwardation: bool
    inventory_z: float | None
    trend_score: float | None
    usd_score: float | None
    real_rate_score: float | None
    regime_score: float
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def commodity_curve_metrics(
    commodity: str, front_price: float, second_price: float, days_between_contracts: float,
    *, inventory_z: float | None=None, trend_score: float | None=None,
    usd_score: float | None=None, real_rate_score: float | None=None,
) -> CommodityCurveMetrics:
    f=float(front_price); s=float(second_price); days=float(days_between_contracts)
    if f<=0 or s<=0 or days<=0: raise ValueError("prices and days_between_contracts must be positive")
    slope=s/f-1.0
    roll=(f/s-1.0)*(365.25/days)
    parts=[float(np.tanh(roll*2.0))]
    if trend_score is not None and np.isfinite(trend_score): parts.append(float(np.clip(trend_score,-1,1)))
    if inventory_z is not None and np.isfinite(inventory_z): parts.append(float(np.tanh(-float(inventory_z)/2.0)))
    if usd_score is not None and np.isfinite(usd_score): parts.append(float(np.clip(-float(usd_score),-1,1)))
    if real_rate_score is not None and np.isfinite(real_rate_score): parts.append(float(np.clip(-float(real_rate_score),-1,1)))
    regime=float(np.mean(parts))
    return CommodityCurveMetrics(str(commodity).upper(),f,s,days,float(slope),float(roll),bool(f>s),
        None if inventory_z is None else float(inventory_z),None if trend_score is None else float(trend_score),
        None if usd_score is None else float(usd_score),None if real_rate_score is None else float(real_rate_score),regime)

__all__=["CommodityCurveMetrics","commodity_curve_metrics"]
