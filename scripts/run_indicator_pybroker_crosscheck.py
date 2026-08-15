#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from stocks.intelligence_agent.strategy_combo_research_lab import FeatureCache
from stocks.research.indicator_crosscheck import hypothesis_from_survivor_row, summarize_crosscheck_rows
from stocks.research.indicator_discovery import evaluate_indicator_hypothesis
from stocks.research.pybroker_crosscheck import replay_contract_audit, run_pybroker_replay
from stocks.research.strategy_factory_1h import contained_trades, prepare_one_hour_frame, trade_metrics
from stocks.research.walkforward_splits import rolling_periods

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config/strategy_validation_pipeline.json"
SURVIVOR_PATH = ROOT / "artifacts/research_runtime/indicator_discovery_1h/survivors.csv"
OUTPUT = ROOT / "artifacts/research_runtime/indicator_pybroker_crosscheck"


def _source(symbol: str) -> Path:
    for relative in (
        "data/canonical/provider_fabric",
        "data/adjusted",
        "data/derived",
        "data/processed",
    ):
        path = ROOT / relative / f"{symbol}_1h.parquet"
        if path.is_file():
            return path
    raise FileNotFoundError(f"{symbol}: 1h source missing")


def _frames(symbols: list[str]) -> dict[str, pd.DataFrame]:
    result = {}
    for symbol in symbols:
        raw = pd.read_parquet(_source(symbol))
        result[symbol] = prepare_one_hour_frame(raw, symbol)
    return result


