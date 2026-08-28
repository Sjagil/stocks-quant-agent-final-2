from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.is_file() else pd.DataFrame()


def build_autonomy_readiness(
    project_root: str | Path,
) -> dict[str, Any]:
    root = Path(project_root).resolve()

    research = _json(
        root
        / "artifacts/research_runtime/"
        "research_readiness/readiness.json"
    )
    market15 = _json(
        root
        / "artifacts/research_runtime/"
        "market_structure_15m_generalization/audit.json"
    )
    shariah = _json(
        root
        / "artifacts/research_runtime/"
        "shariah_financial_verification/audit.json"
    )
    forward = _json(
        root
        / "artifacts/research_runtime/"
        "forward_signal_state/audit.json"
    )
    portfolio = _json(
        root
        / "artifacts/research_runtime/"
        "portfolio_decision_v2_7/audit.json"
    )
    proposals = _csv(
        root
        / "artifacts/research_runtime/"
        "portfolio_decision_v2_7/proposals.csv"
    )

    shariah_ready_count = int(
        shariah.get(
            "verified_matrix_candidates",
            shariah.get("verified_trade_eligible", 0),
        )
    )

    gates = {
        "DISCOVERY_READY": bool(
            research.get("contextual_candidates", 0) > 0
        ),
        "STRATEGY_RESEARCH_READY": bool(
            research.get("broadly_validated_finalists", 0) >= 2
        ),
        "GENERALIZATION_1H_READY": bool(
            research.get("frozen_holdout_usable", 0) >= 5
        ),
        "GENERALIZATION_15M_READY": (
            market15.get("status")
            == "15M_DYNAMIC_UNIVERSE_VALIDATED"
        ),
        "SHARIAH_VERIFICATION_READY": bool(
            shariah_ready_count > 0
        ),
        "FORWARD_SIGNAL_ENGINE_READY": bool(
            forward.get("rows", 0) > 0
        ),
        "FRESH_ENTRY_READY": bool(
            forward.get("new_entry_ready", 0) > 0
        ),
        "PORTFOLIO_DECISION_READY": bool(
            portfolio.get("proposal_count", 0) > 0
        ),
        "WHOLE_SHARE_CANARY_POLICY_READY": bool(
            portfolio.get("whole_share_canary") is True
            and portfolio.get(
                "fixed_euro_order_cap_enabled"
            )
            is False
        ),
        "BROKER_EXECUTION_READY": False,
    }

    blockers = [
        name
        for name, passed in gates.items()
        if not passed
    ]

    return {
        "schema": "autonomy_readiness_v2_8",
        "gates": gates,
        "all_research_decision_gates_ready": all(
            value
            for key, value in gates.items()
            if key != "BROKER_EXECUTION_READY"
        ),
        "broker_execution_ready": False,
        "machine_approved_buy_proposals": int(
            (
                proposals.get(
                    "decision",
                    pd.Series(dtype=str),
                )
                == "BUY_NEW"
            ).sum()
        ) if not proposals.empty else 0,
        "canary_contract": {
            "quantity_mode": "WHOLE_SHARES",
            "fractional_shares_allowed": False,
            "fixed_euro_order_cap_enabled": False,
            "sizing_authority": "RISK_AND_PORTFOLIO_WEIGHT",
        },
        "blockers": blockers,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
