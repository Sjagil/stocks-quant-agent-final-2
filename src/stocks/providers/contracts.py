from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class SourceState(StrEnum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    EMPTY = "EMPTY"
    DISABLED = "DISABLED"
    UNCONFIGURED = "UNCONFIGURED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class SourceProvenance:
    provider: str
    domain: str
    endpoint: str | None = None
    symbol: str | None = None
    provider_symbol: str | None = None
    retrieved_at: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class SourceResult:
    provider: str
    domain: str
    state: SourceState
    items: list[dict[str, Any]] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )
    error: str | None = None
    provenance: list[SourceProvenance] = field(
        default_factory=list
    )
    started_at: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )
    completed_at: str | None = None

    def finish(self) -> "SourceResult":
        self.completed_at = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "domain": self.domain,
            "state": str(self.state),
            "items": self.items,
            "warnings": self.warnings,
            "error": self.error,
            "provenance": [
                asdict(item)
                for item in self.provenance
            ],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
