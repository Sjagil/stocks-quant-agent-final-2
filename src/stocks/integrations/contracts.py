from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

PROTOCOL_VERSION = "1.0"
_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class IntegrationKind(str, Enum):
    ISOLATED_PYTHON = "isolated_python"


class IntegrationState(str, Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ArtifactRef:
    path: str
    media_type: str = "application/octet-stream"
    sha256: str | None = None
    rows: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("artifact path cannot be empty")
        if self.rows is not None and self.rows < 0:
            raise ValueError("artifact rows cannot be negative")


@dataclass(frozen=True)
class IntegrationSpec:
    name: str
    enabled: bool
    kind: IntegrationKind
    python: Path
    worker: Path
    repo: Path | None = None
    timeout_seconds: int = 120
    required: bool = False
    inherit_env: tuple[str, ...] = ("HOME", "PATH", "TMPDIR", "LANG", "LC_ALL", "TZ")
    pass_env: tuple[str, ...] = ()
    distributions: tuple[str, ...] = ()
    imports: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    upgrade: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _NAME_RE.match(self.name):
            raise ValueError(f"invalid integration name: {self.name!r}")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True)
class WorkerRequest:
    integration: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    protocol_version: str = PROTOCOL_VERSION
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if not _NAME_RE.match(self.integration):
            raise ValueError(f"invalid integration name: {self.integration!r}")
        if not self.action or not isinstance(self.action, str):
            raise ValueError("action must be a non-empty string")
        if self.protocol_version != PROTOCOL_VERSION:
            raise ValueError(f"unsupported protocol version: {self.protocol_version}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "WorkerRequest":
        return cls(
            integration=str(raw["integration"]),
            action=str(raw["action"]),
            payload=dict(raw.get("payload") or {}),
            context=dict(raw.get("context") or {}),
            request_id=str(raw.get("request_id") or uuid.uuid4().hex),
            protocol_version=str(raw.get("protocol_version") or PROTOCOL_VERSION),
            created_at=str(raw.get("created_at") or utc_now_iso()),
        )


@dataclass(frozen=True)
class WorkerResponse:
    integration: str
    action: str
    request_id: str
    state: IntegrationState
    data: dict[str, Any] = field(default_factory=dict)
    artifacts: tuple[ArtifactRef, ...] = ()
    warnings: tuple[str, ...] = ()
    error: str | None = None
    protocol_version: str = PROTOCOL_VERSION
    completed_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if self.protocol_version != PROTOCOL_VERSION:
            raise ValueError(f"unsupported protocol version: {self.protocol_version}")
        if self.state is IntegrationState.ERROR and not self.error:
            raise ValueError("ERROR responses must include an error message")

    @property
    def ok(self) -> bool:
        return self.state in {IntegrationState.OK, IntegrationState.DEGRADED}

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["state"] = self.state.value
        return raw

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "WorkerResponse":
        artifacts = tuple(ArtifactRef(**dict(item)) for item in (raw.get("artifacts") or []))
        return cls(
            integration=str(raw["integration"]),
            action=str(raw["action"]),
            request_id=str(raw["request_id"]),
            state=IntegrationState(str(raw["state"])),
            data=dict(raw.get("data") or {}),
            artifacts=artifacts,
            warnings=tuple(str(x) for x in (raw.get("warnings") or [])),
            error=str(raw["error"]) if raw.get("error") else None,
            protocol_version=str(raw.get("protocol_version") or PROTOCOL_VERSION),
            completed_at=str(raw.get("completed_at") or utc_now_iso()),
        )
