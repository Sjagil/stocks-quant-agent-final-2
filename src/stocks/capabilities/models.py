from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class CapabilityMode(StrEnum):
    DIRECT_PYTHON = "direct_python"
    INTEGRATION_WORKER = "integration_worker"
    CLI = "cli"
    SUBPROCESS_REFERENCE = "subprocess_reference"
    DONOR = "donor"


@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    mode: CapabilityMode
    roles: tuple[str, ...]
    description: str
    repo: Path | None = None
    module: str | None = None
    distribution: str | None = None
    integration: str | None = None
    executable: Path | None = None
    python: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityHealth:
    name: str
    mode: CapabilityMode
    status: str
    roles: tuple[str, ...]
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == "OK"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mode": self.mode.value,
            "status": self.status,
            "roles": list(self.roles),
            "details": self.details,
        }
