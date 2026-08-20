#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    registry = IntegrationRegistry.load(
        ROOT / "config/integrations.yaml",
        project_root=ROOT,
    )
    runner = IntegrationRunner(registry)

    mapping = {
        "pybroker": "pybroker_reference",
        "nautilus": "nautilus",
        "lean": "lean_reference",
        "stocks_donor": "stocks_donor_architecture",
    }

    rows = {}
    for engine, integration in mapping.items():
        result = runner.health(integration)
        rows[engine] = result
        print(
            "ENGINE", engine,
            "INTEGRATION", integration,
            "STATE", result.state.value,
            "DATA", result.data,
            "WARNINGS", result.warnings,
        )

    pybroker_ready = (
        rows["pybroker"].ok
        and "replay_intents"
        in rows["pybroker"].data.get("capabilities", [])
    )
    nautilus_ready = (
        rows["nautilus"].ok
        and "replay_intents"
        in rows["nautilus"].data.get("capabilities", [])
    )
    lean_full_ready = bool(
        rows["lean"].data.get("full_engine_replay_candidate", False)
    )
    donor_ready = rows["stocks_donor"].data.get("status") == "GO"

    core_ready = pybroker_ready and nautilus_ready and donor_ready
    promotion_runtime_ready = core_ready and lean_full_ready

    print(
        "CROSS_ENGINE_RUNTIME_AUDIT_V2_17_1",
        "CORE_READY", core_ready,
        "PROMOTION_RUNTIME_READY", promotion_runtime_ready,
    )
    print("PYBROKER_FULL_REPLAY_READY", pybroker_ready)
    print("NAUTILUS_FULL_REPLAY_ADAPTER_READY", nautilus_ready)
    print("LEAN_FULL_REPLAY_RUNTIME_READY", lean_full_ready)
    print("STOCKS_DONOR_CONTRACT_READY", donor_ready)
    print("LEAN_SOURCE_ONLY_DOES_NOT_VALIDATE", True)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")

    # Lean still blocks actual cross-engine validation if unavailable.
    # This diagnostic returns success when the local adapters/contracts
    # we can execute now are healthy.
    return 0 if core_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
