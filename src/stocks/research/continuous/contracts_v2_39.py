from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

AUTHORITY_NONE = "NONE"

class ResearchRole(str, Enum):
    CANDIDATE = "CANDIDATE"
    CHALLENGER = "CHALLENGER"
    CHAMPION = "CHAMPION"
    RETIRED = "RETIRED"

class ResearchHealth(str, Enum):
    NEW = "NEW"
    HEALTHY = "HEALTHY"
    WATCH = "WATCH"
    DEGRADED = "DEGRADED"
    QUARANTINED = "QUARANTINED"
    RETIRED = "RETIRED"

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DEADLETTER = "DEADLETTER"

@dataclass(frozen=True)
class EntityV239:
    entity_id: str
    entity_type: str
    family: str = "UNKNOWN"
    source: str = "MANUAL"
    version: str = ""
    role: str = ResearchRole.CANDIDATE.value
    health: str = ResearchHealth.NEW.value
    metadata: dict[str, Any] | None = None
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self):
        if not self.entity_id.strip():
            raise ValueError("entity_id required")
        if self.role not in {x.value for x in ResearchRole}:
            raise ValueError("invalid research role")
        if self.health not in {x.value for x in ResearchHealth}:
            raise ValueError("invalid research health")
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("research entities cannot grant execution authority")

@dataclass(frozen=True)
class EvidenceRecordV239:
    entity_id: str
    evidence_type: str
    as_of: str
    metrics: dict[str, Any]
    source: str
    source_ref: str
    sample_count: int = 0
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self):
        if not self.entity_id or not self.evidence_type or not self.source_ref:
            raise ValueError("evidence identity fields required")
        if self.sample_count < 0:
            raise ValueError("sample_count must be >= 0")
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("evidence cannot grant execution authority")

    def as_dict(self):
        return asdict(self)

@dataclass(frozen=True)
class HealthAssessmentV239:
    entity_id: str
    health: str
    recommendation: str
    score: float
    reasons: tuple[str, ...]
    posterior_net_edge_bps: float | None = None
    shadow_trades: int = 0
    independent_sources: int = 0
    drift_severity: float = 0.0
    decay_severity: float = 0.0
    disagreement: float = 0.0
    execution_authority: str = AUTHORITY_NONE

    def as_dict(self):
        return asdict(self)

__all__ = [
    "AUTHORITY_NONE", "EntityV239", "EvidenceRecordV239", "HealthAssessmentV239",
    "JobStatus", "ResearchHealth", "ResearchRole",
]
