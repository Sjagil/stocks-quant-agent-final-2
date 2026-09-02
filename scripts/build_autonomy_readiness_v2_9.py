#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from stocks.orchestration.autonomy_readiness_v2_9 import (
    build_autonomy_readiness_v2_9,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    payload = (
        build_autonomy_readiness_v2_9(
            ROOT
        )
    )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "autonomy_readiness_v2_9"
    )
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = output / "readiness.json"
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
        "AUTONOMY_READINESS_V2_9",
        "RESEARCH_DECISION_READY",
        payload[
            "research_decision_ready"
        ],
        "IBKR_READONLY_READY",
        payload[
            "ibkr_readonly_ready"
        ],
        "IBKR_ACCOUNT_READY",
        payload[
            "ibkr_execution_account_state_ready"
        ],
        "WHOLE_SHARE_READY",
        payload[
            "whole_share_sizing_ready"
        ],
        "BROKER_EXECUTION_READY",
        payload[
            "broker_execution_ready"
        ],
    )
    print(
        "BLOCKERS",
        "|".join(
            payload["blockers"]
        ),
    )
    print(
        "BROKER_WRITE_CALLS",
        payload[
            "broker_write_calls"
        ],
    )
    print(
        "OUTPUT",
        path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
