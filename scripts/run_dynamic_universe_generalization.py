#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stocks.research.dynamic_universe_generalization import (
    build_universe_plan,
    configured_holdout_symbols,
    evaluate_generalization,
    load_one_hour_frames,
    walkforward_readiness,
)
from stocks.research.walkforward_splits import rolling_periods

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config/strategy_validation_pipeline.json"
REGISTRY_PATH = ROOT / "artifacts/research_runtime/research_candidate_registry/registry.csv"
VALIDATED_PATH = ROOT / "artifacts/research_runtime/validated_strategy_registry/registry.csv"
CROSSCHECK_PATH = ROOT / "artifacts/research_runtime/indicator_pybroker_crosscheck/summary.csv"
OUTPUT = ROOT / "artifacts/research_runtime/dynamic_universe_generalization"


def main() -> int:
    if not REGISTRY_PATH.is_file():
        raise FileNotFoundError(f"build research candidate registry first: {REGISTRY_PATH}")
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    development = {str(x).upper() for x in policy["development_symbols"]}
    holdout = configured_holdout_symbols(ROOT)
    registry = pd.read_csv(REGISTRY_PATH)
    validated = pd.read_csv(VALIDATED_PATH) if VALIDATED_PATH.is_file() else pd.DataFrame()
    cross = pd.read_csv(CROSSCHECK_PATH) if CROSSCHECK_PATH.is_file() else pd.DataFrame()

    plan = build_universe_plan(
        ROOT,
        development_symbols=development,
        holdout_symbols=holdout,
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plan.to_csv(OUTPUT / "universe_plan.csv", index=False)

    eligible = plan.get("eligible_unseen_1h", pd.Series(dtype=bool)).fillna(False) if not plan.empty else pd.Series(dtype=bool)
    unseen_symbols = plan.loc[eligible, "symbol"].astype(str).tolist() if not plan.empty else []
    holdout_config = json.loads((ROOT / "config/generalization_holdout_v1.json").read_text(encoding="utf-8"))
    min_rows = int(holdout_config.get("minimum_rows", 4000))
    frames = load_one_hour_frames(ROOT, unseen_symbols, min_rows=min_rows)
    minimum_symbols = int(policy["generalization"]["min_unseen_symbols_available"])
    readiness = walkforward_readiness(
        frames,
        min_symbols=minimum_symbols,
        min_rows=min_rows,
    )

    print(
        "GENERALIZATION_UNIVERSE",
        "LOCAL_1H", int(plan.get("has_1h", pd.Series(dtype=bool)).sum()) if not plan.empty else 0,
        "HOLDOUT", len(holdout),
        "UNSEEN_HOLDOUT_1H", len(frames),
        "READY", readiness["ready"],
        "REASON", readiness["reason"],
        "CONTEXTUAL", int(plan.get("contextual_candidate", pd.Series(dtype=bool)).sum()) if not plan.empty else 0,
    )

    validated_map = {str(row["hypothesis_id"]): row for row in validated.to_dict(orient="records")} if not validated.empty else {}
    cross_map = {str(row["hypothesis_id"]): row for row in cross.to_dict(orient="records")} if not cross.empty else {}
    summary_rows: list[dict] = []
    fold_parts: list[pd.DataFrame] = []
    symbol_parts: list[pd.DataFrame] = []

    folds = []
    if readiness["ready"]:
        anchor_symbol = max(frames, key=lambda symbol: len(frames[symbol]))
        index = pd.DatetimeIndex(pd.to_datetime(frames[anchor_symbol]["date"], utc=True)).sort_values().drop_duplicates()
        try:
            folds = rolling_periods(
                index,
                hold_bars=int(policy["purge_bars"]),
                requested_folds=int(policy["folds"]),
            )
        except ValueError as exc:
            readiness = {
                **readiness,
                "ready": False,
                "reason": f"WALKFORWARD_NOT_EVALUABLE:{type(exc).__name__}:{exc}",
            }
            folds = []

    for row in registry.to_dict(orient="records"):
        hypothesis_id = str(row["hypothesis_id"])
        source_engine = str(row.get("source_engine") or "")
        execution_contract = "NEXT_OPEN_REPLAY"
        if source_engine == "strategy_factory_1h" and hypothesis_id in validated_map:
            execution_contract = str(validated_map[hypothesis_id].get("execution_contract") or "NEXT_OPEN_REPLAY")
        elif source_engine == "indicator_discovery_v1":
            execution_contract = "NEXT_OPEN_REPLAY"

        if execution_contract != "NEXT_OPEN_REPLAY":
            summary_rows.append({
                "hypothesis_id": hypothesis_id,
                "strategy": row["strategy"],
                "family": row["family"],
                "source_engine": source_engine,
                "execution_contract": execution_contract,
                "generalization_status": "ROUTE_TO_15M_GENERALIZATION",
                "generalization_passed": False,
                "generalization_evaluable": False,
                "unseen_symbols_available": len(frames),
                "execution_authority": "NONE",
            })
            continue

        if source_engine == "indicator_discovery_v1":
            cross_status = str(cross_map.get(hypothesis_id, {}).get("crosscheck_status") or "PENDING")
            if cross_status not in {"CROSS_ENGINE_VALIDATED", "CROSS_ENGINE_PROVISIONAL"}:
                summary_rows.append({
                    "hypothesis_id": hypothesis_id,
                    "strategy": row["strategy"],
                    "family": row["family"],
                    "source_engine": source_engine,
                    "execution_contract": execution_contract,
                    "generalization_status": "WAITING_CROSS_ENGINE",
                    "generalization_passed": False,
                    "generalization_evaluable": False,
                    "unseen_symbols_available": len(frames),
                    "execution_authority": "NONE",
                })
                continue

        if not readiness["ready"] or not frames or not folds:
            summary_rows.append({
                "hypothesis_id": hypothesis_id,
                "strategy": row["strategy"],
                "family": row["family"],
                "source_engine": source_engine,
                "execution_contract": execution_contract,
                "generalization_status": "NOT_EVALUABLE_INSUFFICIENT_UNSEEN_1H",
                "generalization_passed": False,
                "generalization_evaluable": False,
                "generalization_reasons": str(readiness.get("reason") or ""),
                "unseen_symbols_available": len(frames),
                "execution_authority": "NONE",
            })
            continue

        summary, fold_frame, symbol_frame = evaluate_generalization(
            row,
            frames,
            policy=policy["generalization"],
            folds=folds,
            base_cost_bps_per_side=float(policy["base_cost_bps_per_side"]),
            stress_cost_bps_per_side=float(policy["stress_cost_bps_per_side"]),
        )
        summary["execution_contract"] = execution_contract
        summary_rows.append(summary)
        if not fold_frame.empty:
            fold_parts.append(fold_frame)
        if not symbol_frame.empty:
            symbol_parts.append(symbol_frame)
        print(
            "GENERALIZE", hypothesis_id, row["strategy"], summary["generalization_status"],
            "UNSEEN_TRADED", summary["unseen_symbols_traded"],
            "OOS_TRADES", summary["oos_trades"],
            "POS_SYMBOL", summary["positive_symbol_ratio"],
        )

    summary_frame = pd.DataFrame(summary_rows)
    summary_frame.to_csv(OUTPUT / "summary.csv", index=False)
    (pd.concat(fold_parts, ignore_index=True) if fold_parts else pd.DataFrame()).to_csv(OUTPUT / "fold_metrics.csv", index=False)
    (pd.concat(symbol_parts, ignore_index=True) if symbol_parts else pd.DataFrame()).to_csv(OUTPUT / "symbol_metrics.csv", index=False)

    holdout_mask = plan.get("generalization_holdout", pd.Series(dtype=bool)).fillna(False) if not plan.empty else pd.Series(dtype=bool)
    has_1h = plan.get("has_1h", pd.Series(dtype=bool)).fillna(False) if not plan.empty else pd.Series(dtype=bool)
    missing_holdout = plan.loc[holdout_mask & ~has_1h].copy() if not plan.empty else pd.DataFrame()
    missing_holdout.to_csv(OUTPUT / "missing_holdout_1h.csv", index=False)
    contextual_mask = plan.get("contextual_candidate", pd.Series(dtype=bool)).fillna(False) if not plan.empty else pd.Series(dtype=bool)
    missing_context_1h = plan.loc[contextual_mask & ~has_1h].copy() if not plan.empty else pd.DataFrame()
    missing_context_1h.to_csv(OUTPUT / "missing_contextual_1h.csv", index=False)

    audit = {
        "schema": "dynamic_universe_generalization_v2_4",
        "development_symbols": sorted(development),
        "holdout_symbols": sorted(holdout),
        "holdout_1h_available": len(frames),
        "walkforward_ready": bool(readiness["ready"]),
        "walkforward_reason": readiness["reason"],
        "anchor_rows": int(readiness["anchor_rows"]),
        "contextual_candidates": int(contextual_mask.sum()) if not plan.empty else 0,
        "holdout_missing_1h": int(len(missing_holdout)),
        "validated": int((summary_frame.get("generalization_status", pd.Series(dtype=str)) == "DYNAMIC_UNIVERSE_VALIDATED").sum()),
        "rejected": int((summary_frame.get("generalization_status", pd.Series(dtype=str)) == "DYNAMIC_UNIVERSE_REJECT").sum()),
        "not_evaluable": int(summary_frame.get("generalization_status", pd.Series(dtype=str)).astype(str).str.startswith("NOT_EVALUABLE").sum()) if not summary_frame.empty else 0,
        "routed_to_15m": int((summary_frame.get("generalization_status", pd.Series(dtype=str)) == "ROUTE_TO_15M_GENERALIZATION").sum()),
        "current_screener_used_for_holdout_selection": False,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    (OUTPUT / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "DYNAMIC_UNIVERSE_GENERALIZATION",
        "VALIDATED", audit["validated"],
        "REJECTED", audit["rejected"],
        "NOT_EVALUABLE", audit["not_evaluable"],
        "ROUTE_15M", audit["routed_to_15m"],
    )
    if not summary_frame.empty:
        columns = [
            column for column in (
                "hypothesis_id", "strategy", "source_engine",
                "unseen_symbols_available", "unseen_symbols_traded",
                "oos_trades", "positive_fold_ratio", "positive_symbol_ratio",
                "median_expectancy_bps", "median_stress_expectancy_bps",
                "generalization_status",
            ) if column in summary_frame.columns
        ]
        print(summary_frame[columns].to_string(index=False))
    print("ARTIFACT_ROOT", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
