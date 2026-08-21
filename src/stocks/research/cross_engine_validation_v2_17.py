from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from stocks.research.pybroker_crosscheck import (
    assign_replay_lanes,
    build_schedule_frame,
)


LEDGER_COLUMNS = [
    "trade_id",
    "hypothesis_id",
    "strategy",
    "base_symbol",
    "replay_symbol",
    "entry_time",
    "exit_time",
    "entry_price",
    "exit_price",
    "quantity",
    "gross_return",
    "base_net_return",
    "stress_net_return",
    "execution_contract",
]


def utc(value: Any) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if result.tzinfo is None:
        return result.tz_localize("UTC")
    return result.tz_convert("UTC")


def _float(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite numeric value: {value}")
    return number


def _timestamp_column(frame: pd.DataFrame) -> str | None:
    for column in ("date", "timestamp", "timestamp_utc", "datetime"):
        if column in frame.columns:
            return column
    return None


def normalize_bar_frame(
    frame: pd.DataFrame,
    *,
    symbol: str,
) -> pd.DataFrame:
    work = frame.copy()
    if isinstance(work.index, pd.DatetimeIndex):
        work = work.reset_index()
        timestamp = str(work.columns[0])
    else:
        timestamp = _timestamp_column(work)
        if timestamp is None:
            raise ValueError(f"{symbol}: no timestamp column")

    work[timestamp] = pd.to_datetime(
        work[timestamp],
        utc=True,
        errors="coerce",
    )
    work = work.dropna(subset=[timestamp]).copy()

    required = ["open", "high", "low", "close", "volume"]
    missing = [column for column in required if column not in work]
    if missing:
        raise ValueError(f"{symbol}: missing OHLCV {missing}")

    for column in required:
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.dropna(subset=required).copy()
    work = (
        work.sort_values(timestamp)
        .drop_duplicates(timestamp, keep="last")
        .reset_index(drop=True)
    )

    if work.empty:
        raise ValueError(f"{symbol}: no valid bars")

    if (work["close"] <= 0).any():
        raise ValueError(f"{symbol}: non-positive close")
    if (
        work["high"]
        < work[["open", "close", "low"]].max(axis=1)
    ).any():
        raise ValueError(f"{symbol}: invalid high")
    if (
        work["low"]
        > work[["open", "close", "high"]].min(axis=1)
    ).any():
        raise ValueError(f"{symbol}: invalid low")
    if (work["volume"] < 0).any():
        raise ValueError(f"{symbol}: negative volume")

    work = work.rename(columns={timestamp: "date"})
    work["symbol"] = str(symbol).upper()
    return work[
        ["symbol", "date", "open", "high", "low", "close", "volume"]
    ]


def _lookup_open(
    frame: pd.DataFrame,
    timestamp: Any,
) -> float:
    target = utc(timestamp)
    dates = pd.to_datetime(frame["date"], utc=True)
    matched = frame.loc[dates == target]
    if len(matched) != 1:
        raise ValueError(
            f"execution timestamp {target} has {len(matched)} matching bars"
        )
    return _float(matched.iloc[0]["open"])


def _force_end_mask(trades: pd.DataFrame) -> pd.Series:
    mask = pd.Series(False, index=trades.index)
    for column in (
        "exit_reason",
        "reason",
        "trade_exit_reason",
        "forced_exit_reason",
    ):
        if column in trades:
            text = trades[column].astype(str).str.upper()
            mask |= text.str.contains(
                "FORCE|FORCED|END_OF_DATA|END_OF_SAMPLE",
                regex=True,
                na=False,
            )
    return mask


def build_canonical_replay_packet(
    frames: Mapping[str, pd.DataFrame],
    trades: pd.DataFrame,
    *,
    hypothesis_id: str,
    strategy: str,
    base_cost_bps_per_side: float,
    stress_cost_bps_per_side: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    required = {"symbol", "entry_time", "exit_time"}
    missing = required.difference(trades.columns)
    if missing:
        raise ValueError(f"trade frame missing {sorted(missing)}")

    work = trades.copy()
    work["symbol"] = work["symbol"].astype(str).str.upper()
    work["entry_time"] = pd.to_datetime(
        work["entry_time"], utc=True, errors="coerce"
    )
    work["exit_time"] = pd.to_datetime(
        work["exit_time"], utc=True, errors="coerce"
    )
    work = work.dropna(subset=["entry_time", "exit_time"]).copy()

    force_mask = _force_end_mask(work)
    excluded_forced = int(force_mask.sum())
    work = work.loc[~force_mask].copy()

    if work.empty:
        raise ValueError("zero non-forced trades for replay")
    if (work["exit_time"] <= work["entry_time"]).any():
        raise ValueError("non-positive trade duration")

    normalized_frames = {
        str(symbol).upper(): normalize_bar_frame(frame, symbol=str(symbol))
        for symbol, frame in frames.items()
    }

    unknown = sorted(set(work["symbol"]) - set(normalized_frames))
    if unknown:
        raise ValueError(f"missing frames for symbols {unknown}")

    laned, lane_audit = assign_replay_lanes(work)
    ledger_rows = []

    ordered_trades = (
        laned.sort_values(
            ["entry_time", "symbol", "_replay_lane"]
        )
        .to_dict(orient="records")
    )

    for number, row in enumerate(ordered_trades, start=1):
        base_symbol = str(row["symbol"]).upper()
        replay_symbol = str(row["_replay_symbol"]).upper()
        frame = normalized_frames[base_symbol]
        entry_price = _lookup_open(frame, row["entry_time"])
        exit_price = _lookup_open(frame, row["exit_time"])
        gross = exit_price / entry_price - 1.0
        base_cost = 2.0 * float(base_cost_bps_per_side) / 10_000.0
        stress_cost = 2.0 * float(stress_cost_bps_per_side) / 10_000.0

        ledger_rows.append(
            {
                "trade_id": (
                    f"{hypothesis_id}:{base_symbol}:"
                    f"{number:06d}"
                ),
                "hypothesis_id": str(hypothesis_id),
                "strategy": str(strategy),
                "base_symbol": base_symbol,
                "replay_symbol": replay_symbol,
                "entry_time": utc(row["entry_time"]),
                "exit_time": utc(row["exit_time"]),
                "entry_price": entry_price,
                "exit_price": exit_price,
                "quantity": 1,
                "gross_return": gross,
                "base_net_return": gross - base_cost,
                "stress_net_return": gross - stress_cost,
                "execution_contract": "NEXT_OPEN_REPLAY",
            }
        )

    ledger = pd.DataFrame(ledger_rows, columns=LEDGER_COLUMNS)

    # Reuse the battle-tested PyBroker scheduler to encode every canonical
    # entry/exit on the previous closed bar. It also duplicates rollover
    # lanes where an exit and new entry occur at the same timestamp.
    schedule, schedule_audit = build_schedule_frame(
        {
            symbol: frame.drop(columns=["symbol"])
            for symbol, frame in normalized_frames.items()
        },
        work,
    )

    expected_replay = Counter(
        (
            str(row.replay_symbol).upper(),
            utc(row.entry_time),
            utc(row.exit_time),
        )
        for row in ledger.itertuples(index=False)
    )

    schedule_replay_symbols = set(
        schedule["symbol"].astype(str).str.upper()
    )
    ledger_replay_symbols = set(ledger["replay_symbol"])
    if schedule_replay_symbols != ledger_replay_symbols:
        raise ValueError(
            "schedule/ledger replay symbol mismatch "
            f"{sorted(schedule_replay_symbols ^ ledger_replay_symbols)}"
        )

    packet_hash = canonical_packet_hash(ledger)
    bar_hash = canonical_bar_hash(schedule)

    audit = {
        "schema": "canonical_cross_engine_replay_packet_v2_17",
        "hypothesis_id": str(hypothesis_id),
        "strategy": str(strategy),
        "trades": int(len(ledger)),
        "symbols": int(ledger["base_symbol"].nunique()),
        "replay_symbols": int(ledger["replay_symbol"].nunique()),
        "excluded_forced_end_trades": excluded_forced,
        "rollover_count": int(lane_audit["rollover_count"]),
        "replay_lane_count": int(lane_audit["replay_lane_count"]),
        "scheduled_entries": int(schedule_audit["scheduled_entries"]),
        "scheduled_exits": int(schedule_audit["scheduled_exits"]),
        "packet_hash": packet_hash,
        "bar_hash": bar_hash,
        "expected_replay_keys": int(sum(expected_replay.values())),
        "cross_engine_reselection": False,
        "parameters_frozen": True,
        "whole_shares_only": True,
        "replay_quantity": 1,
        "execution_authority": "NONE",
    }
    return schedule, ledger, audit


def _normalized_json_row(row: Mapping[str, Any]) -> dict[str, Any]:
    result = {}
    for key in sorted(row):
        value = row[key]
        if isinstance(value, pd.Timestamp):
            value = utc(value).isoformat()
        elif isinstance(value, np.generic):
            value = value.item()
        elif isinstance(value, float):
            value = round(value, 12)
        result[str(key)] = value
    return result


def canonical_packet_hash(ledger: pd.DataFrame) -> str:
    if ledger.empty:
        return hashlib.sha256(b"[]").hexdigest()
    records = []
    for row in (
        ledger[LEDGER_COLUMNS]
        .sort_values(["entry_time", "replay_symbol", "trade_id"])
        .to_dict(orient="records")
    ):
        records.append(_normalized_json_row(row))
    text = json.dumps(
        records,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_bar_hash(schedule: pd.DataFrame) -> str:
    columns = [
        "symbol",
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "scheduled_entry",
        "scheduled_exit",
    ]
    missing = [column for column in columns if column not in schedule]
    if missing:
        raise ValueError(f"schedule missing {missing}")
    records = []
    for row in (
        schedule[columns]
        .sort_values(["date", "symbol"])
        .to_dict(orient="records")
    ):
        records.append(_normalized_json_row(row))
    text = json.dumps(
        records,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_external_ledger(
    frame: pd.DataFrame,
    *,
    hypothesis_id: str,
    strategy: str,
    base_cost_bps_per_side: float,
    stress_cost_bps_per_side: float,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=LEDGER_COLUMNS)

    aliases = {
        "replay_symbol": ("replay_symbol", "symbol"),
        "entry_time": ("entry_time", "entry_date", "entry_timestamp"),
        "exit_time": ("exit_time", "exit_date", "exit_timestamp"),
        "entry_price": ("entry_price", "entry"),
        "exit_price": ("exit_price", "exit"),
        "quantity": ("quantity", "shares", "qty"),
    }

    selected: dict[str, str] = {}
    for target, candidates in aliases.items():
        source = next(
            (column for column in candidates if column in frame.columns),
            None,
        )
        if source is None:
            raise ValueError(
                f"external ledger missing {target}; "
                f"tried {list(candidates)}"
            )
        selected[target] = source

    work = pd.DataFrame(
        {
            target: frame[source]
            for target, source in selected.items()
        }
    )
    work["replay_symbol"] = (
        work["replay_symbol"].astype(str).str.upper()
    )
    work["base_symbol"] = (
        work["replay_symbol"]
        .str.split("__PB", n=1)
        .str[0]
    )
    work["entry_time"] = pd.to_datetime(
        work["entry_time"], utc=True, errors="coerce"
    )
    work["exit_time"] = pd.to_datetime(
        work["exit_time"], utc=True, errors="coerce"
    )
    for column in ("entry_price", "exit_price", "quantity"):
        work[column] = pd.to_numeric(work[column], errors="coerce")

    work = work.dropna(
        subset=[
            "entry_time",
            "exit_time",
            "entry_price",
            "exit_price",
            "quantity",
        ]
    ).copy()
    work["quantity"] = work["quantity"].astype(float)
    if not np.allclose(work["quantity"], np.round(work["quantity"])):
        raise ValueError("fractional replay quantity observed")

    work = work.sort_values(
        ["entry_time", "replay_symbol", "exit_time"]
    ).reset_index(drop=True)
    work["trade_id"] = [
        f"{hypothesis_id}:{base}:EXT:{number:06d}"
        for number, base in enumerate(
            work["base_symbol"], start=1
        )
    ]
    work["hypothesis_id"] = str(hypothesis_id)
    work["strategy"] = str(strategy)
    work["gross_return"] = (
        work["exit_price"] / work["entry_price"] - 1.0
    )
    base_cost = 2.0 * float(base_cost_bps_per_side) / 10_000.0
    stress_cost = 2.0 * float(stress_cost_bps_per_side) / 10_000.0
    work["base_net_return"] = work["gross_return"] - base_cost
    work["stress_net_return"] = work["gross_return"] - stress_cost
    work["execution_contract"] = "NEXT_OPEN_REPLAY"
    return work[LEDGER_COLUMNS]


def compare_ledgers(
    expected: pd.DataFrame,
    observed: pd.DataFrame,
    *,
    max_fill_price_relative_error: float,
    max_trade_return_difference_bps: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    expected = expected.copy().sort_values(
        ["entry_time", "replay_symbol", "exit_time"]
    ).reset_index(drop=True)
    observed = observed.copy().sort_values(
        ["entry_time", "replay_symbol", "exit_time"]
    ).reset_index(drop=True)

    count_match = len(expected) == len(observed)
    rows = []
    max_price_error = 0.0
    max_return_error_bps = 0.0
    exact_timestamps = True
    exact_symbols = True
    quantity_integer = True

    limit = min(len(expected), len(observed))
    for index in range(limit):
        left = expected.iloc[index]
        right = observed.iloc[index]

        symbol_match = (
            str(left["replay_symbol"]).upper()
            == str(right["replay_symbol"]).upper()
        )
        entry_time_match = utc(left["entry_time"]) == utc(
            right["entry_time"]
        )
        exit_time_match = utc(left["exit_time"]) == utc(
            right["exit_time"]
        )

        entry_relative = abs(
            float(left["entry_price"]) - float(right["entry_price"])
        ) / max(abs(float(left["entry_price"])), 1e-12)
        exit_relative = abs(
            float(left["exit_price"]) - float(right["exit_price"])
        ) / max(abs(float(left["exit_price"])), 1e-12)
        price_error = max(entry_relative, exit_relative)

        return_error_bps = abs(
            float(left["gross_return"]) - float(right["gross_return"])
        ) * 10_000.0

        right_quantity = float(right["quantity"])
        integer_qty = bool(
            math.isfinite(right_quantity)
            and abs(right_quantity - round(right_quantity)) <= 1e-12
        )

        exact_symbols &= symbol_match
        exact_timestamps &= entry_time_match and exit_time_match
        quantity_integer &= integer_qty
        max_price_error = max(max_price_error, price_error)
        max_return_error_bps = max(
            max_return_error_bps, return_error_bps
        )

        rows.append(
            {
                "row": index,
                "expected_symbol": left["replay_symbol"],
                "observed_symbol": right["replay_symbol"],
                "symbol_match": symbol_match,
                "entry_time_match": entry_time_match,
                "exit_time_match": exit_time_match,
                "entry_price_relative_error": entry_relative,
                "exit_price_relative_error": exit_relative,
                "return_difference_bps": return_error_bps,
                "integer_quantity": integer_qty,
                "row_match": bool(
                    symbol_match
                    and entry_time_match
                    and exit_time_match
                    and price_error <= max_fill_price_relative_error
                    and return_error_bps
                    <= max_trade_return_difference_bps
                    and integer_qty
                ),
            }
        )

    matched = sum(bool(row["row_match"]) for row in rows)
    denominator = max(len(expected), len(observed), 1)
    ratio = matched / denominator

    parity = bool(
        count_match
        and exact_symbols
        and exact_timestamps
        and quantity_integer
        and max_price_error <= max_fill_price_relative_error
        and max_return_error_bps <= max_trade_return_difference_bps
        and ratio >= 0.999999
    )

    return (
        pd.DataFrame(rows),
        {
            "expected_trades": int(len(expected)),
            "observed_trades": int(len(observed)),
            "trade_count_match": bool(count_match),
            "exact_symbols": bool(exact_symbols),
            "exact_timestamps": bool(exact_timestamps),
            "integer_quantity": bool(quantity_integer),
            "maximum_fill_price_relative_error": float(max_price_error),
            "maximum_trade_return_difference_bps": float(
                max_return_error_bps
            ),
            "trade_match_ratio": float(ratio),
            "parity": parity,
            "execution_authority": "NONE",
        },
    )


def aggregate_engine_status(
    engine_rows: Iterable[Mapping[str, Any]],
    *,
    required_engines: Iterable[str],
    minimum_symbols: int,
    minimum_total_trades: int,
) -> dict[str, Any]:
    rows = [dict(row) for row in engine_rows]
    by_engine = {str(row["engine"]): row for row in rows}
    required = tuple(str(value) for value in required_engines)
    missing = [engine for engine in required if engine not in by_engine]
    non_validating = []
    engine_failures = {}

    blockers = []
    for engine in required:
        row = by_engine.get(engine)
        if row is None:
            blockers.append(f"{engine.upper()}_MISSING")
            non_validating.append(engine)
            engine_failures[engine] = ["MISSING"]
            continue

        reasons = []
        if str(row.get("mode")) != "FULL_ENGINE_REPLAY":
            blockers.append(f"{engine.upper()}_FULL_REPLAY_REQUIRED")
            reasons.append("FULL_ENGINE_REPLAY_REQUIRED")
        if not bool(row.get("parity")):
            blockers.append(f"{engine.upper()}_PARITY_FAILED")
            reasons.append("PARITY_FAILED")
        if row.get("error"):
            reasons.append(f"ERROR:{row.get('error')}")
        warnings = row.get("warnings")
        if warnings:
            reasons.append(f"WARNINGS:{warnings}")

        if reasons:
            non_validating.append(engine)
            engine_failures[engine] = reasons

    native = by_engine.get("native", {})
    if int(native.get("symbols", 0)) < int(minimum_symbols):
        blockers.append("MINIMUM_SYMBOL_BREADTH_NOT_MET")
    if int(native.get("trades", 0)) < int(minimum_total_trades):
        blockers.append("MINIMUM_TRADE_COUNT_NOT_MET")

    validated = not blockers and not missing
    return {
        "status": (
            "CROSS_ENGINE_VALIDATED"
            if validated
            else "CROSS_ENGINE_NOT_VALIDATED"
        ),
        "required_engines": list(required),
        "missing_engines": missing,
        "non_validating_engines": sorted(set(non_validating)),
        "engine_failures": engine_failures,
        "blockers": sorted(set(blockers)),
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
