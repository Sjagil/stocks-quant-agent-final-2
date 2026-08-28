
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stocks.intelligence_agent.strategy_combo_research_lab import FeatureCache
from stocks.research.dynamic_universe_generalization import discover_interval_sources
from stocks.research.indicator_discovery import (
    IndicatorHypothesis,
    evaluate_indicator_hypothesis,
)
from stocks.research.strategy_factory_1h import (
    OneHourHypothesis,
    build_feature_caches,
    eligible_1h_specs,
    evaluate_hypothesis,
    prepare_one_hour_frame,
    trade_metrics,
)


def _read(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path)


def _params(row: dict[str, Any]) -> dict:
    raw = row.get("params_json", "{}")
    return dict(raw) if isinstance(raw, dict) else json.loads(str(raw))


def _evaluate(
    row: dict[str, Any],
    *,
    symbol: str,
    frame: pd.DataFrame,
) -> pd.DataFrame:
    params = _params(row)
    source = str(row.get("source_engine") or "")

    if source == "indicator_discovery_v1":
        hypothesis = IndicatorHypothesis(
            hypothesis_id=str(row["hypothesis_id"]),
            template=str(row["strategy"]),
            family=str(row["family"]),
            params=params,
            execution_contract="NEXT_OPEN_REPLAY",
        )
        return evaluate_indicator_hypothesis(
            hypothesis,
            {symbol: frame},
            {symbol: FeatureCache(frame)},
        )

    if source == "strategy_generation_v2_22":
        from stocks.research.strategy_generation_v2_22 import (
            GeneratedStrategyHypothesis,
            evaluate_generated_hypothesis,
        )

        hypothesis = GeneratedStrategyHypothesis(
            hypothesis_id=str(row["hypothesis_id"]),
            strategy=str(row["strategy"]),
            family=str(row["family"]),
            rationale=str(row.get("rationale") or ""),
            params=params,
            complexity=int(row.get("complexity") or len(params)),
        )
        return evaluate_generated_hypothesis(
            hypothesis,
            {symbol: frame},
            {symbol: FeatureCache(frame)},
        )

    specs = {spec.name: spec for spec in eligible_1h_specs()}
    strategy = str(row["strategy"])
    if strategy not in specs:
        raise KeyError(f"missing strategy spec: {strategy}")

    hypothesis = OneHourHypothesis(
        hypothesis_id=str(row["hypothesis_id"]),
        strategy=strategy,
        family=str(row["family"]),
        horizon="CURRENT_CANDIDATE_MATRIX",
        params=params,
    )
    caches = build_feature_caches({symbol: frame})
    return evaluate_hypothesis(
        hypothesis,
        specs[strategy],
        {symbol: frame},
        caches,
    )


def _bars_since(
    dates: pd.DatetimeIndex,
    timestamp: pd.Timestamp,
) -> int:
    values = dates.view("int64")
    position = int(
        np.searchsorted(values, int(timestamp.value), side="left")
    )
    position = min(max(position, 0), len(dates) - 1)
    return int(len(dates) - 1 - position)


