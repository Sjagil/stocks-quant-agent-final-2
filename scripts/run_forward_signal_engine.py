#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from stocks.orchestration.forward_signal_engine import (
    build_forward_signal_state,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    frame, audit = (
        build_forward_signal_state(
            ROOT
        )
    )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "forward_signal_state"
    )
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        output / "signals.csv",
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

    version = (
        "V2_8"
        if str(
            audit.get("schema", "")
        ).endswith("v2_8")
        else str(
            audit.get(
                "schema",
                "UNKNOWN",
            )
        ).upper()
    )

    print(
        f"FORWARD_SIGNAL_ENGINE_{version}",
        "ROWS",
        audit["rows"],
        "NEW_ENTRY_READY",
        audit["new_entry_ready"],
        "ACTIVE_POSITION_STATES",
        audit[
            "active_research_positions"
        ],
        "RECENT_OBSERVE",
        audit["recent_observe"],
    )

    if not frame.empty:
        columns = [
            "symbol",
            "strategy",
            "research_lane",
            "forward_state",
            "fresh_trigger_reason",
            "signal_bar_time",
            "bars_since_entry",
            "applicability_score",
            "new_entry_ready",
            "position_management_candidate",
        ]
        print(
            frame[
                [
                    column
                    for column in columns
                    if column in frame.columns
                ]
            ]
            .head(60)
            .to_string(index=False)
        )

    print(
        "ARTIFACT_ROOT",
        output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
