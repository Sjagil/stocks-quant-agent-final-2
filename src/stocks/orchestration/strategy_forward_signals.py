from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.orchestration.generated_strategy_forward_signals_v2_23 import (
    GENERATED_NEXT_OPEN_STRATEGIES,
    evaluate_latest_generated_entry_condition,
)
from stocks.intelligence_agent.strategy_combo_research_lab import (
    FeatureCache,
)
from stocks.research.dynamic_universe_generalization import (
    discover_interval_sources,
)
from stocks.research.indicator_discovery import (
    obv,
    relative_volume,
)
from stocks.research.strategy_factory_1h import (
    prepare_one_hour_frame,
)

LEGACY_NEXT_OPEN_STRATEGIES = frozenset(
    {
        "rsi_threshold_exit",
        "obv_breakout",
    }
)
SUPPORTED_NEXT_OPEN_STRATEGIES = frozenset(
    LEGACY_NEXT_OPEN_STRATEGIES | GENERATED_NEXT_OPEN_STRATEGIES
)


def _params(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("params_json", "{}")
    if isinstance(raw, dict):
        return dict(raw)
    return dict(json.loads(str(raw)))


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def latest_rsi_threshold_signal(
    frame: pd.DataFrame,
    params: dict[str, Any],
) -> dict[str, Any]:
    cache = FeatureCache(frame)
    rsi = cache.rsi(int(params["rsi_period"]))
    value = _finite(rsi[-1]) if len(rsi) else None
    threshold = float(params["entry_threshold"])

    ready = bool(
        value is not None
        and value < threshold
    )

    return {
        "ready": ready,
        "indicator": "RSI",
        "indicator_value": value,
        "threshold": threshold,
        "reason": (
            f"RSI_{value:.4f}_LT_{threshold:.4f}"
            if ready and value is not None
            else "RSI_ENTRY_CONDITION_FALSE"
        ),
    }


def latest_obv_breakout_signal(
    frame: pd.DataFrame,
    params: dict[str, Any],
) -> dict[str, Any]:
    cache = FeatureCache(frame)
    close = cache.arr("close")
    values = obv(cache)

    span = int(params["obv_ema"])
    obv_mean = (
        pd.Series(values)
        .ewm(
            span=span,
            adjust=False,
            min_periods=span,
        )
        .mean()
        .to_numpy()
    )

    prior_high = cache.rolling_max(
        "high",
        int(params["lookback"]),
        shift=1,
    )
    rvol = relative_volume(
        cache,
        int(params["rvol_period"]),
    )

    if not len(close):
        return {
            "ready": False,
            "reason": "EMPTY_FRAME",
        }

    close_value = _finite(close[-1])
    high_value = _finite(prior_high[-1])
    obv_value = _finite(values[-1])
    obv_mean_value = _finite(obv_mean[-1])
    rvol_value = _finite(rvol[-1])
    rvol_min = float(params["rvol_min"])

    ready = bool(
        close_value is not None
        and high_value is not None
        and obv_value is not None
        and obv_mean_value is not None
        and rvol_value is not None
        and close_value > high_value
        and obv_value > obv_mean_value
        and rvol_value >= rvol_min
    )

    return {
        "ready": ready,
        "indicator": "OBV_BREAKOUT",
        "close": close_value,
        "prior_high": high_value,
        "obv": obv_value,
        "obv_ema": obv_mean_value,
        "relative_volume": rvol_value,
        "relative_volume_min": rvol_min,
        "reason": (
            "OBV_BREAKOUT_ENTRY_CONDITION_TRUE"
            if ready
            else "OBV_BREAKOUT_ENTRY_CONDITION_FALSE"
        ),
    }


def evaluate_latest_entry_condition(
    *,
    strategy: str,
    frame: pd.DataFrame,
    params: dict[str, Any],
) -> dict[str, Any]:
    if strategy in GENERATED_NEXT_OPEN_STRATEGIES:
        return evaluate_latest_generated_entry_condition(
            strategy=strategy,
            frame=frame,
            params=params,
        )

    if strategy == "rsi_threshold_exit":
        return latest_rsi_threshold_signal(frame, params)

    if strategy == "obv_breakout":
        return latest_obv_breakout_signal(frame, params)

    return {
        "ready": False,
        "reason": "STRATEGY_FORWARD_ADAPTER_NOT_IMPLEMENTED",
    }


def build_forward_trigger_map(
    project_root: str | Path,
    matrix: pd.DataFrame,
    *,
    strategy_registry: pd.DataFrame | None = None,
    required_status_column: str = "roster_status",
    required_status: str = "BROADLY_VALIDATED_FINALIST",
) -> dict[tuple[str, str], dict[str, Any]]:
    root = Path(project_root).resolve()
    if strategy_registry is None:
        roster_path = (
            root
            / "artifacts/research_runtime/"
            "final_strategy_roster/roster.csv"
        )
        if not roster_path.is_file() or matrix.empty:
            return {}
        roster = pd.read_csv(roster_path)
        missing_reason = "STRATEGY_NOT_BROADLY_VALIDATED"
    else:
        roster = strategy_registry.copy()
        missing_reason = "STRATEGY_NOT_DEPLOYED_FOR_RESEARCH_SIGNALS"
        if matrix.empty:
            return {}

    required_columns = {
        "hypothesis_id",
        "strategy",
        "params_json",
        required_status_column,
    }
    missing_columns = sorted(required_columns.difference(roster.columns))
    if missing_columns:
        raise ValueError(
            f"strategy registry missing columns {missing_columns}"
        )
    roster_map = {
        str(row["hypothesis_id"]): row
        for row in roster.to_dict(orient="records")
        if str(row.get(required_status_column) or "") == required_status
    }

    sources = discover_interval_sources(root, "1h")
    output: dict[tuple[str, str], dict[str, Any]] = {}
    frame_cache: dict[str, pd.DataFrame] = {}

    for row in matrix.to_dict(orient="records"):
        symbol = str(row["symbol"]).upper()
        hypothesis_id = str(row["hypothesis_id"])
        strategy = str(row["strategy"])

        key = (symbol, hypothesis_id)

        if strategy not in SUPPORTED_NEXT_OPEN_STRATEGIES:
            output[key] = {
                "ready": False,
                "reason": "STRATEGY_FORWARD_ADAPTER_NOT_IMPLEMENTED",
            }
            continue

        roster_row = roster_map.get(hypothesis_id)
        if roster_row is None:
            output[key] = {
                "ready": False,
                "reason": missing_reason,
            }
            continue

        path = sources.get(symbol)
        if path is None:
            output[key] = {
                "ready": False,
                "reason": "CANONICAL_1H_SOURCE_MISSING",
            }
            continue

        try:
            if symbol not in frame_cache:
                frame_cache[symbol] = prepare_one_hour_frame(
                    pd.read_parquet(path),
                    symbol,
                )

            frame = frame_cache[symbol]
            signal = evaluate_latest_entry_condition(
                strategy=strategy,
                frame=frame,
                params=_params(roster_row),
            )
            signal["signal_bar_time"] = (
                pd.Timestamp(frame["date"].iloc[-1]).isoformat()
                if not frame.empty
                else None
            )
            signal["execution_contract"] = "NEXT_OPEN_REPLAY"
            signal["canonical_source"] = str(path)
            output[key] = signal

        except Exception as exc:  # noqa: BLE001
            output[key] = {
                "ready": False,
                "reason": f"{type(exc).__name__}:{exc}",
            }

    return output


def research_entry_ready(
    *,
    local_evidence_positive: bool,
    source_setup_state: str,
    trigger_ready: bool,
) -> bool:
    if not local_evidence_positive:
        return False

    # A forced boundary state is an already-open replay position.
    if source_setup_state == "ACTIVE_AT_DATA_BOUNDARY":
        return False

    return bool(trigger_ready)


__all__ = [
    "GENERATED_NEXT_OPEN_STRATEGIES",
    "LEGACY_NEXT_OPEN_STRATEGIES",
    "SUPPORTED_NEXT_OPEN_STRATEGIES",
    "build_forward_trigger_map",
    "evaluate_latest_entry_condition",
    "latest_obv_breakout_signal",
    "latest_rsi_threshold_signal",
    "research_entry_ready",
]
