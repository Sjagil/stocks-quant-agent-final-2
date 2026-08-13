from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from stocks.capabilities import CapabilityRegistry


@dataclass(frozen=True)
class ResearchStage:
    name: str
    purpose: str
    engines: tuple[str, ...]


class ResearchPipeline:
    def __init__(
        self,
        stages: tuple[ResearchStage, ...],
        *,
        capabilities: CapabilityRegistry,
    ) -> None:
        self.stages = stages
        self.capabilities = capabilities
        self._validate()

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        capabilities: CapabilityRegistry,
    ) -> "ResearchPipeline":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if int(raw.get("schema_version", 0)) != 1:
            raise ValueError("research pipeline schema_version must be 1")

        stages = tuple(
            ResearchStage(
                name=name,
                purpose=str(item.get("purpose", "")),
                engines=tuple(str(x) for x in item.get("engines", ())),
            )
            for name, item in dict(raw.get("stages") or {}).items()
        )
        return cls(stages, capabilities=capabilities)

    def _validate(self) -> None:
        known = set(self.capabilities.names())
        used: set[str] = set()
        for stage in self.stages:
            unknown = set(stage.engines) - known
            if unknown:
                raise ValueError(
                    f"{stage.name}: unknown capability engines: "
                    + ", ".join(sorted(unknown))
                )
            used.update(stage.engines)

        missing = known - used
        if missing:
            raise ValueError(
                "capabilities missing from research pipeline: "
                + ", ".join(sorted(missing))
            )

    def engines(self) -> tuple[str, ...]:
        result: list[str] = []
        for stage in self.stages:
            for engine in stage.engines:
                if engine not in result:
                    result.append(engine)
        return tuple(result)
