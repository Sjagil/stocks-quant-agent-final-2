from __future__ import annotations

import math
from typing import Any

import pandas as pd

from stocks.research.kronos_strategy_factory import trade_metrics


CANDIDATE_STATUSES = {
    "PROVISIONAL_SURVIVOR",
    "INSUFFICIENT_OOS_EVIDENCE",
}


def freeze_candidates(
    summary: pd.DataFrame,
    *,
    max_candidates: int,
) -> pd.DataFrame:
    if summary.empty:
        return summary.copy()

    work = summary.copy()
    work["selected_folds"] = pd.to_numeric(
        work.get("selected_folds"), errors="coerce"
    ).fillna(0)
    work["evaluated_test_folds"] = pd.to_numeric(
        work.get("evaluated_test_folds"), errors="coerce"
    ).fillna(0)
    work["median_test_expectancy_bps"] = pd.to_numeric(
        work.get("median_test_expectancy_bps"), errors="coerce"
    )

    eligible = work.loc[
        work["status"].astype(str).isin(CANDIDATE_STATUSES)
        & (work["selected_folds"] >= 2)
        & work["median_test_expectancy_bps"].notna()
        & (work["median_test_expectancy_bps"] > 0)
    ].copy()

    eligible = eligible.sort_values(
        [
            "evaluated_test_folds",
            "median_test_expectancy_bps",
            "total_test_trades",
        ],
        ascending=[False, False, False],
    )

    return eligible.head(max(1, int(max_candidates))).reset_index(drop=True)


def evaluate_symbol_tests(
    trades: pd.DataFrame,
    folds: tuple[dict[str, tuple[pd.Timestamp, pd.Timestamp]], ...],
    *,
    minimum_test_trades: int,
    base_cost_bps_per_side: float,
    stress_cost_bps_per_side: float,
) -> dict[str, Any]:
    rows = []
    for fold_number, periods in enumerate(folds, start=1):
        test = trade_metrics(
            trades,
            periods["test"][0],
            periods["test"][1],
            cost_bps_per_side=base_cost_bps_per_side,
        )
        stress = trade_metrics(
            trades,
            periods["test"][0],
            periods["test"][1],
            cost_bps_per_side=stress_cost_bps_per_side,
        )
        usable = int(test["trades"]) >= int(minimum_test_trades)
        rows.append(
            {
                "fold": fold_number,
                "test_trades": int(test["trades"]),
                "test_expectancy_bps": float(test["net_expectancy_bps"])
                if math.isfinite(float(test["net_expectancy_bps"]))
                else math.nan,
                "stress_expectancy_bps": float(stress["net_expectancy_bps"])
                if math.isfinite(float(stress["net_expectancy_bps"]))
                else math.nan,
                "test_profit_factor": float(test["profit_factor"])
                if math.isfinite(float(test["profit_factor"]))
                else math.inf,
                "test_usable": bool(usable),
            }
        )

    frame = pd.DataFrame(rows)
    usable = frame.loc[frame["test_usable"]].copy()

    if usable.empty:
        return {
            "evaluated_test_folds": 0,
            "total_test_trades": 0,
            "positive_test_fold_ratio": math.nan,
            "stress_positive_test_fold_ratio": math.nan,
            "median_test_expectancy_bps": math.nan,
            "median_stress_test_expectancy_bps": math.nan,
            "worst_test_expectancy_bps": math.nan,
            "median_test_profit_factor": math.nan,
            "fold_rows": rows,
        }

    return {
        "evaluated_test_folds": int(len(usable)),
        "total_test_trades": int(usable["test_trades"].sum()),
        "positive_test_fold_ratio": float(
            (usable["test_expectancy_bps"] > 0).mean()
        ),
        "stress_positive_test_fold_ratio": float(
            (usable["stress_expectancy_bps"] > 0).mean()
        ),
        "median_test_expectancy_bps": float(
            usable["test_expectancy_bps"].median()
        ),
        "median_stress_test_expectancy_bps": float(
            usable["stress_expectancy_bps"].median()
        ),
        "worst_test_expectancy_bps": float(
            usable["test_expectancy_bps"].min()
        ),
        "median_test_profit_factor": float(
            usable["test_profit_factor"].replace([math.inf], math.nan).median()
        )
        if usable["test_profit_factor"].replace([math.inf], math.nan).notna().any()
        else math.inf,
        "fold_rows": rows,
    }


