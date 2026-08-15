
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _read(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path)


def _components(
    ids: list[str],
    pairs: pd.DataFrame,
) -> list[set[str]]:
    parent = {item: item for item in ids}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        if left not in parent or right not in parent:
            return
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    if not pairs.empty:
        for row in pairs.to_dict(orient="records"):
            if bool(row.get("redundancy_flag", False)):
                union(str(row["left"]), str(row["right"]))

    groups: dict[str, set[str]] = {}
    for item in ids:
        groups.setdefault(find(item), set()).add(item)
    return list(groups.values())


def build_final_strategy_roster(
    project_root: str | Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()

    registry = _read(
        root / "artifacts/research_runtime/research_candidate_registry/registry.csv"
    )
    if registry.empty:
        return pd.DataFrame(), {
            "schema": "final_strategy_roster_v1",
            "strategy_count": 0,
            "execution_authority": "NONE",
        }

    pairs = _read(
        root / "artifacts/research_runtime/strategy_redundancy/pairs.csv"
    )
    execution = _read(
        root / "artifacts/research_runtime/market_structure_15m_execution/summary.csv"
    )

    execution_map = {
        str(row["hypothesis_id"]): row
        for row in execution.to_dict(orient="records")
    } if not execution.empty else {}

    ids = registry["hypothesis_id"].astype(str).tolist()
    components = _components(ids, pairs)

    cluster_by_id: dict[str, str] = {}
    champion_by_cluster: dict[str, str] = {}

    for number, component in enumerate(components, start=1):
        cluster = f"CLUSTER_{number:02d}"
        for item in component:
            cluster_by_id[item] = cluster

        with_execution = [
            item for item in component
            if item in execution_map
        ]
        if with_execution:
            champion = max(
                with_execution,
                key=lambda item: (
                    float(
                        execution_map[item].get(
                            "median_stress_expectancy_bps",
                            float("-inf"),
                        )
                    ),
                    float(
                        execution_map[item].get(
                            "median_resolved_profit_factor",
                            float("-inf"),
                        )
                    ),
                ),
            )
        else:
            champion = min(component)

        champion_by_cluster[cluster] = champion

    rows = []
    for row in registry.to_dict(orient="records"):
        hypothesis_id = str(row["hypothesis_id"])
        cluster = cluster_by_id[hypothesis_id]
        champion = champion_by_cluster[cluster]
        is_champion = hypothesis_id == champion
        general = str(row.get("generalization_status") or "")
        stage = str(row.get("promotion_stage") or "")

        if general == "DYNAMIC_UNIVERSE_REJECT":
            roster_status = "REJECTED_GENERALIZATION"
        elif not is_champion:
            roster_status = "REDUNDANT_ALTERNATE"
        elif (
            general == "DYNAMIC_UNIVERSE_VALIDATED"
            and stage == "FINALIST_CANDIDATE"
        ):
            roster_status = "BROADLY_VALIDATED_FINALIST"
        elif general == "ROUTE_TO_15M_GENERALIZATION":
            roster_status = "PENDING_15M_BROAD_GENERALIZATION"
        elif stage == "CHALLENGER":
            roster_status = "CHALLENGER"
        else:
            roster_status = "RESEARCH_PENDING"

        rows.append(
            {
                **row,
                "redundancy_cluster": cluster,
                "cluster_champion": is_champion,
                "roster_status": roster_status,
                "research_deployment_ready": (
                    roster_status == "BROADLY_VALIDATED_FINALIST"
                ),
                "automatic_live_ready": False,
                "execution_authority": "NONE",
            }
        )

    frame = pd.DataFrame(rows)
    rank = {
        "BROADLY_VALIDATED_FINALIST": 0,
        "PENDING_15M_BROAD_GENERALIZATION": 1,
        "CHALLENGER": 2,
        "RESEARCH_PENDING": 3,
        "REDUNDANT_ALTERNATE": 8,
        "REJECTED_GENERALIZATION": 9,
    }
    frame["_rank"] = frame["roster_status"].map(rank).fillna(7)
    frame = (
        frame.sort_values(
            ["_rank", "family", "strategy", "hypothesis_id"]
        )
        .drop(columns=["_rank"])
        .reset_index(drop=True)
    )

    audit = {
        "schema": "final_strategy_roster_v1",
        "strategy_count": int(len(frame)),
        "broadly_validated_finalists": int(
            (frame["roster_status"] == "BROADLY_VALIDATED_FINALIST").sum()
        ),
        "pending_15m_champions": int(
            (
                frame["roster_status"]
                == "PENDING_15M_BROAD_GENERALIZATION"
            ).sum()
        ),
        "redundant_alternates": int(
            (frame["roster_status"] == "REDUNDANT_ALTERNATE").sum()
        ),
        "generalization_rejects": int(
            (frame["roster_status"] == "REJECTED_GENERALIZATION").sum()
        ),
        "live_ready": False,
        "live_blockers": [
            "CANDIDATE_SHARIAH_VERIFICATION",
            "PORTFOLIO_AUTHORITY_NOT_GRANTED",
        ],
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    return frame, audit


def write_final_strategy_roster(
    project_root: str | Path,
) -> tuple[pd.DataFrame, dict[str, Any], Path]:
    root = Path(project_root).resolve()
    frame, audit = build_final_strategy_roster(root)
    output = root / "artifacts/research_runtime/final_strategy_roster"
    output.mkdir(parents=True, exist_ok=True)
    path = output / "roster.csv"
    frame.to_csv(path, index=False)
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return frame, audit, path
