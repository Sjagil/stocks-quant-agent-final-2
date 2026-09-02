from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Mapping

@dataclass(frozen=True)
class GemScreenerPolicyV2351:
    min_market_cap: float = 150_000_000.0
    min_price: float = 2.0
    min_avg_dollar_volume_20d: float = 1_500_000.0
    min_data_quality_score: float = 0.70
    max_fundamentals_age_days: float = 180.0
    max_spread_bps: float = 80.0
    max_dilution_yoy: float = 0.25
    hard_pump_return: float = 0.35
    hard_pump_volume_ratio: float = 5.0
    min_news_diversity_for_extreme_move: float = 0.30
    min_component_coverage: float = 0.40
    tier_a_score: float = 75.0
    tier_b_score: float = 65.0
    watch_score: float = 55.0
    max_per_sector: int = 3
    max_per_industry: int = 2
    weights: Mapping[str,float] = field(default_factory=lambda:{
        "quality":0.20,"growth":0.18,"revisions":0.15,"value":0.15,
        "momentum":0.12,"forecast":0.12,"catalyst":0.08,
    })
    execution_authority: str = "NONE"

    def __post_init__(self):
        if abs(sum(self.weights.values())-1.0)>1e-8: raise ValueError("component weights must sum to 1")
        if self.execution_authority!="NONE": raise ValueError("screener cannot grant execution authority")

@dataclass(frozen=True)
class GemScreenSummary:
    total: int
    eligible: int
    tier_a: int
    tier_b: int
    watch: int
    rejected: int
    execution_authority: str="NONE"
    def as_dict(self): return asdict(self)

__all__=["GemScreenerPolicyV2351","GemScreenSummary"]