def aggregate_generalization(
    symbol_results: pd.DataFrame,
    *,
    minimum_evaluated_test_folds: int = 2,
    minimum_eligible_symbols: int = 3,
    minimum_total_test_trades: int = 60,
    minimum_positive_symbol_ratio: float = 0.60,
    minimum_stress_positive_symbol_ratio: float = 0.50,
    minimum_median_expectancy_bps: float = 0.0,
    minimum_median_stress_expectancy_bps: float = 0.0,
    minimum_worst_symbol_expectancy_bps: float = -50.0,
) -> pd.DataFrame:
    columns = [
        "hypothesis_id",
        "eligible_symbols",
        "evaluated_symbols",
        "total_test_trades",
        "positive_symbol_ratio",
        "stress_positive_symbol_ratio",
        "median_symbol_expectancy_bps",
        "median_symbol_stress_expectancy_bps",
        "worst_symbol_expectancy_bps",
        "status",
        "promotion_stage",
        "cross_engine_validated",
        "dynamic_universe_generalized",
        "execution_authority",
    ]
    if symbol_results.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for hypothesis_id, group in symbol_results.groupby("hypothesis_id"):
        eligible = group.loc[
            pd.to_numeric(
                group["evaluated_test_folds"], errors="coerce"
            ).fillna(0)
            >= int(minimum_evaluated_test_folds)
        ].copy()

        if eligible.empty:
            rows.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "eligible_symbols": 0,
                    "evaluated_symbols": int(group["symbol"].nunique()),
                    "total_test_trades": 0,
                    "positive_symbol_ratio": math.nan,
                    "stress_positive_symbol_ratio": math.nan,
                    "median_symbol_expectancy_bps": math.nan,
                    "median_symbol_stress_expectancy_bps": math.nan,
                    "worst_symbol_expectancy_bps": math.nan,
                    "status": "NOT_EVALUABLE",
                    "promotion_stage": "RESEARCH_ONLY",
                    "cross_engine_validated": False,
                    "dynamic_universe_generalized": False,
                    "execution_authority": "NONE",
                }
            )
            continue

        positive = float(
            (eligible["median_test_expectancy_bps"] > 0).mean()
        )
        stress_positive = float(
            (eligible["median_stress_test_expectancy_bps"] > 0).mean()
        )
        median_expectancy = float(
            eligible["median_test_expectancy_bps"].median()
        )
        median_stress = float(
            eligible["median_stress_test_expectancy_bps"].median()
        )
        worst = float(
            eligible["median_test_expectancy_bps"].min()
        )
        total_trades = int(
            pd.to_numeric(
                eligible["total_test_trades"], errors="coerce"
            ).fillna(0).sum()
        )
        passed = (
            len(eligible) >= int(minimum_eligible_symbols)
            and total_trades >= int(minimum_total_test_trades)
            and positive >= float(minimum_positive_symbol_ratio)
            and stress_positive
            >= float(minimum_stress_positive_symbol_ratio)
            and median_expectancy
            > float(minimum_median_expectancy_bps)
            and median_stress
            > float(minimum_median_stress_expectancy_bps)
            and worst
            > float(minimum_worst_symbol_expectancy_bps)
        )

        rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "eligible_symbols": int(len(eligible)),
                "evaluated_symbols": int(group["symbol"].nunique()),
                "total_test_trades": total_trades,
                "positive_symbol_ratio": positive,
                "stress_positive_symbol_ratio": stress_positive,
                "median_symbol_expectancy_bps": median_expectancy,
                "median_symbol_stress_expectancy_bps": median_stress,
                "worst_symbol_expectancy_bps": worst,
                "status": (
                    "DYNAMIC_UNIVERSE_VALIDATED"
                    if passed
                    else "DYNAMIC_UNIVERSE_REJECT"
                ),
                "promotion_stage": (
                    "CROSS_ENGINE_VALIDATION_QUEUE"
                    if passed
                    else "REJECTED_AFTER_GENERALIZATION"
                ),
                "cross_engine_validated": False,
                "dynamic_universe_generalized": bool(passed),
                "execution_authority": "NONE",
            }
        )

    return pd.DataFrame(rows, columns=columns)
