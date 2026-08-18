#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

COLUMNS = [
    "hypothesis_id",
    "source_engine",
    "validation_engine",
    "validation_role",
    "required",
    "reselection_allowed",
    "test_parameters_frozen",
    "status",
    "broker_calls",
    "order_calls",
    "execution_authority",
]


def main() -> int:
    source = (
        ROOT
        / "artifacts/research_runtime/"
        "kronos_dynamic_generalization_v2_16/validated.csv"
    )
    output = (
        ROOT
        / "artifacts/research_runtime/"
        "cross_engine_validation_queue_v2_16"
    )
    output.mkdir(parents=True, exist_ok=True)

    if not source.is_file() or source.stat().st_size == 0:
        frame = pd.DataFrame(columns=COLUMNS)
    else:
        validated = pd.read_csv(source)
        rows = []
        for hypothesis_id in validated.get(
            "hypothesis_id", pd.Series(dtype=str)
        ):
            for engine, role in (
                ("pybroker_reference", "walkforward_accounting_crosscheck"),
                ("nautilus", "deterministic_event_fill_crosscheck"),
                ("lean_reference", "independent_event_backtest_crosscheck"),
            ):
                rows.append(
                    {
                        "hypothesis_id": str(hypothesis_id),
                        "source_engine": "kronos_foundation_model_v2_15",
                        "validation_engine": engine,
                        "validation_role": role,
                        "required": True,
                        "reselection_allowed": False,
                        "test_parameters_frozen": True,
                        "status": "PENDING",
                        "broker_calls": 0,
                        "order_calls": 0,
                        "execution_authority": "NONE",
                    }
                )
        frame = pd.DataFrame(rows, columns=COLUMNS)

    frame.to_csv(output / "queue.csv", index=False)
    audit = {
        "schema": "cross_engine_validation_queue_v2_16",
        "rows": int(len(frame)),
        "hypotheses": int(frame["hypothesis_id"].nunique())
        if not frame.empty
        else 0,
        "required_engines": [
            "pybroker_reference",
            "nautilus",
            "lean_reference",
        ],
        "reselection_allowed": False,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "CROSS_ENGINE_VALIDATION_QUEUE_V2_16",
        "ROWS",
        len(frame),
        "HYPOTHESES",
        audit["hypotheses"],
    )
    if not frame.empty:
        print(frame.to_string(index=False))
    print("RESELECTION_ALLOWED False")
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
