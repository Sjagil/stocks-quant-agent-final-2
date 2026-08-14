from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


FACTORY_PATH = Path(
    "artifacts/research_runtime/"
    "strategy_factory_1h/"
    "survivors.csv"
)

PYBROKER_PATH = Path(
    "artifacts/research_runtime/"
    "pybroker_crosscheck/"
    "summary.csv"
)

MARKET_STRUCTURE_PATH = Path(
    "artifacts/research_runtime/"
    "market_structure_15m_execution/"
    "summary.csv"
)

OUTPUT_ROOT = Path(
    "artifacts/research_runtime/"
    "validated_strategy_registry"
)


def _read_csv(
    path: Path,
    *,
    required: bool = True,
) -> pd.DataFrame:
    if not path.is_file():
        if required:
            raise FileNotFoundError(
                path
            )

        return pd.DataFrame()

    frame = pd.read_csv(
        path,
        dtype={
            "hypothesis_id": str,
        },
    )

    if (
        "hypothesis_id"
        not in frame.columns
    ):
        raise ValueError(
            f"{path}: hypothesis_id missing"
        )

    frame[
        "hypothesis_id"
    ] = (
        frame[
            "hypothesis_id"
        ]
        .astype(str)
    )

    if (
        frame[
            "hypothesis_id"
        ]
        .duplicated()
        .any()
    ):
        raise ValueError(
            f"{path}: duplicate hypothesis_id"
        )

    return frame


def _one(
    frame: pd.DataFrame,
    hypothesis_id: str,
    *,
    source: str,
) -> dict[str, Any]:
    if frame.empty:
        raise ValueError(
            f"{hypothesis_id}: "
            f"{source} evidence missing"
        )

    match = frame.loc[
        frame[
            "hypothesis_id"
        ]
        .astype(str)
        == str(
            hypothesis_id
        )
    ]

    if len(match) != 1:
        raise ValueError(
            f"{hypothesis_id}: expected "
            f"exactly one {source} row, "
            f"got {len(match)}"
        )

    return dict(
        match.iloc[
            0
        ]
    )


