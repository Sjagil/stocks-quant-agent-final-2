from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from stocks.capabilities import (
    CapabilityRegistry,
)


VALID_STATUSES = {
    "implemented",
    "planned",
    "donor",
}


@dataclass(frozen=True)
class ReferenceAction:
    engine: str
    name: str
    mode: str
    stage: str
    artifact_kind: str
    status: str

    def to_dict(self) -> dict[str, str]:
        return {
            "engine": self.engine,
            "name": self.name,
            "mode": self.mode,
            "stage": self.stage,
            "artifact_kind": (
                self.artifact_kind
            ),
            "status": self.status,
        }


class ReferenceActionRegistry:
    def __init__(
        self,
        actions: tuple[
            ReferenceAction,
            ...
        ],
        *,
        capabilities: CapabilityRegistry,
    ) -> None:
        self.actions = actions
        self.capabilities = capabilities
        self._validate()

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        capabilities: CapabilityRegistry,
    ) -> "ReferenceActionRegistry":
        raw = yaml.safe_load(
            Path(path).read_text(
                encoding="utf-8"
            )
        ) or {}

        if int(
            raw.get(
                "schema_version",
                0,
            )
        ) != 1:
            raise ValueError(
                "reference action "
                "schema_version must be 1"
            )

        rows: list[
            ReferenceAction
        ] = []

        for engine, engine_cfg in (
            dict(
                raw.get(
                    "engines"
                )
                or {}
            ).items()
        ):
            mode = str(
                engine_cfg.get(
                    "mode",
                    "",
                )
            )

            for action_name, action_cfg in (
                dict(
                    engine_cfg.get(
                        "actions"
                    )
                    or {}
                ).items()
            ):
                rows.append(
                    ReferenceAction(
                        engine=str(engine),
                        name=str(
                            action_name
                        ),
                        mode=mode,
                        stage=str(
                            action_cfg[
                                "stage"
                            ]
                        ),
                        artifact_kind=str(
                            action_cfg[
                                "artifact_kind"
                            ]
                        ),
                        status=str(
                            action_cfg[
                                "status"
                            ]
                        ),
                    )
                )

        return cls(
            tuple(rows),
            capabilities=capabilities,
        )

    def _validate(self) -> None:
        capability_names = set(
            self.capabilities.names()
        )

        action_engines = {
            row.engine
            for row in self.actions
        }

        missing = (
            capability_names
            - action_engines
        )

        extra = (
            action_engines
            - capability_names
        )

        if missing:
            raise ValueError(
                "reference engines missing "
                "actions: "
                + ", ".join(
                    sorted(missing)
                )
            )

        if extra:
            raise ValueError(
                "unknown reference engines: "
                + ", ".join(
                    sorted(extra)
                )
            )

        seen = set()

        for row in self.actions:
            key = (
                row.engine,
                row.name,
            )

            if key in seen:
                raise ValueError(
                    f"duplicate action: {key}"
                )

            seen.add(key)

            capability = (
                self.capabilities.get(
                    row.engine
                )
            )

            expected_mode = (
                capability.mode.value
            )

            if row.mode != expected_mode:
                raise ValueError(
                    f"{row.engine}: "
                    f"mode {row.mode!r} "
                    f"!= {expected_mode!r}"
                )

            if (
                row.status
                not in VALID_STATUSES
            ):
                raise ValueError(
                    f"{row.engine}: "
                    f"invalid status "
                    f"{row.status!r}"
                )

    def summary(self) -> dict[str, Any]:
        engines = {}

        for engine in (
            self.capabilities.names()
        ):
            rows = [
                row
                for row in self.actions
                if row.engine == engine
            ]

            engines[
                engine
            ] = {
                "mode": (
                    self.capabilities
                    .get(engine)
                    .mode
                    .value
                ),
                "actions": [
                    row.to_dict()
                    for row in rows
                ],
                "implemented": sum(
                    row.status
                    == "implemented"
                    for row in rows
                ),
                "planned": sum(
                    row.status
                    == "planned"
                    for row in rows
                ),
            }

        return {
            "schema": (
                "reference_action_status_v1"
            ),
            "engine_count": len(
                engines
            ),
            "action_count": len(
                self.actions
            ),
            "engines": engines,
        }
