from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

AUTHORITY_NONE = "NONE"


@dataclass(frozen=True)
class ProductionInputAuditV2393:
    entity_id: str
    adapter: str
    status: str
    ready: bool
    reasons: tuple[str, ...]
    details: dict[str, Any]
    execution_authority: str = AUTHORITY_NONE

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OOSProductionResultV2393:
    entity_id: str
    status: str
    raw_trades: int
    effective_observations: int
    folds: int
    net_expectancy_bps: float | None
    profit_factor: float | None
    passed: bool
    observations_path: str | None
    evidence_path: str | None
    provenance_hash: str | None
    reasons: tuple[str, ...] = ()
    execution_authority: str = AUTHORITY_NONE

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CostStressProductionResultV2393:
    entity_id: str
    status: str
    required_multiplier: float
    max_positive_multiplier: float
    effective_observations: int
    required_multiplier_passed: bool
    scenarios_path: str | None
    evidence_path: str | None
    reasons: tuple[str, ...] = ()
    execution_authority: str = AUTHORITY_NONE

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceProductionResultV2393:
    entity_id: str
    status: str
    input_audit: dict[str, Any]
    oos: dict[str, Any] | None
    cost_stress: dict[str, Any] | None
    evidence_added: int
    before_assessment: dict[str, Any] | None
    after_assessment: dict[str, Any] | None
    output_dir: str
    execution_authority: str = AUTHORITY_NONE

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "AUTHORITY_NONE",
    "ProductionInputAuditV2393",
    "OOSProductionResultV2393",
    "CostStressProductionResultV2393",
    "EvidenceProductionResultV2393",
]