def build_validated_strategy_registry(
    root: Path,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    factory = _read_csv(
        root
        / FACTORY_PATH
    )

    pybroker = _read_csv(
        root
        / PYBROKER_PATH
    )

    market_structure = (
        _read_csv(
            root
            / MARKET_STRUCTURE_PATH,
            required=False,
        )
    )

    rows: list[
        dict[str, Any]
    ] = []

    for survivor in (
        factory.to_dict(
            orient="records"
        )
    ):
        hypothesis_id = str(
            survivor[
                "hypothesis_id"
            ]
        )

        strategy = str(
            survivor[
                "strategy"
            ]
        )

        factory_status = str(
            survivor[
                "status"
            ]
        )

        validation_status = (
            "UNVALIDATED"
        )

        validation_engine = (
            "NONE"
        )

        execution_contract = (
            "1H_NEXT_OPEN"
        )

        execution_timeframe = (
            "1h"
        )

        evidence_status = (
            "MISSING"
        )

        if (
            strategy
            == (
                "market_structure_"
                "atr_pullback"
            )
        ):
            evidence = _one(
                market_structure,
                hypothesis_id,
                source=(
                    "15m execution"
                ),
            )

            evidence_status = str(
                evidence[
                    "status"
                ]
            )

            validation_engine = (
                "CANONICAL_15M_"
                "EXECUTION_CHRONOLOGY"
            )

            execution_contract = (
                "1H_SETUP_"
                "15M_EXECUTION"
            )

            execution_timeframe = (
                "15m"
            )

            if (
                evidence_status
                == (
                    "15M_EXECUTION_"
                    "VALIDATED"
                )
            ):
                validation_status = (
                    "VALIDATED"
                )
            else:
                validation_status = (
                    "REJECT_OR_INCOMPLETE"
                )

        else:
            evidence = _one(
                pybroker,
                hypothesis_id,
                source="PyBroker",
            )

            evidence_status = str(
                evidence[
                    "crosscheck_status"
                ]
            )

            validation_engine = (
                "PYBROKER"
            )

            execution_contract = str(
                evidence.get(
                    "execution_contract"
                )
                or "NEXT_OPEN_REPLAY"
            )

            if (
                evidence_status
                == (
                    "CROSS_ENGINE_"
                    "VALIDATED"
                )
            ):
                validation_status = (
                    "VALIDATED"
                )

            elif (
                evidence_status
                == (
                    "CROSS_ENGINE_"
                    "PROVISIONAL"
                )
            ):
                validation_status = (
                    "PROVISIONAL"
                )

            else:
                validation_status = (
                    "REJECT_OR_INCOMPLETE"
                )

        if (
            validation_status
            == "VALIDATED"
            and factory_status
            == "STRONG_SURVIVOR"
        ):
            promotion_stage = (
                "FINALIST_CANDIDATE"
            )

        elif (
            validation_status
            in {
                "VALIDATED",
                "PROVISIONAL",
            }
        ):
            promotion_stage = (
                "CHALLENGER"
            )

        else:
            promotion_stage = (
                "NOT_PROMOTED"
            )

        rows.append(
            {
                "hypothesis_id": (
                    hypothesis_id
                ),
                "strategy": strategy,
                "family": str(
                    survivor[
                        "family"
                    ]
                ),
                "params_json": str(
                    survivor[
                        "params_json"
                    ]
                ),
                "primary_timeframe": (
                    "1h"
                ),
                "execution_timeframe": (
                    execution_timeframe
                ),
                "execution_contract": (
                    execution_contract
                ),
                "factory_status": (
                    factory_status
                ),
                "validation_status": (
                    validation_status
                ),
                "validation_engine": (
                    validation_engine
                ),
                "evidence_status": (
                    evidence_status
                ),
                "promotion_stage": (
                    promotion_stage
                ),
                "execution_authority": (
                    "NONE"
                ),
                "broker_calls": 0,
            }
        )

    result = pd.DataFrame(
        rows
    )

    if result.empty:
        raise ValueError(
            "strategy registry is empty"
        )

    if (
        result[
            "hypothesis_id"
        ]
        .duplicated()
        .any()
    ):
        raise ValueError(
            "strategy registry contains "
            "duplicate hypotheses"
        )

    finalist_count = int(
        (
            result[
                "promotion_stage"
            ]
            == "FINALIST_CANDIDATE"
        ).sum()
    )

    if finalist_count < 1:
        raise ValueError(
            "no independently validated "
            "finalist candidate"
        )

    rank = {
        "FINALIST_CANDIDATE": 0,
        "CHALLENGER": 1,
        "NOT_PROMOTED": 2,
    }

    result[
        "_rank"
    ] = (
        result[
            "promotion_stage"
        ]
        .map(
            rank
        )
        .fillna(
            99
        )
    )

    result = (
        result.sort_values(
            [
                "_rank",
                "strategy",
                "hypothesis_id",
            ]
        )
        .drop(
            columns=[
                "_rank"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    audit = {
        "schema": (
            "validated_strategy_"
            "registry_v1"
        ),
        "strategy_count": int(
            len(
                result
            )
        ),
        "finalist_candidate_count": (
            finalist_count
        ),
        "challenger_count": int(
            (
                result[
                    "promotion_stage"
                ]
                == "CHALLENGER"
            ).sum()
        ),
        "not_promoted_count": int(
            (
                result[
                    "promotion_stage"
                ]
                == "NOT_PROMOTED"
            ).sum()
        ),
        "primary_timeframe": "1h",
        "live_ready": False,
        "event_driven_finalist_validation_required": (
            True
        ),
        "dynamic_universe_generalization_required": (
            True
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }

    return (
        result,
        audit,
    )


def write_validated_strategy_registry(
    root: Path,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
    Path,
]:
    frame, audit = (
        build_validated_strategy_registry(
            root
        )
    )

    output_root = (
        root
        / OUTPUT_ROOT
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        output_root
        / "registry.csv"
    )

    audit_path = (
        output_root
        / "audit.json"
    )

    frame.to_csv(
        csv_path,
        index=False,
    )

    audit_path.write_text(
        json.dumps(
            audit,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return (
        frame,
        audit,
        csv_path,
    )
