
#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from stocks.orchestration.autonomy_readiness import (
    build_autonomy_readiness,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    payload = (
        build_autonomy_readiness(
            ROOT
        )
    )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "autonomy_readiness_v2_7"
    )
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        output
        / "readiness.json"
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "AUTONOMY_READINESS_V2_7",
        "RESEARCH_DECISION_READY",
        payload[
            "all_research_decision_gates_ready"
        ],
        "BROKER_EXECUTION_READY",
        payload[
            "broker_execution_ready"
        ],
        "BUY_PROPOSALS",
        payload[
            "machine_approved_buy_proposals"
        ],
    )

    print(
        "GATES",
        json.dumps(
            payload[
                "gates"
            ],
            sort_keys=True,
        ),
    )

    print(
        "BLOCKERS",
        "|".join(
            payload[
                "blockers"
            ]
        ),
    )

    print(
        "OUTPUT",
        path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
