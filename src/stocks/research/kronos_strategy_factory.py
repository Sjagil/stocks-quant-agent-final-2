from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from stocks.rl.features import build_rl_features


@dataclass(frozen=True)
class KronosHypothesis:
    hypothesis_id: str
    template: str
    family: str
    params: dict[str, Any]

    @property
    def params_json(self) -> str:
        return json.dumps(
            self.params,
            sort_keys=True,
            separators=(",", ":"),
        )

    def as_record(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "template": self.template,
            "family": self.family,
            "params_json": self.params_json,
            "execution_contract": "NEXT_OPEN_TO_HORIZON_CLOSE",
            "source_engine": "kronos_foundation_model_v2_15",
            "research_stage": "LEAKAGE_SAFE_WALK_FORWARD",
            "execution_authority": "NONE",
        }


def _id(template: str, params: dict[str, Any]) -> str:
    payload = json.dumps(
        {"template": template, "params": params},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


def generate_kronos_hypotheses() -> list[KronosHypothesis]:
    specs: list[tuple[str, str, dict[str, Any]]] = []

    for threshold in (0.0025, 0.005, 0.0075, 0.01):
        specs.append(
            (
                "kronos_directional",
                "KRONOS_DIRECTION",
                {"min_terminal_return": threshold},
            )
        )

    for threshold in (0.0025, 0.005, 0.0075):
        for adx_min in (15.0, 20.0, 25.0):
            specs.append(
                (
                    "kronos_trend_confirmed",
                    "KRONOS_TREND",
                    {
                        "min_terminal_return": threshold,
                        "adx_min": adx_min,
                        "require_ema20_above_ema50": True,
                    },
                )
            )

    for threshold in (0.003, 0.006):
        for rsi_max in (45.0, 50.0, 55.0):
            specs.append(
                (
                    "kronos_pullback_recovery",
                    "KRONOS_PULLBACK",
                    {
                        "min_terminal_return": threshold,
                        "rsi_max": rsi_max,
                        "require_close_above_ema50": True,
                    },
                )
            )

    for upside in (0.006, 0.01, 0.015):
        for max_distance in (0.0025, 0.005, 0.01):
            specs.append(
                (
                    "kronos_breakout_pressure",
                    "KRONOS_BREAKOUT",
                    {
                        "min_max_upside": upside,
                        "max_donchian_high_distance": max_distance,
                        "min_adx": 15.0,
                    },
                )
            )

    for threshold in (0.003, 0.006):
        for downside_floor in (-0.03, -0.02, -0.01):
            specs.append(
                (
                    "kronos_asymmetric_path",
                    "KRONOS_ASYMMETRY",
                    {
                        "min_terminal_return": threshold,
                        "min_downside": downside_floor,
                    },
                )
            )

    return [
        KronosHypothesis(
            hypothesis_id=_id(template, params),
            template=template,
            family=family,
            params=params,
        )
        for template, family, params in specs
    ]


def _decision_features(bars: pd.DataFrame) -> pd.DataFrame:
    features = build_rl_features(bars)
    selected = pd.DataFrame(index=bars.index)
    for column in (
        "rsi_14",
        "adx_14",
        "donchian_high_dist_20",
        "volume_robust_z",
        "atr_pct",
    ):
        selected[column] = features[column]
    selected["close"] = bars["close"].astype(float)
    ema20 = bars["close"].ewm(span=20, adjust=False).mean()
    ema50 = bars["close"].ewm(span=50, adjust=False).mean()
    selected["ema20_above_ema50"] = ema20 > ema50
    selected["close_above_ema50"] = bars["close"] > ema50
    return selected


def _signal(row: pd.Series, hypothesis: KronosHypothesis) -> bool:
    p = hypothesis.params
    terminal = float(row["kronos_terminal_return"])
    upside = float(row["kronos_max_upside"])
    downside = float(row["kronos_min_downside"])

    if hypothesis.template == "kronos_directional":
        return terminal >= float(p["min_terminal_return"])

    if hypothesis.template == "kronos_trend_confirmed":
        return (
            terminal >= float(p["min_terminal_return"])
            and float(row["adx_14"]) >= float(p["adx_min"])
            and bool(row["ema20_above_ema50"])
        )

    if hypothesis.template == "kronos_pullback_recovery":
        return (
            terminal >= float(p["min_terminal_return"])
            and float(row["rsi_14"]) <= float(p["rsi_max"])
            and bool(row["close_above_ema50"])
        )

    if hypothesis.template == "kronos_breakout_pressure":
        return (
            upside >= float(p["min_max_upside"])
            and abs(float(row["donchian_high_dist_20"]))
            <= float(p["max_donchian_high_distance"])
            and float(row["adx_14"]) >= float(p["min_adx"])
        )

    if hypothesis.template == "kronos_asymmetric_path":
        return (
            terminal >= float(p["min_terminal_return"])
            and downside >= float(p["min_downside"])
        )

    raise ValueError(hypothesis.template)


def evaluate_kronos_hypothesis(
    hypothesis: KronosHypothesis,
    bars: pd.DataFrame,
    forecasts: pd.DataFrame,
) -> pd.DataFrame:
    work = bars.copy().sort_index()
    work.index = pd.to_datetime(work.index, utc=True)
    decision = _decision_features(work)

    fc = forecasts.copy()
    fc["decision_timestamp"] = pd.to_datetime(
        fc["decision_timestamp"], utc=True
    )
    fc = fc.set_index("decision_timestamp").sort_index()
    merged = fc.join(decision, how="inner").dropna(
        subset=[
            "kronos_terminal_return",
            "kronos_max_upside",
            "kronos_min_downside",
            "rsi_14",
            "adx_14",
            "donchian_high_dist_20",
        ]
    )

    rows: list[dict[str, Any]] = []
    index = work.index

    for timestamp, row in merged.iterrows():
        if not _signal(row, hypothesis):
            continue
        position = index.searchsorted(timestamp, side="right")
        pred_len = int(row["pred_len"])
        exit_position = position + pred_len - 1
        if position >= len(work) or exit_position >= len(work):
            continue

        entry_ts = index[position]
        exit_ts = index[exit_position]
        entry = float(work["open"].iloc[position])
        exit_price = float(work["close"].iloc[exit_position])
        if not (
            math.isfinite(entry)
            and math.isfinite(exit_price)
            and entry > 0.0
        ):
            continue

        rows.append(
            {
                "hypothesis_id": hypothesis.hypothesis_id,
                "strategy": hypothesis.template,
                "family": hypothesis.family,
                "decision_timestamp": timestamp,
                "entry_timestamp": entry_ts,
                "exit_timestamp": exit_ts,
                "entry_price": entry,
                "exit_price": exit_price,
                "gross_return": exit_price / entry - 1.0,
                "pred_len": pred_len,
                "kronos_terminal_return": float(
                    row["kronos_terminal_return"]
                ),
                "kronos_mean_return": float(
                    row["kronos_mean_return"]
                ),
                "kronos_max_upside": float(
                    row["kronos_max_upside"]
                ),
                "kronos_min_downside": float(
                    row["kronos_min_downside"]
                ),
                "execution_contract": "NEXT_OPEN_TO_HORIZON_CLOSE",
                "execution_authority": "NONE",
            }
        )

    return pd.DataFrame(rows)


def trade_metrics(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    cost_bps_per_side: float,
) -> dict[str, float | int]:
    if trades.empty:
        return {
            "trades": 0,
            "net_expectancy": math.nan,
            "net_expectancy_bps": math.nan,
            "profit_factor": math.nan,
            "total_return": 0.0,
        }

    timestamps = pd.to_datetime(
        trades["decision_timestamp"], utc=True
    )
    subset = trades.loc[
        timestamps.between(start, end, inclusive="both")
    ].copy()
    if subset.empty:
        return {
            "trades": 0,
            "net_expectancy": math.nan,
            "net_expectancy_bps": math.nan,
            "profit_factor": math.nan,
            "total_return": 0.0,
        }

    roundtrip_cost = 2.0 * float(cost_bps_per_side) / 10_000.0
    net = subset["gross_return"].astype(float) - roundtrip_cost
    wins = float(net.loc[net > 0.0].sum())
    losses = float(-net.loc[net < 0.0].sum())
    profit_factor = (
        wins / losses
        if losses > 0.0
        else math.inf if wins > 0.0 else math.nan
    )
    expectancy = float(net.mean())
    return {
        "trades": int(len(subset)),
        "net_expectancy": expectancy,
        "net_expectancy_bps": expectancy * 10_000.0,
        "profit_factor": profit_factor,
        "total_return": float((1.0 + net).prod() - 1.0),
    }
