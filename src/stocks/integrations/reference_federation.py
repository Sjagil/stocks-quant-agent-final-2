from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


EXPECTED_ENGINES = {
    "FinRL-Trading",
    "Kronos",
    "Lean",
    "MoonDev-Trading-Ai-Agents",
    "nautilus_trader",
    "optuna",
    "pybroker",
    "qlib",
    "skfolio",
    "stable-baselines3-contrib",
    "Stocks",
    "vectorbt",
    "vnpy",
    "vnpy_ib",
}


@dataclass(frozen=True)
class FederationAudit:
    declared_engines: int
    missing_engine_names: tuple[str, ...]
    extra_engine_names: tuple[str, ...]
    invalid_authority_engines: tuple[str, ...]
    direct_writer_violations: tuple[str, ...]
    optuna_test_access: bool
    whole_shares_only: bool
    fixed_euro_order_cap: bool
    canonical_broker_writer: str

    @property
    def ok(self) -> bool:
        return not (
            self.missing_engine_names
            or self.extra_engine_names
            or self.invalid_authority_engines
            or self.direct_writer_violations
            or self.optuna_test_access
            or not self.whole_shares_only
            or self.fixed_euro_order_cap
            or not self.canonical_broker_writer
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "declared_engines": self.declared_engines,
            "missing_engine_names": list(self.missing_engine_names),
            "extra_engine_names": list(self.extra_engine_names),
            "invalid_authority_engines": list(self.invalid_authority_engines),
            "direct_writer_violations": list(self.direct_writer_violations),
            "optuna_test_access": self.optuna_test_access,
            "whole_shares_only": self.whole_shares_only,
            "fixed_euro_order_cap": self.fixed_euro_order_cap,
            "canonical_broker_writer": self.canonical_broker_writer,
            "ok": self.ok,
        }


def load_reference_federation(
    project_root: str | Path,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    path = root / "config/reference_engine_federation_v2_16.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if payload.get("schema") != "reference_engine_federation_v2_16":
        raise ValueError("unexpected reference federation schema")
    return payload


def audit_reference_federation(
    project_root: str | Path,
) -> FederationAudit:
    payload = load_reference_federation(project_root)
    engines = dict(payload.get("engines") or {})
    declared = set(engines)
    global_policy = dict(payload.get("global_policy") or {})
    optimization = dict(payload.get("optimization_policy") or {})

    invalid_authority = []
    direct_writer = []
    for name, spec in engines.items():
        forbidden = {str(value) for value in spec.get("forbidden", [])}
        if "execution_authority" not in forbidden:
            invalid_authority.append(name)
        if "direct_broker_write" not in forbidden:
            direct_writer.append(name)

    optuna_forbidden = {
        str(value)
        for value in optimization.get("optuna_forbidden_segments", [])
    }

    return FederationAudit(
        declared_engines=len(declared),
        missing_engine_names=tuple(sorted(EXPECTED_ENGINES - declared)),
        extra_engine_names=tuple(sorted(declared - EXPECTED_ENGINES)),
        invalid_authority_engines=tuple(sorted(invalid_authority)),
        direct_writer_violations=tuple(sorted(direct_writer)),
        optuna_test_access=("test" not in optuna_forbidden),
        whole_shares_only=bool(global_policy.get("whole_shares_only")),
        fixed_euro_order_cap=bool(global_policy.get("fixed_euro_order_cap")),
        canonical_broker_writer=str(
            global_policy.get("canonical_broker_writer") or ""
        ),
    )
