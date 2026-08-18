from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def _csv(path: Path) -> pd.DataFrame:
    return (
        pd.read_csv(path)
        if path.is_file()
        else pd.DataFrame()
    )


def build_autonomy_readiness_v2_9(
    project_root: str | Path,
) -> dict[str, Any]:
    root = Path(
        project_root
    ).resolve()

    prior = _json(
        root
        / "artifacts/research_runtime/"
        "autonomy_readiness_v2_7/"
        "readiness.json"
    )
    broker = _json(
        root
        / "artifacts/research_runtime/"
        "ibkr_readonly_v2_9/"
        "snapshot.json"
    )
    sizing = _json(
        root
        / "artifacts/research_runtime/"
        "whole_share_sizing_v2_9/"
        "audit.json"
    )
    shariah = _json(
        root
        / "artifacts/research_runtime/"
        "shariah_financial_verification/"
        "audit.json"
    )
    forward = _json(
        root
        / "artifacts/research_runtime/"
        "forward_signal_state/"
        "audit.json"
    )
    proposals = _csv(
        root
        / "artifacts/research_runtime/"
        "portfolio_decision_v2_7/"
        "proposals.csv"
    )

    economic = (
        broker.get(
            "economic_account_state"
        )
        or {}
    )

    observation_ready = bool(
        broker
        and broker.get(
            "snapshot_components_complete"
        )
        and broker.get(
            "double_snapshot_stable"
        )
        and int(
            broker.get(
                "broker_write_calls",
                0,
            )
        )
        == 0
    )

    execution_account_ready = bool(
        observation_ready
        and economic.get(
            "execution_status"
        )
        == "EXECUTION_ACCOUNT_READY"
    )

    gates = dict(
        prior.get("gates")
        or {}
    )
    gates[
        "IBKR_READ_ONLY_OBSERVATION_READY"
    ] = observation_ready
    gates[
        "IBKR_EXECUTION_ACCOUNT_STATE_READY"
    ] = execution_account_ready
    gates[
        "WHOLE_SHARE_SIZING_EVALUATED"
    ] = bool(
        sizing
        and sizing.get(
            "whole_shares_only"
        )
        is True
    )
    gates[
        "WHOLE_SHARE_SIZE_READY"
    ] = bool(
        int(
            sizing.get(
                "sizing_ready",
                0,
            )
        )
        > 0
    )

    # v2.9 deliberately never grants submission authority.
    gates[
        "BROKER_EXECUTION_READY"
    ] = False

    blockers = [
        name
        for name, value
        in gates.items()
        if not value
    ]

    return {
        "schema": (
            "autonomy_readiness_v2_9"
        ),
        "gates": gates,
        "research_decision_ready": bool(
            all(
                value
                for name, value
                in gates.items()
                if name
                not in {
                    "BROKER_EXECUTION_READY",
                    "WHOLE_SHARE_SIZE_READY",
                    "FRESH_ENTRY_READY",
                    "SHARIAH_VERIFICATION_READY",
                }
            )
        ),
        "broker_execution_ready": False,
        "machine_buy_proposals": int(
            (
                proposals.get(
                    "decision",
                    pd.Series(dtype=str),
                )
                == "BUY_NEW"
            ).sum()
        )
        if not proposals.empty
        else 0,
        "fresh_entry_ready": int(
            forward.get(
                "new_entry_ready",
                0,
            )
        ),
        "shariah_verified": int(
            shariah.get(
                "verified_trade_eligible",
                0,
            )
        ),
        "ibkr_readonly_ready": (
            observation_ready
        ),
        "ibkr_execution_account_state_ready": (
            execution_account_ready
        ),
        "whole_share_sizing_ready": int(
            sizing.get(
                "sizing_ready",
                0,
            )
        ),
        "broker_write_calls": int(
            broker.get(
                "broker_write_calls",
                0,
            )
        ),
        "blockers": blockers,
        "execution_authority": "NONE",
        "order_submission_enabled": False,
    }
