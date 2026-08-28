from __future__ import annotations

from dataclasses import asdict, dataclass

from .strategy_dna_v2_32 import StrategyDNA
from .strategy_provenance_v2_32 import StrategyProvenance


VALIDATION_STAGES = (
    "FAST_DISCOVERY",
    "PARAMETER_SEARCH",
    "PURGED_WALK_FORWARD",
    "COST_STRESS",
    "CROSS_ENGINE_VALIDATION",
    "FORWARD_SHADOW",
)


@dataclass(frozen=True)
class StrategyResearchHandoff:
    dna_id: str
    family: str
    priority_score: float
    frozen_parameters: dict[str, object]
    validation_stages: tuple[str, ...]
    generic_feature_panel_executable: bool
    provenance: dict[str, object]
    research_stage: str = "AWAITING_VALIDATION"
    automatic_live_promotion: bool = False
    broker_submission_enabled: bool = False
    order_calls: int = 0
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def build_research_handoff(dna: StrategyDNA, provenance: StrategyProvenance, *, priority_score: float) -> StrategyResearchHandoff:
    return StrategyResearchHandoff(
        dna_id=dna.dna_id,
        family=dna.family,
        priority_score=float(priority_score),
        frozen_parameters=dict(dna.parameters),
        validation_stages=VALIDATION_STAGES,
        generic_feature_panel_executable=True,
        provenance=provenance.as_dict(),
    )


__all__ = ["StrategyResearchHandoff", "VALIDATION_STAGES", "build_research_handoff"]
