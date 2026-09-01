from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner
from stocks.providers.env import load_project_env


@dataclass(frozen=True)
class HistoricalBatchV2431:
    frames: dict[str, pd.DataFrame]
    symbol_results: dict[str, dict[str, Any]]
    historical_data_calls: int
    broker_write_calls: int
    order_calls: int
    chunks: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    execution_authority: str = "NONE"

    @property
    def failed_symbols(self) -> tuple[str, ...]:
        return tuple(
            symbol
            for symbol, row in sorted(self.symbol_results.items())
            if str(row.get("status")) != "OK"
        )


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


def _run_chunk(
    runner: IntegrationRunner,
    *,
    integration: str,
    symbols: list[str],
    duration: str,
    bar_size: str,
    what_to_show: str,
    use_rth: bool,
    timeout_seconds: int,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    started = time.monotonic()
    try:
        response = runner.run(
            integration,
            "historical_bars_read_only",
            {
                "symbols": symbols,
                "duration": str(duration),
                "bar_size": str(bar_size),
                "what_to_show": str(what_to_show).upper(),
                "use_rth": bool(use_rth),
                "keep_up_to_date": False,
            },
            timeout_seconds=int(timeout_seconds),
        )
        elapsed = time.monotonic() - started
        diag = {
            "symbols": list(symbols),
            "elapsed_seconds": round(elapsed, 4),
            "response_ok": bool(response.ok),
            "response_state": str(getattr(getattr(response, "state", None), "value", getattr(response, "state", "UNKNOWN"))),
            "error": str(response.error or ""),
            "artifact_count": len(response.artifacts or []),
        }
        if not response.ok or not response.artifacts:
            return None, diag
        artifact = Path(response.artifacts[0].path)
        data = json.loads(artifact.read_text(encoding="utf-8"))
        diag["artifact"] = str(artifact)
        diag["historical_data_calls"] = int(data.get("historical_data_calls", 0))
        diag["historical_cancel_calls"] = int(data.get("historical_cancel_calls", 0))
        return data, diag
    except Exception as exc:
        return None, {
            "symbols": list(symbols),
            "elapsed_seconds": round(time.monotonic() - started, 4),
            "response_ok": False,
            "response_state": "EXCEPTION",
            "error": f"{type(exc).__name__}:{exc}",
            "artifact_count": 0,
        }


def fetch_historical_batch_v2431(
    project_root: str | Path,
    symbols: Iterable[str],
    *,
    duration: str = "5 D",
    bar_size: str = "30 mins",
    what_to_show: str = "TRADES",
    use_rth: bool = True,
    integration: str = "stocks_ibkr_reference",
    chunk_timeout_seconds: int = 90,
    maximum_symbols_per_request: int = 2,
    retry_failed_symbols: bool = True,
    individual_retry_timeout_seconds: int = 55,
) -> HistoricalBatchV2431:
    """Fetch read-only IBKR bars through the imported Stocks reference repo.

    The Stocks worker serves symbols sequentially. A 12-symbol request can therefore
    exceed the outer integration timeout even when every individual IBKR request is
    behaving as configured. v2.43.1 deliberately uses small chunks and retries only
    failed symbols individually. One bad symbol can never erase successful peers.
    """
    root = Path(project_root).resolve()
    load_project_env(root)

    clean: list[str] = []
    for raw in symbols:
        symbol = str(raw).strip().upper()
        if symbol and symbol not in clean:
            clean.append(symbol)
    if not clean:
        raise ValueError("IBKR_HISTORICAL_SYMBOLS_REQUIRED")

    chunk_size = int(maximum_symbols_per_request)
    if chunk_size < 1 or chunk_size > 4:
        raise ValueError("IBKR_HISTORICAL_CHUNK_SIZE_MUST_BE_1_TO_4")

    registry = IntegrationRegistry.load(
        root / "config/integrations.yaml",
        project_root=root,
    )
    runner = IntegrationRunner(registry)

    frames: dict[str, pd.DataFrame] = {}
    symbol_results: dict[str, dict[str, Any]] = {
        symbol: {"status": "PENDING", "attempts": 0} for symbol in clean
    }
    chunks: list[dict[str, Any]] = []
    historical_data_calls = 0
    broker_write_calls = 0
    order_calls = 0

    def consume(targets: list[str], timeout_seconds: int, attempt_kind: str) -> None:
        nonlocal historical_data_calls, broker_write_calls, order_calls
        data, diag = _run_chunk(
            runner,
            integration=integration,
            symbols=targets,
            duration=duration,
            bar_size=bar_size,
            what_to_show=what_to_show,
            use_rth=use_rth,
            timeout_seconds=timeout_seconds,
        )
        diag["attempt_kind"] = attempt_kind
        chunks.append(diag)
        for symbol in targets:
            symbol_results[symbol]["attempts"] = int(symbol_results[symbol].get("attempts", 0)) + 1
        if data is None:
            for symbol in targets:
                symbol_results[symbol].update({
                    "status": "ERROR",
                    "reason": "INTEGRATION_CHUNK_FAILED",
                    "integration_error": diag.get("error"),
                })
            return

        writes = int(data.get("broker_write_calls", 0))
        orders = int(data.get("order_calls", 0))
        if writes != 0 or orders != 0:
            raise RuntimeError("IBKR_HISTORICAL_READER_RECORDED_WRITE_CALLS")
        broker_write_calls += writes
        order_calls += orders
        historical_data_calls += int(data.get("historical_data_calls", 0))

        records_by_symbol = data.get("records") or {}
        current_results = data.get("symbol_results") or {}
        for symbol in targets:
            provider = dict(current_results.get(symbol) or {})
            provider["attempts"] = symbol_results[symbol]["attempts"]
            if str(provider.get("status")) == "OK":
                try:
                    frame = _frame(list(records_by_symbol.get(symbol) or []))
                    if frame.empty:
                        raise ValueError("IBKR_HISTORICAL_EMPTY_FRAME")
                    frames[symbol] = frame
                    provider["rows"] = len(frame)
                    provider["first_timestamp"] = frame.index.min().isoformat()
                    provider["last_timestamp"] = frame.index.max().isoformat()
                    symbol_results[symbol] = provider
                except Exception as exc:
                    symbol_results[symbol] = {
                        **provider,
                        "status": "ERROR",
                        "reason": f"{type(exc).__name__}:{exc}",
                    }
            else:
                symbol_results[symbol] = {
                    **provider,
                    "status": "ERROR",
                    "reason": provider.get("reason") or "IBKR_SYMBOL_FAILED",
                }

    for offset in range(0, len(clean), chunk_size):
        consume(
            clean[offset : offset + chunk_size],
            int(chunk_timeout_seconds),
            "PRIMARY_CHUNK",
        )

    if retry_failed_symbols:
        failed = [
            symbol for symbol in clean
            if str(symbol_results[symbol].get("status")) != "OK"
        ]
        for symbol in failed:
            consume([symbol], int(individual_retry_timeout_seconds), "INDIVIDUAL_RETRY")

    return HistoricalBatchV2431(
        frames=frames,
        symbol_results=symbol_results,
        historical_data_calls=historical_data_calls,
        broker_write_calls=broker_write_calls,
        order_calls=order_calls,
        chunks=tuple(chunks),
    )


# Backwards-compatible name so existing v2.43 call sites can be patched with
# only an import change, while diagnostics and isolation semantics come from 43.1.
fetch_historical_batch_v243 = fetch_historical_batch_v2431
HistoricalBatchV243 = HistoricalBatchV2431

__all__ = [
    "HistoricalBatchV2431",
    "HistoricalBatchV243",
    "fetch_historical_batch_v2431",
    "fetch_historical_batch_v243",
]
