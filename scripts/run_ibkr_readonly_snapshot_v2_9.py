#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from stocks.integrations.registry import (
    IntegrationRegistry,
)
from stocks.integrations.runner import (
    IntegrationRunner,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--integration",
        default="stocks_ibkr_reference",
    )
    args = parser.parse_args()

    registry = IntegrationRegistry.load(
        ROOT / "config/integrations.yaml",
        project_root=ROOT,
    )
    runner = IntegrationRunner(registry)

    response = runner.run(
        args.integration,
        "broker_snapshot_read_only",
        timeout_seconds=90,
    )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "ibkr_readonly_v2_9"
    )
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    response_path = output / "response.json"
    response_path.write_text(
        json.dumps(
            response.to_dict(),
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    if not response.ok:
        print(
            "IBKR_READONLY_V2_9",
            "STATUS",
            response.state.value,
            "ERROR",
            response.error,
        )
        print(
            "BROKER_WRITES",
            0,
        )
        print(
            "OUTPUT",
            output,
        )
        return 2

    if not response.artifacts:
        print(
            "IBKR_READONLY_V2_9",
            "STATUS",
            "ERROR",
            "NO_SNAPSHOT_ARTIFACT",
        )
        return 2

    source = Path(
        response.artifacts[0].path
    ).resolve()
    target = output / "snapshot.json"
    shutil.copy2(
        source,
        target,
    )

    payload = json.loads(
        target.read_text(
            encoding="utf-8"
        )
    )
    economic = (
        payload.get(
            "economic_account_state"
        )
        or {}
    )
    snapshot = (
        payload.get("snapshot")
        or {}
    )

    positions = (
        (snapshot.get("positions") or {})
        .get("positions")
        or []
    )
    orders = (
        (
            snapshot.get(
                "all_api_open_orders"
            )
            or {}
        ).get("open_orders")
        or []
    )

    print(
        "IBKR_READONLY_V2_9",
        "STATUS",
        response.state.value,
        "LIFECYCLE",
        economic.get("lifecycle_state"),
        "RESEARCH",
        economic.get("research_status"),
        "EXECUTION_ACCOUNT",
        economic.get("execution_status"),
        "STABLE",
        payload.get(
            "double_snapshot_stable"
        ),
    )
    print(
        "NET_LIQUIDATION_EUR",
        economic.get(
            "reporting_value_eur"
        ),
        "SPENDABLE_EUR",
        economic.get(
            "spendable_eur"
        ),
        "EXECUTION_CAPACITY_EUR",
        economic.get(
            "execution_sizing_capacity_eur"
        ),
    )
    print(
        "POSITIONS",
        len(positions),
        "ALL_API_OPEN_ORDERS",
        len(orders),
    )
    print(
        "EXECUTION_BLOCKERS",
        "|".join(
            economic.get(
                "execution_blockers"
            )
            or []
        ),
    )
    print(
        "BROKER_WRITES",
        payload.get(
            "broker_write_calls",
            0,
        ),
    )
    print(
        "OUTPUT",
        target,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
