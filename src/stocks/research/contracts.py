from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


DEFAULT_SWING_TIMEFRAMES = ("15m", "1h", "2h", "4h", "1d", "1w")


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


@dataclass(frozen=True)
class AlphaHypothesis:
    family: str
    thesis: str
    symbols: tuple[str, ...]
    timeframes: tuple[str, ...] = DEFAULT_SWING_TIMEFRAMES
    data_domains: tuple[str, ...] = (
        "price",
        "technical",
        "fundamental",
        "news",
        "macro",
        "options",
        "gex",
        "cross_sectional",
    )
    parameters: dict[str, Any] | None = None

    @property
    def hypothesis_id(self) -> str:
        return "ALPHA-" + stable_hash(asdict(self))[:24]


@dataclass(frozen=True)
class ResearchTask:
    stage: str
    engine: str
    mode: str
    purpose: str


@dataclass(frozen=True)
class AlphaResearchPlan:
    hypothesis_id: str
    created_at: str
    tasks: tuple[ResearchTask, ...]
    execution_authority: str = "NONE"

    @classmethod
    def create(
        cls,
        *,
        hypothesis_id: str,
        tasks: tuple[ResearchTask, ...],
    ) -> "AlphaResearchPlan":
        return cls(
            hypothesis_id=hypothesis_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            tasks=tasks,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "created_at": self.created_at,
            "execution_authority": self.execution_authority,
            "tasks": [asdict(task) for task in self.tasks],
        }
