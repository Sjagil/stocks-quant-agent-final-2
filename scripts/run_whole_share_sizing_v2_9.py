#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from stocks.orchestration.whole_share_sizing import (
    build_whole_share_sizing,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    frame, audit = (
        build_whole_share_sizing(
            ROOT
        )
    )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "whole_share_sizing_v2_9"
    )
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        output / "sizing.csv",
        index=False,
    )
    (
        output / "audit.json"
    ).write_text(
        json.dumps(
            audit,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "WHOLE_SHARE_SIZING_V2_9",
        "BUY_INPUTS",
        audit["buy_new_inputs"],
        "ROWS",
        audit["rows"],
        "READY",
        audit["sizing_ready"],
        "ACCOUNT_READY",
        audit["account_ready"],
        "FIXED_EURO_CAP",
        audit[
            "fixed_euro_order_cap_enabled"
        ],
    )

    if not frame.empty:
        print(
            frame[
                [
                    "symbol",
                    "conviction",
                    "reference_price_eur",
                    "stop_distance_eur",
                    "net_liquidation_eur",
                    "execution_capacity_eur",
                    "whole_share_quantity",
                    "estimated_stop_risk_eur",
                    "sizing_ready",
                    "blockers",
                ]
            ].to_string(index=False)
        )

    print(
        "BROKER_WRITES",
        0,
    )
    print(
        "ARTIFACT_ROOT",
        output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
