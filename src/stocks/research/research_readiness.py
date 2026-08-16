from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.is_file() else pd.DataFrame()


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_research_readiness(
    project_root: str | Path,
) -> dict[str, Any]:
    root = Path(project_root).resolve()

    contextual = _csv(
        root
        / "artifacts/research_runtime/"
        "contextual_discovery/candidates.csv"
    )
    hydration = _csv(
        root
        / "artifacts/research_runtime/"
        "contextual_1h_hydration/usable_candidates.csv"
    )
    roster = _csv(
        root
        / "artifacts/research_runtime/"
        "final_strategy_roster/roster.csv"
    )
    matrix = _csv(
        root
        / "artifacts/research_runtime/"
        "candidate_strategy_matrix/matrix.csv"
    )
    opportunities = _csv(
        root
        / "artifacts/research_runtime/"
        "candidate_strategy_matrix/opportunities.csv"
    )
    holdout = _json(
        root
        / "artifacts/research_runtime/"
        "unseen_1h_hydration/audit.json"
    )
    shariah = _csv(
        root
        / "artifacts/research_runtime/"
        "shariah_financial_verification/verification.csv"
    )

    generalized = int(
        (
            roster.get(
                "roster_status",
                pd.Series(dtype=str),
            )
            == "BROADLY_VALIDATED_FINALIST"
        ).sum()
    ) if not roster.empty else 0

    pending_15m = int(
        (
            roster.get(
                "roster_status",
                pd.Series(dtype=str),
            )
            == "PENDING_15M_BROAD_GENERALIZATION"
        ).sum()
    ) if not roster.empty else 0

    if not shariah.empty:
        shariah_tradeable = int(
            shariah.get(
                "trade_eligible",
                pd.Series(dtype=bool),
            )
            .fillna(False)
            .astype(bool)
            .sum()
        )
        pending_attestation = int(
            (
                shariah.get(
                    "status",
                    pd.Series(dtype=str),
                )
                == (
                    "FINANCIAL_SCREEN_PASS_"
                    "ATTESTATION_REQUIRED"
                )
            ).sum()
        )
    else:
        shariah_tradeable = int(
            contextual.get(
                "trade_eligible",
                pd.Series(dtype=bool),
            )
            .fillna(False)
            .astype(bool)
            .sum()
        ) if not contextual.empty else 0
        pending_attestation = 0

    research_complete = (
        len(contextual) > 0
        and len(hydration) >= 8
        and generalized >= 2
        and int(holdout.get("usable_after_run", 0)) >= 5
        and not matrix.empty
    )

    live_blockers: list[str] = []

    if shariah_tradeable == 0:
        live_blockers.append(
            "NO_SHARIAH_VERIFIED_TRADEABLE_CANDIDATES"
        )

    if pending_15m > 0:
        live_blockers.append(
            "15M_BROAD_GENERALIZATION_PENDING_FOR_"
            "MARKET_STRUCTURE_FAMILY"
        )

    live_blockers.extend(
        [
            "PORTFOLIO_CONSTRUCTION_AUTHORITY_NOT_GRANTED",
            "BROKER_EXECUTION_AUTHORITY_NOT_GRANTED",
        ]
    )

    return {
        "schema": "research_readiness_v2_8",
        "research_platform_complete": bool(research_complete),
        "contextual_candidates": int(len(contextual)),
        "hydrated_current_candidates": int(len(hydration)),
        "frozen_holdout_usable": int(
            holdout.get("usable_after_run", 0)
        ),
        "broadly_validated_finalists": generalized,
        "pending_15m_family_champions": pending_15m,
        "candidate_strategy_matrix_rows": int(len(matrix)),
        "current_research_opportunities": int(len(opportunities)),
        "shariah_verified_tradeable_candidates": (
            shariah_tradeable
        ),
        "shariah_financial_pass_pending_attestation": (
            pending_attestation
        ),
        "live_trading_ready": False,
        "live_blockers": live_blockers,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }


def write_research_readiness(
    project_root: str | Path,
) -> tuple[dict[str, Any], Path]:
    root = Path(project_root).resolve()
    payload = build_research_readiness(root)

    output = (
        root
        / "artifacts/research_runtime/research_readiness"
    )
    output.mkdir(parents=True, exist_ok=True)

    path = output / "readiness.json"
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return payload, path
