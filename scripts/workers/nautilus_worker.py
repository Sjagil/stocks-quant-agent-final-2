from __future__ import annotations

import json
import pkgutil
from pathlib import Path

from _common import (
    artifact_ref,
    base_health,
    import_probe,
    repo_catalog,
    require_path,
    run_worker,
)

CAPABILITIES = ("health", "catalog", "candle_validate")


def _health(request: dict) -> dict:
    return base_health(
        request,
        distributions=("nautilus_trader",),
        imports=("nautilus_trader",),
        capabilities=CAPABILITIES,
    )


def _catalog(request: dict) -> dict:
    repo = (request.get("context") or {}).get("repo_path")
    probe = import_probe("nautilus_trader")
    modules: list[str] = []
    warnings: list[str] = []
    state = "OK"

    if probe["ok"]:
        import nautilus_trader

        modules = sorted(
            module.name
            for module in pkgutil.iter_modules(nautilus_trader.__path__)
        )
    else:
        state = "DEGRADED"
        warnings.append(
            "NautilusTrader runtime package is unavailable; "
            "reference-repository catalog is still reported"
        )

    return {
        "state": state,
        "data": {
            "runtime": probe,
            "top_level_modules": modules,
            "repo_catalog": repo_catalog(
                repo,
                ("*fill*.py", "*execution*.py", "*backtest*.py", "*risk*.py"),
            ),
            "purpose": (
                "Independent candle/event/execution simulation challenger; "
                "no live authority."
            ),
        },
        "warnings": warnings,
    }


def _text_number(value: float, decimals: int = 8) -> str:
    text = f"{float(value):.{decimals}f}".rstrip("0").rstrip(".")
    return text or "0"


def _candle_validate(
    request: dict,
    artifact_dir: Path,
) -> dict:
    import pandas as pd

    from nautilus_trader.model.data import Bar, BarType
    from nautilus_trader.model.objects import Price, Quantity

    payload = dict(request.get("payload") or {})
    source = require_path(payload, "input_parquet")
    symbol = str(payload.get("symbol") or "").strip().upper()
    timeframe = str(payload.get("timeframe") or "").strip()
    sample_rows = int(payload.get("sample_rows", 512))

    if not symbol:
        raise ValueError("payload.symbol is required")

    timeframe_spec = {
        "5m": "5-MINUTE",
        "15m": "15-MINUTE",
        "1h": "1-HOUR",
        "2h": "2-HOUR",
        "4h": "4-HOUR",
        "1d": "1-DAY",
    }.get(timeframe)

    if timeframe_spec is None:
        raise ValueError(f"unsupported Nautilus candle timeframe: {timeframe}")

    frame = pd.read_parquet(source)

    if not isinstance(frame.index, pd.DatetimeIndex):
        timestamp_column = next(
            (
                column
                for column in ("timestamp", "timestamp_utc", "datetime", "date")
                if column in frame.columns
            ),
            None,
        )
        if timestamp_column is None:
            raise ValueError("candle parquet has no datetime index/column")
        frame[timestamp_column] = pd.to_datetime(
            frame[timestamp_column],
            utc=True,
            errors="coerce",
        )
        frame = frame.dropna(subset=[timestamp_column]).set_index(timestamp_column)
    else:
        frame.index = pd.to_datetime(frame.index, utc=True)

    frame = frame.sort_index()
    required = ["open", "high", "low", "close", "volume"]
    missing = [column for column in required if column not in frame]
    if missing:
        raise ValueError(f"missing OHLCV columns: {missing}")
    if frame.index.has_duplicates:
        raise ValueError("duplicate candle timestamps")
    if not frame.index.is_monotonic_increasing:
        raise ValueError("candle timestamps not monotonic")

    frame = frame.tail(max(1, sample_rows)).copy()

    bar_type = BarType.from_str(
        f"{symbol}.SIM-{timeframe_spec}-LAST-EXTERNAL"
    )

    bars = []
    prior_ts = -1

    for timestamp, row in frame.iterrows():
        values = {
            key: float(row[key])
            for key in required
        }

        if values["high"] < max(values["open"], values["close"], values["low"]):
            raise ValueError(f"{timestamp}: invalid high")
        if values["low"] > min(values["open"], values["close"], values["high"]):
            raise ValueError(f"{timestamp}: invalid low")
        if values["volume"] < 0:
            raise ValueError(f"{timestamp}: negative volume")

        ts_ns = int(pd.Timestamp(timestamp).value)
        if ts_ns <= prior_ts:
            raise ValueError("non-increasing Nautilus event timestamps")
        prior_ts = ts_ns

        bars.append(
            Bar(
                bar_type=bar_type,
                open=Price.from_str(_text_number(values["open"])),
                high=Price.from_str(_text_number(values["high"])),
                low=Price.from_str(_text_number(values["low"])),
                close=Price.from_str(_text_number(values["close"])),
                volume=Quantity.from_str(
                    _text_number(values["volume"], decimals=4)
                ),
                ts_event=ts_ns,
                ts_init=ts_ns,
            )
        )

    if not bars:
        raise ValueError("no candles available for Nautilus validation")

    summary = {
        "schema": "nautilus_candle_crosscheck_v2_12",
        "symbol": symbol,
        "timeframe": timeframe,
        "bar_type": str(bar_type),
        "bars": len(bars),
        "first_ts_event": int(bars[0].ts_event),
        "last_ts_event": int(bars[-1].ts_event),
        "monotonic": True,
        "ohlcv_valid": True,
        "money_control": False,
        "execution_authority": "NONE",
    }

    output = artifact_dir / "candle_validation.json"
    output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "state": "OK",
        "data": summary,
        "artifacts": [
            artifact_ref(
                output,
                media_type="application/json",
                rows=len(bars),
            )
        ],
    }


def handle(request: dict, artifact_dir: Path) -> dict:
    action = request["action"]

    if action == "health":
        return _health(request)
    if action == "catalog":
        return _catalog(request)
    if action == "candle_validate":
        return _candle_validate(request, artifact_dir)

    raise ValueError(f"unsupported nautilus action: {action}")


if __name__ == "__main__":
    run_worker(handle)
