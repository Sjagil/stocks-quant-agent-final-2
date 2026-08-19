#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.agents.pipeline import build_agent_shadow_decisions


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeframe", default="1h")
    args = parser.parse_args()

    frame, audit = build_agent_shadow_decisions(
        ROOT,
        timeframe=args.timeframe,
    )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "agent_fabric_v2_12"
    )
    output.mkdir(parents=True, exist_ok=True)

    frame.to_csv(output / "shadow_decisions.csv", index=False)
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    print(
        "AGENT_FABRIC_V2_12",
        "ROWS",
        audit["rows"],
        "IBKR_READY",
        audit["broker_account_ready"],
        "DQN_MODELS",
        audit["trained_dqn_votes"],
        "SAC_MODELS",
        audit["trained_sac_votes"],
        "RISK_MODELS",
        audit["trained_risk_votes"],
        "HARD_GATE_PASSES",
        audit["hard_gate_passes"],
        "POSITIVE_SHADOW_TARGETS",
        audit["positive_shadow_targets"],
    )

    if not frame.empty:
        print(
            frame[
                [
                    "symbol",
                    "strategy",
                    "dqn_action",
                    "sac_target_exposure",
                    "risk_action",
                    "nlp_modifier",
                    "fresh_validated_entry",
                    "shariah_verified",
                    "broker_account_ready",
                    "shadow_target_exposure",
                    "blockers",
                ]
            ].head(80).to_string(index=False)
        )

    print("MONEY_CONTROL False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
