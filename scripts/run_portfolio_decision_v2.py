
#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from stocks.orchestration.portfolio_decision_v2 import (
    build_portfolio_proposals,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    frame, audit = (
        build_portfolio_proposals(
            ROOT
        )
    )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "portfolio_decision_v2_7"
    )
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        output / "proposals.csv",
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
        "PORTFOLIO_DECISION_V2_7",
        "PROPOSALS",
        audit["proposal_count"],
        "BUY_NEW",
        audit["buy_new"],
        "OBSERVE_EXISTING",
        audit["observe_existing"],
        "SHARIAH_VERIFIED",
        audit["shariah_verified"],
        "WHOLE_SHARE_CANARY",
        audit["whole_share_canary"],
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
                    "decision",
                    "conviction",
                    "strategy_votes",
                    "shariah_status",
                    "fresh_entry_trigger",
                    "active_position_state",
                    "canary_quantity_mode",
                    "fixed_euro_order_cap_enabled",
                    "blockers",
                ]
            ].to_string(
                index=False
            )
        )

    print(
        "ARTIFACT_ROOT",
        output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
