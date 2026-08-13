from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def sha256_file(
    path: str | Path,
) -> str:
    digest = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


@dataclass(frozen=True)
class EngineArtifact:
    engine: str
    stage: str
    artifact_kind: str
    hypothesis_id: str

    symbols: tuple[str, ...] = ()
    timeframes: tuple[str, ...] = ()

    periods: dict[str, Any] = field(
        default_factory=dict
    )

    input_hashes: dict[str, str] = field(
        default_factory=dict
    )

    metrics: dict[str, Any] = field(
        default_factory=dict
    )

    payload: dict[str, Any] = field(
        default_factory=dict
    )

    provenance: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: tuple[str, ...] = ()

    lookahead_safe: bool = False
    costs_included: bool = False

    execution_authority: str = "NONE"
    broker_order_calls: int = 0

    created_at: str = field(
        default_factory=utc_now_iso
    )

    schema: str = "engine_artifact_v1"

    def __post_init__(self) -> None:
        if not self.engine.strip():
            raise ValueError(
                "engine is required"
            )

        if not self.stage.strip():
            raise ValueError(
                "stage is required"
            )

        if not self.artifact_kind.strip():
            raise ValueError(
                "artifact_kind is required"
            )

        if not self.hypothesis_id.strip():
            raise ValueError(
                "hypothesis_id is required"
            )

        if self.execution_authority != "NONE":
            raise ValueError(
                "research engine artifacts must "
                "have execution_authority=NONE"
            )

        if self.broker_order_calls != 0:
            raise ValueError(
                "research engine artifacts may "
                "not contain broker order calls"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(
        self,
        path: str | Path,
    ) -> Path:
        output = Path(path)

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output.write_text(
            json.dumps(
                self.to_dict(),
                indent=2,
                sort_keys=True,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )

        return output
