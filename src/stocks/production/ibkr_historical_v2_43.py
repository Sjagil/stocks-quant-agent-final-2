from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner


@dataclass(frozen=True)
class HistoricalBatchV243:
    frames: dict[str, pd.DataFrame]
    symbol_results: dict[str, dict[str, Any]]
    historical_data_calls: int
    broker_write_calls: int
    execution_authority: str = "NONE"


def _frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([], tz="UTC", name="timestamp"),
        )
    frame = pd.DataFrame(records)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError("IBKR_HISTORICAL_RECORD_COLUMNS_MISSING:" + ",".join(missing))
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    if frame["timestamp"].isna().any():
        raise ValueError("IBKR_HISTORICAL_RECORD_TIMESTAMP_INVALID")
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[["open", "high", "low", "close", "volume"]].isna().any().any():
        raise ValueError("IBKR_HISTORICAL_RECORD_NUMERIC_INVALID")
    frame = frame.set_index("timestamp").sort_index(kind="stable")
    frame.index = pd.DatetimeIndex(frame.index, tz="UTC", name="timestamp")
    if frame.index.duplicated().any():
        raise ValueError("IBKR_HISTORICAL_DUPLICATE_TIMESTAMPS")
    return frame[["open", "high", "low", "close", "volume"]]


def fetch_historical_batch_v243(
    project_root: str | Path,
    symbols: Iterable[str],
    *,
    duration: str = "5 D",
    bar_size: str = "30 mins",
    what_to_show: str = "TRADES",
    use_rth: bool = True,
    integration: str = "stocks_ibkr_reference",
    timeout_seconds: int = 180,
    maximum_symbols_per_request: int = 25,
) -> HistoricalBatchV243:
    root = Path(project_root).resolve()
    clean = []
    for raw in symbols:
        symbol = str(raw).strip().upper()
        if symbol and symbol not in clean:
            clean.append(symbol)
    if not clean:
        raise ValueError("IBKR_HISTORICAL_SYMBOLS_REQUIRED")
    chunk_size = int(maximum_symbols_per_request)
    if chunk_size < 1 or chunk_size > 25:
        raise ValueError("IBKR_HISTORICAL_CHUNK_SIZE_INVALID")

    registry = IntegrationRegistry.load(
        root / "config/integrations.yaml",
        project_root=root,
    )
    runner = IntegrationRunner(registry)

    frames: dict[str, pd.DataFrame] = {}
    symbol_results: dict[str, dict[str, Any]] = {}
    historical_data_calls = 0
    broker_write_calls = 0

    for offset in range(0, len(clean), chunk_size):
        chunk = clean[offset: offset + chunk_size]
        response = runner.run(
            integration,
            "historical_bars_read_only",
            {
                "symbols": chunk,
                "duration": str(duration),
                "bar_size": str(bar_size),
                "what_to_show": str(what_to_show).upper(),
                "use_rth": bool(use_rth),
                "keep_up_to_date": False,
            },
            timeout_seconds=int(timeout_seconds),
        )
        if not response.ok or not response.artifacts:
            raise RuntimeError(
                "IBKR_HISTORICAL_INTEGRATION_FAILED:"
                + str(response.error or getattr(response.state, "value", response.state))
            )

        artifact = Path(response.artifacts[0].path)
        data = json.loads(artifact.read_text(encoding="utf-8"))
        write_calls = int(data.get("broker_write_calls", 0))
        order_calls = int(data.get("order_calls", 0))
        if write_calls != 0 or order_calls != 0:
            raise RuntimeError("IBKR_HISTORICAL_READER_RECORDED_WRITE_CALLS")
        broker_write_calls += write_calls
        historical_data_calls += int(data.get("historical_data_calls", 0))

        records_by_symbol = data.get("records") or {}
        current_results = data.get("symbol_results") or {}
        for symbol in chunk:
            provider = dict(current_results.get(symbol) or {})
            symbol_results[symbol] = provider
            if str(provider.get("status")) != "OK":
                continue
            frames[symbol] = _frame(list(records_by_symbol.get(symbol) or []))

    return HistoricalBatchV243(
        frames=frames,
        symbol_results=symbol_results,
        historical_data_calls=historical_data_calls,
        broker_write_calls=broker_write_calls,
    )


__all__ = ["HistoricalBatchV243", "fetch_historical_batch_v243"]