def main() -> int:
    if not SURVIVOR_PATH.is_file():
        raise FileNotFoundError(f"run indicator discovery first: {SURVIVOR_PATH}")

    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    survivors = pd.read_csv(SURVIVOR_PATH)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    if survivors.empty:
        pd.DataFrame().to_csv(OUTPUT / "summary.csv", index=False)
        (OUTPUT / "audit.json").write_text(json.dumps({"schema": "indicator_pybroker_crosscheck_v1", "survivors": 0, "execution_authority": "NONE"}, indent=2) + "\n", encoding="utf-8")
        print("INDICATOR_PYBROKER_CROSSCHECK SURVIVORS 0")
        return 0

    symbols = [str(x).upper() for x in policy["development_symbols"]]
    frames = _frames(symbols)
    caches = {symbol: FeatureCache(frame) for symbol, frame in frames.items()}
    anchor = frames["SPY"] if "SPY" in frames else next(iter(frames.values()))
    index = pd.DatetimeIndex(pd.to_datetime(anchor["date"], utc=True)).sort_values().drop_duplicates()
    folds = rolling_periods(index, hold_bars=int(policy["purge_bars"]), requested_folds=int(policy["folds"]))

    fold_rows: list[dict] = []
    summary_rows: list[dict] = []
    all_survivor_trades: list[pd.DataFrame] = []

    for raw in survivors.to_dict(orient="records"):
        hypothesis = hypothesis_from_survivor_row(raw)
        trades = evaluate_indicator_hypothesis(hypothesis, frames, caches)
        if not trades.empty:
            all_survivor_trades.append(trades.assign(factory_status=str(raw.get("status", ""))))

        contract = replay_contract_audit(trades, strategy=hypothesis.template)
        if not contract["compatible"]:
            summary_rows.append(
                {
                    "hypothesis_id": hypothesis.hypothesis_id,
                    "strategy": hypothesis.template,
                    "family": hypothesis.family,
                    "factory_status": str(raw.get("status", "")),
                    "execution_contract": contract["execution_contract"],
                    "execution_route": contract["route"],
                    "crosscheck_status": "ROUTE_TO_EXECUTION_CHRONOLOGY_VALIDATION",
                    "execution_authority": "NONE",
                }
            )
            continue

        rows_for_hypothesis: list[dict] = []
        oos_parts: list[pd.DataFrame] = []
        for fold_number, periods in enumerate(folds, start=1):
            test = contained_trades(trades, periods["test"])
            base = trade_metrics(test, cost_bps_per_side=float(policy["base_cost_bps_per_side"]))
            stress = trade_metrics(test, cost_bps_per_side=float(policy["stress_cost_bps_per_side"]))
            usable = len(test) >= int(policy["min_test_trades"])
            row = {
                "hypothesis_id": hypothesis.hypothesis_id,
                "strategy": hypothesis.template,
                "family": hypothesis.family,
                "fold": fold_number,
                "usable": bool(usable),
                "canonical_trades": int(len(test)),
                "canonical_base_expectancy_bps": float(base["net_expectancy_bps"]),
                "canonical_stress_expectancy_bps": float(stress["net_expectancy_bps"]),
            }
            if not test.empty:
                replay_base = run_pybroker_replay(frames, test, cost_bps_per_side=float(policy["base_cost_bps_per_side"]))
                replay_stress = run_pybroker_replay(frames, test, cost_bps_per_side=float(policy["stress_cost_bps_per_side"]))
                row.update({f"pybroker_base_{k}": v for k, v in replay_base.items()})
                row.update({f"pybroker_stress_{k}": v for k, v in replay_stress.items()})
                oos_parts.append(test.assign(fold=fold_number))
            fold_rows.append(row)
            rows_for_hypothesis.append(row)
            print("INDICATOR_CROSSCHECK", hypothesis.hypothesis_id, "FOLD", fold_number, "TRADES", len(test), "BASE_BPS", base["net_expectancy_bps"], "STRESS_BPS", stress["net_expectancy_bps"], "MATCH", row.get("pybroker_base_schedule_match_ratio"))

        oos = pd.concat(oos_parts, ignore_index=True) if oos_parts else trades.iloc[0:0]
        summary = summarize_crosscheck_rows(rows_for_hypothesis, all_test_trades=oos, stress_cost_bps_per_side=float(policy["stress_cost_bps_per_side"]))
        if str(raw.get("status")) == "PROVISIONAL_SURVIVOR" and summary["crosscheck_status"] == "CROSS_ENGINE_VALIDATED":
            summary["crosscheck_status"] = "CROSS_ENGINE_PROVISIONAL"
        summary_rows.append(
            {
                "hypothesis_id": hypothesis.hypothesis_id,
                "strategy": hypothesis.template,
                "family": hypothesis.family,
                "factory_status": str(raw.get("status", "")),
                "execution_contract": hypothesis.execution_contract,
                "execution_route": "PYBROKER_NEXT_OPEN",
                **summary,
                "execution_authority": "NONE",
            }
        )

    fold_frame = pd.DataFrame(fold_rows)
    summary_frame = pd.DataFrame(summary_rows)
    fold_frame.to_csv(OUTPUT / "fold_results.csv", index=False)
    summary_frame.to_csv(OUTPUT / "summary.csv", index=False)
    if all_survivor_trades:
        pd.concat(all_survivor_trades, ignore_index=True).to_parquet(OUTPUT / "survivor_trades.parquet", index=False)

    audit = {
        "schema": "indicator_pybroker_crosscheck_v1",
        "survivors": int(len(survivors)),
        "validated": int((summary_frame.get("crosscheck_status", pd.Series(dtype=str)) == "CROSS_ENGINE_VALIDATED").sum()),
        "provisional": int((summary_frame.get("crosscheck_status", pd.Series(dtype=str)) == "CROSS_ENGINE_PROVISIONAL").sum()),
        "rejected": int((summary_frame.get("crosscheck_status", pd.Series(dtype=str)) == "CROSS_ENGINE_REJECT").sum()),
        "execution_authority": "NONE",
        "broker_calls": 0,
    }
    (OUTPUT / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("INDICATOR_PYBROKER_CROSSCHECK", "VALIDATED", audit["validated"], "PROVISIONAL", audit["provisional"], "REJECTED", audit["rejected"])
    if not summary_frame.empty:
        print(summary_frame[[c for c in ["hypothesis_id", "strategy", "factory_status", "usable_folds", "positive_fold_ratio", "stress_positive_fold_ratio", "median_base_expectancy_bps", "worst_base_expectancy_bps", "positive_symbol_ratio", "max_symbol_trade_share", "crosscheck_status"] if c in summary_frame.columns]].to_string(index=False))
    print("ARTIFACT_ROOT", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
