from __future__ import annotations
from dataclasses import asdict, dataclass
import math
import numpy as np

@dataclass(frozen=True)
class DynamicRiskStateV234:
    drawdown: float = 0.0
    drawdown_velocity: float = 0.0
    realized_volatility: float = 0.10
    target_volatility: float = 0.12
    regime_confidence: float = 1.0
    liquidity_score: float = 1.0
    data_quality_score: float = 1.0
    loss_guard_score: float = 1.0

@dataclass(frozen=True)
class DynamicRiskOverlayV234:
    exposure_multiplier: float
    multipliers: dict[str,float]
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def _unit(x: float) -> float: return float(np.clip(float(x),0.0,1.0))

def dynamic_risk_overlay(state: DynamicRiskStateV234, *, max_drawdown_guard: float=0.15, min_exposure_multiplier: float=0.0) -> DynamicRiskOverlayV234:
    if max_drawdown_guard <= 0: raise ValueError("max_drawdown_guard must be positive")
    if not 0 <= min_exposure_multiplier <= 1: raise ValueError("invalid minimum multiplier")
    dd=max(0.0,float(state.drawdown)); velocity=max(0.0,float(state.drawdown_velocity))
    m_dd=_unit(1.0-dd/max_drawdown_guard)
    m_vel=float(np.clip(math.exp(-12.0*velocity),0.25,1.0))
    rv=max(float(state.realized_volatility),1e-12); tv=max(float(state.target_volatility),1e-12)
    m_vol=float(np.clip(tv/rv,0.25,1.0))
    m_regime=0.50+0.50*_unit(state.regime_confidence)
    m_liq=float(np.clip(state.liquidity_score,0.25,1.0)); m_data=float(np.clip(state.data_quality_score,0.25,1.0)); m_loss=float(np.clip(state.loss_guard_score,0.25,1.0))
    parts={"drawdown":m_dd,"drawdown_velocity":m_vel,"volatility":m_vol,"regime":m_regime,"liquidity":m_liq,"data_quality":m_data,"loss_guard":m_loss}
    product=float(np.prod(list(parts.values())))
    return DynamicRiskOverlayV234(float(np.clip(product,min_exposure_multiplier,1.0)),parts)

__all__=["DynamicRiskStateV234","DynamicRiskOverlayV234","dynamic_risk_overlay"]
