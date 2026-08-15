from __future__ import annotations

import json
import math
from typing import Any, Mapping

import numpy as np
import pandas as pd


def hypothesis_from_survivor_row(row: Mapping[str, Any]):
    from stocks.research.indicator_discovery import IndicatorHypothesis

    raw_params = row.get("params_json", "{}")
    params = raw_params if isinstance(raw_params, dict) else json.loads(str(raw_params))
    return IndicatorHypothesis(
        hypothesis_id=str(row["hypothesis_id"]),
        template=str(row.get("template") or row.get("strategy")),
        family=str(row["family"]),
        params=dict(params),
        execution_contract=str(row.get("execution_contract") or "NEXT_OPEN_REPLAY"),
    )


def _finite(values) -> list[float]:
    output: list[float] = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            output.append(number)
    return output


def summarize_crosscheck_rows(
    rows: list[dict[str, Any]],
    *,
    all_test_trades: pd.DataFrame,
    stress_cost_bps_per_side: float,
) -> dict[str, Any]:
    from stocks.research.pybroker_crosscheck import classify_crosscheck, evaluate_symbol_breadth

    usable = [row for row in rows if bool(row.get("usable"))]
    base = _finite(row.get("canonical_base_expectancy_bps") for row in usable)
    stress = _finite(row.get("canonical_stress_expectancy_bps") for row in usable)
    matches = _finite(row.get("pybroker_base_schedule_match_ratio") for row in usable)

    positive_fold_ratio = float(np.mean([value > 0 for value in base])) if base else 0.0
    stress_positive_fold_ratio = float(np.mean([value > 0 for value in stress])) if stress else 0.0
    median_base = float(np.median(base)) if base else math.nan
    worst_base = float(min(base)) if base else math.nan
    median_stress = float(np.median(stress)) if stress else math.nan
    minimum_match = float(min(matches)) if matches else 0.0

    breadth = evaluate_symbol_breadth(
        all_test_trades,
        cost_bps_per_side=float(stress_cost_bps_per_side),
    )

    status = classify_crosscheck(
        usable_folds=len(usable),
        positive_fold_ratio=positive_fold_ratio,
        stress_positive_fold_ratio=stress_positive_fold_ratio,
        worst_expectancy_bps=worst_base,
        median_stress_expectancy_bps=median_stress,
        min_schedule_match_ratio=minimum_match,
        positive_symbol_ratio=float(breadth["positive_symbol_ratio"]),
        max_symbol_trade_share=float(breadth["max_symbol_trade_share"]),
    )

    return {
        "usable_folds": int(len(usable)),
        "positive_fold_ratio": positive_fold_ratio,
        "stress_positive_fold_ratio": stress_positive_fold_ratio,
        "median_base_expectancy_bps": median_base,
        "worst_base_expectancy_bps": worst_base,
        "median_stress_expectancy_bps": median_stress,
        "minimum_pybroker_schedule_match_ratio": minimum_match,
        "symbol_count": int(breadth["symbol_count"]),
        "positive_symbol_ratio": float(breadth["positive_symbol_ratio"]),
        "max_symbol_trade_share": float(breadth["max_symbol_trade_share"]),
        "crosscheck_status": status,
    }
