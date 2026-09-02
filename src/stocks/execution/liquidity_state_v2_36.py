from __future__ import annotations
from dataclasses import asdict, dataclass
from .cost_contracts_v2_36 import ExecutionCostPolicyV236, LiquidityBucket, MarketStateV236

@dataclass(frozen=True)
class LiquidityAssessmentV236:
    bucket: str
    participation_rate: float
    capacity_notional: float
    capacity_ratio: float
    blockers: tuple[str, ...]
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def classify_liquidity(state: MarketStateV236) -> LiquidityBucket:
    adv = state.adv20_notional
    spread = state.spread_bps
    if adv >= 100_000_000 and spread <= 8: return LiquidityBucket.DEEP
    if adv >= 25_000_000 and spread <= 20: return LiquidityBucket.HIGH
    if adv >= 5_000_000 and spread <= 40: return LiquidityBucket.MEDIUM
    if adv >= 1_000_000 and spread <= 80: return LiquidityBucket.LOW
    return LiquidityBucket.VERY_LOW

def assess_liquidity(notional: float, state: MarketStateV236, policy: ExecutionCostPolicyV236 | None = None) -> LiquidityAssessmentV236:
    cfg = policy or ExecutionCostPolicyV236()
    participation = float(notional / state.adv20_notional)
    capacity = min(cfg.max_adv_fraction, cfg.max_participation_rate) * state.adv20_notional
    blockers = []
    if state.adv20_notional < cfg.minimum_adv_notional: blockers.append("ADV_TOO_LOW")
    if state.data_quality_score < cfg.minimum_data_quality: blockers.append("DATA_QUALITY_LOW")
    if participation > cfg.max_adv_fraction + 1e-12: blockers.append("ADV_FRACTION_EXCEEDED")
    if participation > cfg.max_participation_rate + 1e-12: blockers.append("PARTICIPATION_RATE_EXCEEDED")
    bucket = classify_liquidity(state).value
    if bucket == "VERY_LOW": blockers.append("VERY_LOW_LIQUIDITY")
    return LiquidityAssessmentV236(
        bucket, participation, float(capacity), float(capacity / max(notional, 1e-12)),
        tuple(dict.fromkeys(blockers)),
    )

__all__ = ["LiquidityAssessmentV236", "assess_liquidity", "classify_liquidity"]