def build_candidate_strategy_matrix(
    project_root: str | Path,
    *,
    trailing_days: int = 730,
    recent_bars: int = 8,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()

    candidates = _read(
        root / "artifacts/research_runtime/contextual_discovery/candidates.csv"
    )
    hydration = _read(
        root / "artifacts/research_runtime/contextual_1h_hydration/usable_candidates.csv"
    )
    roster = _read(
        root / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    )

    if candidates.empty or hydration.empty or roster.empty:
        return pd.DataFrame(), pd.DataFrame(), {
            "schema": "candidate_strategy_matrix_v1",
            "matrix_rows": 0,
            "opportunity_rows": 0,
            "reason": "required_artifact_missing_or_empty",
            "execution_authority": "NONE",
        }

    hydrated_symbols = set(
        hydration["symbol"].dropna().astype(str).str.upper()
    )
    strategy_rows = roster.loc[
        (roster["roster_status"] == "BROADLY_VALIDATED_FINALIST")
        & (roster["execution_contract"] == "NEXT_OPEN_REPLAY")
    ].copy()

    sources = discover_interval_sources(root, "1h")
    policy = json.loads(
        (
            root / "config/strategy_validation_pipeline.json"
        ).read_text(encoding="utf-8")
    )
    base_cost = float(policy["base_cost_bps_per_side"])
    stress_cost = float(policy["stress_cost_bps_per_side"])

    candidate_map = {
        str(row["symbol"]).upper(): row
        for row in candidates.to_dict(orient="records")
    }

    rows = []

    for symbol in sorted(hydrated_symbols):
        path = sources.get(symbol)
        if path is None:
            continue

        frame = prepare_one_hour_frame(
            pd.read_parquet(path),
            symbol,
        )
        if frame.empty:
            continue

        dates = pd.DatetimeIndex(
            pd.to_datetime(frame["date"], utc=True)
        )
        last_bar = dates.max()
        cutoff = last_bar - pd.Timedelta(days=int(trailing_days))
        context = candidate_map.get(symbol, {})

        for strategy in strategy_rows.to_dict(orient="records"):
            trades = _evaluate(
                strategy,
                symbol=symbol,
                frame=frame,
            )
            trailing = (
                trades.loc[
                    pd.to_datetime(
                        trades["entry_time"],
                        utc=True,
                    )
                    >= cutoff
                ].copy()
                if not trades.empty
                else trades
            )

            base = trade_metrics(
                trailing,
                cost_bps_per_side=base_cost,
            )
            stress = trade_metrics(
                trailing,
                cost_bps_per_side=stress_cost,
            )

            latest = trades.iloc[-1] if not trades.empty else None
            bars_since_entry = None
            setup_state = "NO_SIGNAL_HISTORY"
            latest_score = None

            if latest is not None:
                entry_time = pd.Timestamp(latest["entry_time"])
                entry_time = (
                    entry_time.tz_localize("UTC")
                    if entry_time.tzinfo is None
                    else entry_time.tz_convert("UTC")
                )
                exit_time = pd.Timestamp(latest["exit_time"])
                exit_time = (
                    exit_time.tz_localize("UTC")
                    if exit_time.tzinfo is None
                    else exit_time.tz_convert("UTC")
                )
                bars_since_entry = _bars_since(dates, entry_time)
                latest_score = float(latest.get("score", 0.0))
                forced = bool(latest.get("forced", False))

                if forced and exit_time == last_bar:
                    setup_state = "ACTIVE_AT_DATA_BOUNDARY"
                elif bars_since_entry <= int(recent_bars):
                    setup_state = "RECENT_ENTRY"
                else:
                    setup_state = "DORMANT"

            base_exp = float(base["net_expectancy_bps"])
            stress_exp = float(stress["net_expectancy_bps"])
            pf = float(base["profit_factor"])

            positive_local = (
                int(base["trades"]) >= 8
                and math.isfinite(base_exp)
                and math.isfinite(stress_exp)
                and base_exp > 0
                and stress_exp > 0
                and pf > 1.0
            )

            context_score = float(
                context.get("contextual_score", 50.0) or 50.0
            )
            performance_component = max(
                0.0,
                min(
                    100.0,
                    50.0
                    + (base_exp if math.isfinite(base_exp) else -100.0) / 4.0
                    + (
                        stress_exp
                        if math.isfinite(stress_exp)
                        else -100.0
                    )
                    / 8.0,
                ),
            )
            setup_component = {
                "ACTIVE_AT_DATA_BOUNDARY": 100.0,
                "RECENT_ENTRY": 80.0,
                "DORMANT": 25.0,
                "NO_SIGNAL_HISTORY": 0.0,
            }[setup_state]
            applicability = (
                0.45 * context_score
                + 0.35 * performance_component
                + 0.20 * setup_component
            )

            rows.append(
                {
                    "symbol": symbol,
                    "hypothesis_id": strategy["hypothesis_id"],
                    "strategy": strategy["strategy"],
                    "family": strategy["family"],
                    "research_lane": context.get(
                        "research_lane",
                        context.get("lane"),
                    ),
                    "shariah_gate": context.get("shariah_gate"),
                    "trade_eligible": bool(
                        context.get("trade_eligible", False)
                    ),
                    "contextual_score": context_score,
                    "trailing_days": int(trailing_days),
                    "trailing_trades": int(base["trades"]),
                    "trailing_expectancy_bps": base_exp,
                    "trailing_stress_expectancy_bps": stress_exp,
                    "trailing_profit_factor": pf,
                    "trailing_win_rate": base["win_rate"],
                    "setup_state": setup_state,
                    "bars_since_entry": bars_since_entry,
                    "latest_strategy_score": latest_score,
                    "local_evidence_positive": positive_local,
                    "applicability_score": float(applicability),
                    "research_opportunity": (
                        positive_local
                        and setup_state
                        in {
                            "ACTIVE_AT_DATA_BOUNDARY",
                            "RECENT_ENTRY",
                        }
                    ),
                    "strategy_assignment": "RESEARCH_ONLY",
                    "trade_gate": (
                        "PASS"
                        if bool(context.get("trade_eligible", False))
                        else "BLOCKED_PENDING_SHARIAH"
                    ),
                    "execution_authority": "NONE",
                    "broker_calls": 0,
                    "order_calls": 0,
                }
            )

    matrix = pd.DataFrame(rows)
    if not matrix.empty:
        matrix = (
            matrix.sort_values(
                [
                    "research_opportunity",
                    "applicability_score",
                    "contextual_score",
                    "symbol",
                    "strategy",
                ],
                ascending=[False, False, False, True, True],
            )
            .reset_index(drop=True)
        )

    opportunities = (
        matrix.loc[matrix["research_opportunity"]].copy()
        if not matrix.empty
        else pd.DataFrame()
    )

    audit = {
        "schema": "candidate_strategy_matrix_v1",
        "hydrated_symbols": len(hydrated_symbols),
        "broadly_validated_strategies": len(strategy_rows),
        "matrix_rows": len(matrix),
        "positive_local_evidence_rows": int(
            matrix["local_evidence_positive"].sum()
        ) if not matrix.empty else 0,
        "active_boundary_rows": int(
            (matrix["setup_state"] == "ACTIVE_AT_DATA_BOUNDARY").sum()
        ) if not matrix.empty else 0,
        "recent_entry_rows": int(
            (matrix["setup_state"] == "RECENT_ENTRY").sum()
        ) if not matrix.empty else 0,
        "opportunity_rows": len(opportunities),
        "strategy_parameters_retuned": False,
        "candidate_selection_used_for_generalization": False,
        "automatic_order_authority": False,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    return matrix, opportunities, audit


def write_candidate_strategy_matrix(
    project_root: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], Path]:
    root = Path(project_root).resolve()
    matrix, opportunities, audit = build_candidate_strategy_matrix(root)

    output = root / "artifacts/research_runtime/candidate_strategy_matrix"
    output.mkdir(parents=True, exist_ok=True)
    path = output / "matrix.csv"
    matrix.to_csv(path, index=False)
    opportunities.to_csv(output / "opportunities.csv", index=False)

    if not matrix.empty:
        summary = (
            matrix.sort_values(
                "applicability_score",
                ascending=False,
            )
            .groupby("symbol", as_index=False)
            .first()
        )
    else:
        summary = pd.DataFrame()

    summary.to_csv(output / "candidate_summary.csv", index=False)
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return matrix, opportunities, audit, path
