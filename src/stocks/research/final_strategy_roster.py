from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


def _read(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path)


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _evidence_champion(
    component: set[str],
    registry_by_id: dict[str, dict[str, Any]],
) -> str:
    def descending(value: Any) -> float:
        number = _finite(value)
        return -number if number is not None else math.inf

    def rank(hypothesis_id: str) -> tuple[Any, ...]:
        row = registry_by_id[hypothesis_id]
        return (
            -int(str(row.get("promotion_stage")) == "FINALIST_CANDIDATE"),
            -int(
                str(row.get("generalization_status"))
                == "DYNAMIC_UNIVERSE_VALIDATED"
            ),
            descending(row.get("robustness_score")),
            descending(row.get("median_stress_test_expectancy_bps")),
            descending(row.get("median_test_expectancy_bps")),
            _finite(row.get("queue_rank")) or math.inf,
            hypothesis_id,
        )

    return min(component, key=rank)


def validated_15m_champion(
    root: Path,
) -> tuple[str | None, dict[str, Any]]:
    audit = _json(
        root
        / "artifacts/research_runtime/"
        "market_structure_15m_generalization/audit.json"
    )
    if not audit:
        return None, {}

    policy = _json(
        root / "config/final_decision_fabric_v2_8.json"
    ).get("market_structure_promotion", {})

    if not policy:
        return None, audit

    checks = [
        audit.get("status") == policy["required_status"],
        int(audit.get("eligible_symbols", 0))
        >= int(policy["minimum_eligible_symbols"]),
        int(audit.get("traded_symbols", 0))
        >= int(policy["minimum_traded_symbols"]),
        int(audit.get("oos_trades", 0))
        >= int(policy["minimum_oos_trades"]),
        float(audit.get("positive_fold_ratio", 0.0))
        >= float(policy["minimum_positive_fold_ratio"]),
        float(audit.get("stress_positive_fold_ratio", 0.0))
        >= float(policy["minimum_stress_positive_fold_ratio"]),
        float(audit.get("positive_symbol_ratio", 0.0))
        >= float(policy["minimum_positive_symbol_ratio"]),
        float(audit.get("stress_positive_symbol_ratio", 0.0))
        >= float(policy["minimum_stress_positive_symbol_ratio"]),
        float(audit.get("max_symbol_trade_share", 1.0))
        <= float(policy["maximum_symbol_trade_share"]),
    ]

    median = _finite(audit.get("median_expectancy_bps"))
    stress_median = _finite(
        audit.get("median_stress_expectancy_bps")
    )

    if bool(policy.get("require_positive_median_expectancy", True)):
        checks.append(median is not None and median > 0)

    if bool(
        policy.get(
            "require_positive_median_stress_expectancy",
            True,
        )
    ):
        checks.append(
            stress_median is not None and stress_median > 0
        )

    if not all(checks):
        return None, audit

    hypothesis_id = str(audit.get("hypothesis_id") or "")
    return (hypothesis_id or None), audit


