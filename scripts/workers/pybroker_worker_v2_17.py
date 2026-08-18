from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from _common import artifact_ref, base_health, run_worker


CAPABILITIES = ("health", "replay_intents")


def _health(request: dict) -> dict:
    return base_health(
        request,
        distributions=("lib-pybroker",),
        imports=("pybroker",),
        capabilities=CAPABILITIES,
    )


def _normalize_order_fill_ledger(orders: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_symbol",
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "quantity",
    ]
    if orders is None or orders.empty:
        return pd.DataFrame(columns=columns)

    work = orders.copy()
    work.columns = [str(column).strip().lower() for column in work.columns]

    required = {"symbol", "date", "shares", "fill_price"}
    missing = sorted(required.difference(work.columns))
    if missing:
        raise ValueError(
            "PyBroker order report missing "
            f"{missing}; columns={list(work.columns)}"
        )

    work["date"] = pd.to_datetime(work["date"], utc=True, errors="coerce")
    work["shares"] = pd.to_numeric(work["shares"], errors="coerce")
    work["fill_price"] = pd.to_numeric(
        work["fill_price"], errors="coerce"
    )
    work = work.dropna(
        subset=["symbol", "date", "shares", "fill_price"]
    ).copy()

    sort_columns = ["date"]
    if "id" in work.columns:
        sort_columns.append("id")
    work = work.sort_values(sort_columns).reset_index(drop=True)

    def classify(row: dict) -> str:
        intent = str(row.get("intent") or "").strip().lower()
        side = str(row.get("type") or "").strip().lower()

        if intent:
            if intent == "buy_to_open":
                return "ENTRY"
            if intent == "sell_to_close":
                return "EXIT"
            raise ValueError(
                f"unsupported PyBroker long-only intent: {intent}"
            )

        if side == "buy":
            return "ENTRY"
        if side == "sell":
            return "EXIT"
        raise ValueError(
            f"cannot classify PyBroker order side: {side!r}"
        )

    open_by_symbol = {}
    rows = []

    for row in work.to_dict(orient="records"):
        symbol = str(row["symbol"]).upper()
        action = classify(row)
        quantity = float(row["shares"])

        if quantity <= 0 or abs(quantity - round(quantity)) > 1e-12:
            raise ValueError(
                f"{symbol}: non-integer PyBroker fill quantity {quantity}"
            )

        if action == "ENTRY":
            if symbol in open_by_symbol:
                raise ValueError(
                    f"{symbol}: overlapping PyBroker long fills"
                )
            open_by_symbol[symbol] = row
            continue

        if symbol not in open_by_symbol:
            raise ValueError(
                f"{symbol}: PyBroker exit without entry"
            )

        entry = open_by_symbol.pop(symbol)
        entry_quantity = float(entry["shares"])
        if abs(entry_quantity - quantity) > 1e-12:
            raise ValueError(
                f"{symbol}: PyBroker entry/exit quantity mismatch "
                f"{entry_quantity} != {quantity}"
            )

        rows.append(
            {
                "replay_symbol": symbol,
                "entry_time": entry["date"],
                "exit_time": row["date"],
                "entry_price": float(entry["fill_price"]),
                "exit_price": float(row["fill_price"]),
                "quantity": int(round(quantity)),
            }
        )

    if open_by_symbol:
        raise ValueError(
            "PyBroker open fills remain after replay: "
            + ",".join(sorted(open_by_symbol))
        )

    return pd.DataFrame(rows, columns=columns)

def _replay(request: dict, artifact_dir: Path) -> dict:
    import pybroker
    from pybroker import (
        PositionMode,
        PriceType,
        Strategy,
        StrategyConfig,
    )

    payload = dict(request.get("payload") or {})
    source = Path(str(payload["schedule_parquet"])).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    data = pd.read_parquet(source).copy()
    required = {
        "symbol",
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "scheduled_entry",
        "scheduled_exit",
    }
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"schedule missing {missing}")

    data["date"] = pd.to_datetime(
        data["date"], utc=True, errors="coerce"
    )
    data = data.dropna(subset=["date"]).copy()
    data["date"] = data["date"].dt.tz_localize(None)
    data = data.sort_values(["date", "symbol"]).reset_index(drop=True)

    try:
        pybroker.register_columns("scheduled_entry", "scheduled_exit")
    except Exception as exc:
        text = str(exc).lower()
        if "already" not in text and "registered" not in text:
            raise

    def execute(ctx):
        if ctx.bars < 1:
            return

        exit_signal = float(ctx.scheduled_exit[-1]) > 0.0
        entry_signal = float(ctx.scheduled_entry[-1]) > 0.0
        position = ctx.long_pos()

        if position:
            if exit_signal:
                ctx.sell_shares = position.shares
                ctx.sell_fill_price = PriceType.OPEN
            return

        if entry_signal:
            ctx.buy_shares = 1
            ctx.buy_fill_price = PriceType.OPEN

    symbols = sorted(data["symbol"].astype(str).unique().tolist())
    config = StrategyConfig(
        initial_cash=1_000_000.0,
        round_fill_price=False,
        round_test_result=False,
        position_mode=PositionMode.LONG_ONLY,
        max_long_positions=max(1, len(symbols)),
        max_short_positions=None,
        buy_delay=1,
        sell_delay=1,
        exit_on_last_bar=False,
        enable_fractional_shares=False,
    )

    strategy = Strategy(
        data,
        data["date"].min(),
        data["date"].max(),
        config,
    )
    strategy.add_execution(execute, symbols)
    result = strategy.backtest(calc_bootstrap=False)

    trades = result.trades.copy()
    trades_path = artifact_dir / "trades.csv"
    trades.to_csv(trades_path, index=False)

    orders = result.orders.copy()
    orders_path = artifact_dir / "orders.csv"
    orders.to_csv(orders_path, index=False)

    normalized = _normalize_order_fill_ledger(orders)

    normalized_path = artifact_dir / "normalized_ledger.parquet"
    normalized.to_parquet(normalized_path, index=False)

    summary = {
        "schema": "pybroker_intent_replay_v2_17",
        "engine": "pybroker",
        "engine_version": str(
            getattr(pybroker, "__version__", "unknown")
        ),
        "mode": "FULL_ENGINE_REPLAY",
        "trades": int(len(normalized)),
        "orders": int(len(result.orders)),
        "buy_delay": 1,
        "sell_delay": 1,
        "fill": "OPEN",
        "normalization_source": "ORDER_FILL_REPORT",
        "bootstrap_metrics": False,
        "round_test_result": False,
        "whole_shares_only": True,
        "fractional_shares_allowed": False,
        "money_control": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    summary_path = artifact_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "state": "OK",
        "data": summary,
        "artifacts": [
            artifact_ref(normalized_path, media_type="application/x-parquet"),
            artifact_ref(trades_path, media_type="text/csv"),
            artifact_ref(orders_path, media_type="text/csv"),
            artifact_ref(summary_path, media_type="application/json"),
        ],
    }


def handle(request: dict, artifact_dir: Path) -> dict:
    action = request["action"]
    if action == "health":
        return _health(request)
    if action == "replay_intents":
        return _replay(request, artifact_dir)
    raise ValueError(f"unsupported PyBroker v2.17 action: {action}")


if __name__ == "__main__":
    run_worker(handle)
