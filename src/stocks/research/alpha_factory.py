from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stocks.capabilities import CapabilityRegistry

from .contracts import AlphaHypothesis, AlphaResearchPlan, ResearchTask
from .pipeline import ResearchPipeline


class AlphaFactory:
    def __init__(
        self,
        project_root: str | Path,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.capabilities = CapabilityRegistry.load(
            self.project_root / "config" / "capabilities.yaml",
            project_root=self.project_root,
        )
        self.pipeline = ResearchPipeline.load(
            self.project_root / "config" / "research_pipeline.yaml",
            capabilities=self.capabilities,
        )

    def create_plan(self, hypothesis: AlphaHypothesis) -> AlphaResearchPlan:
        tasks: list[ResearchTask] = []
        for stage in self.pipeline.stages:
            for engine in stage.engines:
                spec = self.capabilities.get(engine)
                tasks.append(
                    ResearchTask(
                        stage=stage.name,
                        engine=engine,
                        mode=spec.mode.value,
                        purpose=stage.purpose,
                    )
                )
        return AlphaResearchPlan.create(
            hypothesis_id=hypothesis.hypothesis_id,
            tasks=tuple(tasks),
        )

    def capability_status(self) -> dict[str, Any]:
        health = self.capabilities.health_all()
        ok = sum(item.ok for item in health.values())
        return {
            "schema": "alpha_factory_capability_status_v1",
            "status": "OK" if ok == len(health) else "DEGRADED",
            "available": ok,
            "total": len(health),
            "pipeline_engines": list(self.pipeline.engines()),
            "capabilities": {
                name: item.as_dict()
                for name, item in health.items()
            },
        }

    def write_status(self) -> Path:
        output = self.project_root / "artifacts" / "alpha_factory"
        output.mkdir(parents=True, exist_ok=True)
        path = output / "capability_status.json"
        path.write_text(
            json.dumps(self.capability_status(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def write_plan(self, plan: AlphaResearchPlan) -> Path:
        output = (
            self.project_root
            / "artifacts"
            / "alpha_factory"
            / "plans"
        )
        output.mkdir(parents=True, exist_ok=True)
        path = output / f"{plan.hypothesis_id}.json"
        path.write_text(
            json.dumps(plan.as_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path