def build_final_strategy_roster(
    project_root: str | Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()

    registry = _read(
        root
        / "artifacts/research_runtime/"
        "research_candidate_registry/registry.csv"
    )
    if registry.empty:
        return pd.DataFrame(), {
            "schema": "final_strategy_roster_v2_8",
            "strategy_count": 0,
            "execution_authority": "NONE",
        }

    pairs = _read(
        root
        / "artifacts/research_runtime/"
        "strategy_redundancy/pairs.csv"
    )
    execution = _read(
        root
        / "artifacts/research_runtime/"
        "market_structure_15m_execution/summary.csv"
    )

    execution_map = {
        str(row["hypothesis_id"]): row
        for row in execution.to_dict(orient="records")
    } if not execution.empty else {}

    ids = registry["hypothesis_id"].astype(str).tolist()
    registry_by_id = {
        str(row["hypothesis_id"]): row
        for row in registry.to_dict(orient="records")
    }
    components = _components(ids, pairs)

    cluster_by_id: dict[str, str] = {}
    champion_by_cluster: dict[str, str] = {}

    for number, component in enumerate(components, start=1):
        cluster = f"CLUSTER_{number:02d}"
        for item in component:
            cluster_by_id[item] = cluster

        with_execution = [
            item
            for item in component
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
            champion = _evidence_champion(component, registry_by_id)

        champion_by_cluster[cluster] = champion

    validated_15m_id, generalization_15m = (
        validated_15m_champion(root)
    )

    rows = []

    for row in registry.to_dict(orient="records"):
        hypothesis_id = str(row["hypothesis_id"])
        cluster = cluster_by_id[hypothesis_id]
        champion = champion_by_cluster[cluster]
        is_champion = hypothesis_id == champion
        general = str(row.get("generalization_status") or "")
        stage = str(row.get("promotion_stage") or "")

        broad_generalization_status = general
        broad_evidence = "1H_DYNAMIC_UNIVERSE"

        if (
            general == "ROUTE_TO_15M_GENERALIZATION"
            and is_champion
            and validated_15m_id == hypothesis_id
        ):
            broad_generalization_status = (
                "15M_DYNAMIC_UNIVERSE_VALIDATED"
            )
            broad_evidence = (
                "REAL_15M_CHRONOLOGY_UNSEEN_HOLDOUT"
            )

        if general == "DYNAMIC_UNIVERSE_REJECT":
            roster_status = "REJECTED_GENERALIZATION"
        elif not is_champion:
            roster_status = "REDUNDANT_ALTERNATE"
        elif (
            broad_generalization_status
            in {
                "DYNAMIC_UNIVERSE_VALIDATED",
                "15M_DYNAMIC_UNIVERSE_VALIDATED",
            }
            and stage == "FINALIST_CANDIDATE"
        ):
            roster_status = "BROADLY_VALIDATED_FINALIST"
        elif general == "ROUTE_TO_15M_GENERALIZATION":
            if (
                generalization_15m.get("status")
                == "15M_DYNAMIC_UNIVERSE_REJECT"
                and str(
                    generalization_15m.get("hypothesis_id") or ""
                )
                == hypothesis_id
            ):
                roster_status = "REJECTED_15M_GENERALIZATION"
            else:
                roster_status = "PENDING_15M_BROAD_GENERALIZATION"
        elif stage == "CHALLENGER":
            roster_status = "CHALLENGER"
        else:
            roster_status = "RESEARCH_PENDING"

        rows.append(
            {
                **row,
                "broad_generalization_status": (
                    broad_generalization_status
                ),
                "broad_generalization_evidence": broad_evidence,
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
        "REJECTED_15M_GENERALIZATION": 9,
        "REJECTED_GENERALIZATION": 9,
    }

    frame["_rank"] = (
        frame["roster_status"]
        .map(rank)
        .fillna(7)
    )
    frame = (
        frame.sort_values(
            [
                "_rank",
                "family",
                "strategy",
                "hypothesis_id",
            ]
        )
        .drop(columns=["_rank"])
        .reset_index(drop=True)
    )

    pending_15m = int(
        (
            frame["roster_status"]
            == "PENDING_15M_BROAD_GENERALIZATION"
        ).sum()
    )

    audit = {
        "schema": "final_strategy_roster_v2_8",
        "strategy_count": len(frame),
        "broadly_validated_finalists": int(
            (
                frame["roster_status"]
                == "BROADLY_VALIDATED_FINALIST"
            ).sum()
        ),
        "validated_15m_champions": int(
            (
                frame["broad_generalization_status"]
                == "15M_DYNAMIC_UNIVERSE_VALIDATED"
            ).sum()
        ),
        "pending_15m_champions": pending_15m,
        "redundant_alternates": int(
            (
                frame["roster_status"]
                == "REDUNDANT_ALTERNATE"
            ).sum()
        ),
        "generalization_rejects": int(
            frame["roster_status"]
            .astype(str)
            .str.startswith("REJECTED")
            .sum()
        ),
        "live_ready": False,
        "live_blockers": [
            *(
                ["CANDIDATE_SHARIAH_VERIFICATION"]
            ),
            *(
                [
                    "15M_BROAD_GENERALIZATION_PENDING"
                ]
                if pending_15m
                else []
            ),
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

    output = (
        root
        / "artifacts/research_runtime/"
        "final_strategy_roster"
    )
    output.mkdir(parents=True, exist_ok=True)

    path = output / "roster.csv"
    frame.to_csv(path, index=False)

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

    return frame, audit, path
