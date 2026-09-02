from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from .feature_registry_v2_31 import FeatureRegistry, default_feature_registry
from .strategy_dna_v2_32 import StrategyDNA


@dataclass(frozen=True)
class StrategyFeasibility:
    dna_id: str
    status: str
    blockers: tuple[str, ...]
    missing_features: tuple[str, ...]
    non_promoted_features: tuple[str, ...]
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def promoted_feature_ids(governance: Mapping[str, Mapping[str, object]] | Mapping[str, object]) -> set[str]:
    promoted: set[str] = set()
    for key, value in governance.items():
        if isinstance(value, Mapping):
            status = str(value.get("status", ""))
        else:
            status = str(value)
        if status == "PROMOTE_RESEARCH":
            promoted.add(str(key))
    return promoted


def evaluate_strategy_feasibility(
    dna: StrategyDNA,
    *,
    governance: Mapping[str, Mapping[str, object]] | Mapping[str, object],
    registry: FeatureRegistry | None = None,
    require_promoted_features: bool = True,
    max_complexity: int = 8,
) -> StrategyFeasibility:
    reg = registry or default_feature_registry()
    registered = set(reg.ids())
    features = set(dna.all_feature_ids)
    missing = tuple(sorted(features - registered))
    promoted = promoted_feature_ids(governance)
    non_promoted = tuple(sorted(features - promoted)) if require_promoted_features else ()
    blockers: list[str] = []
    if missing:
        blockers.append("UNREGISTERED_FEATURE")
    if non_promoted:
        blockers.append("FEATURE_NOT_PROMOTED")
    if dna.complexity > max_complexity:
        blockers.append("COMPLEXITY_EXCEEDED")
    if dna.sizing.leverage_allowed:
        blockers.append("LEVERAGE_FORBIDDEN")
    if dna.execution_authority != "NONE":
        blockers.append("EXECUTION_AUTHORITY_FORBIDDEN")
    if dna.research_compliance_gate_applied:
        blockers.append("RESEARCH_COMPLIANCE_GATE_FORBIDDEN")
    return StrategyFeasibility(
        dna_id=dna.dna_id,
        status="ELIGIBLE_RESEARCH" if not blockers else "REJECTED_RESEARCH",
        blockers=tuple(dict.fromkeys(blockers)),
        missing_features=missing,
        non_promoted_features=non_promoted,
    )


__all__ = ["StrategyFeasibility", "evaluate_strategy_feasibility", "promoted_feature_ids"]
