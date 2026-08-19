from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pandas as pd

from _common import artifact_ref, base_health, run_worker
from nautilus_worker import handle as base_handle


CAPABILITIES = ("health", "catalog", "candle_validate", "replay_intents")
REPLAY_PRICE_PRECISION = 8
REPLAY_PRICE_INCREMENT = "0.00000001"


def _health(request: dict) -> dict:
    return base_health(
        request,
        distributions=("nautilus_trader",),
        imports=("nautilus_trader",),
        capabilities=CAPABILITIES,
    )


def _price_text(value: float) -> str:
    return f"{float(value):.{REPLAY_PRICE_PRECISION}f}"


def _execution_quote_frame(schedule: pd.DataFrame) -> pd.DataFrame:
    required = {
        "symbol",
        "date",
        "open",
        "scheduled_entry",
        "scheduled_exit",
    }
    missing = sorted(required.difference(schedule.columns))
    if missing:
        raise ValueError(f"schedule missing {missing}")

    frames = []
    for symbol, group in schedule.groupby("symbol", sort=True):
        work = group.copy()
        work["date"] = pd.to_datetime(
            work["date"],
            utc=True,
            errors="coerce",
        )
        work = (
            work.dropna(subset=["date", "open"])
            .sort_values("date")
            .drop_duplicates("date", keep="last")
            .reset_index(drop=True)
        )

        # build_schedule_frame places the frozen decision signal on the
        # previous closed bar. PyBroker uses buy/sell_delay=1. For Nautilus
        # execution parity we make that delay explicit and submit at the next
        # canonical row after a QuoteTick has established BBO=open.
        work["execute_entry"] = (
            pd.to_numeric(
                work["scheduled_entry"],
                errors="coerce",
            )
            .fillna(0)
            .shift(1)
            .fillna(0)
            .astype(int)
        )
        work["execute_exit"] = (
            pd.to_numeric(
                work["scheduled_exit"],
                errors="coerce",
            )
            .fillna(0)
            .shift(1)
            .fillna(0)
            .astype(int)
        )
        work["symbol"] = str(symbol).upper()
        frames.append(
            work[
                [
                    "symbol",
                    "date",
                    "open",
                    "execute_entry",
                    "execute_exit",
                ]
            ]
        )

    if not frames:
        raise ValueError("zero Nautilus execution quote rows")

    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["date", "symbol"])
        .reset_index(drop=True)
    )


def _normalize_fill_report(report: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_symbol",
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "quantity",
    ]
    if report is None or report.empty:
        return pd.DataFrame(columns=columns)

    work = report.copy()
    work.columns = [
        str(column).strip().lower()
        for column in work.columns
    ]

    timestamp = next(
        (
            column
            for column in (
                "ts_event",
                "timestamp",
                "event_timestamp",
                "last_ts",
                "ts_last",
                "ts_init",
            )
            if column in work
        ),
        None,
    )
    side = next(
        (
            column
            for column in (
                "order_side",
                "side",
            )
            if column in work
        ),
        None,
    )
    price = next(
        (
            column
            for column in (
                "last_px",
                "avg_px",
                "price",
                "fill_price",
            )
            if column in work
        ),
        None,
    )
    quantity = next(
        (
            column
            for column in (
                "last_qty",
                "filled_qty",
                "quantity",
                "qty",
            )
            if column in work
        ),
        None,
    )
    instrument = next(
        (
            column
            for column in (
                "instrument_id",
                "instrument",
                "symbol",
            )
            if column in work
        ),
        None,
    )

    if None in (timestamp, side, price, quantity, instrument):
        raise ValueError(
            "Nautilus fill report cannot be normalized; "
            f"columns={list(work.columns)}"
        )

    ts_raw = work[timestamp]
    if pd.api.types.is_numeric_dtype(ts_raw):
        parsed_ts = pd.to_datetime(
            ts_raw,
            utc=True,
            unit="ns",
            errors="coerce",
        )
    else:
        parsed_ts = pd.to_datetime(
            ts_raw,
            utc=True,
            errors="coerce",
        )

    fills = pd.DataFrame(
        {
            "timestamp": parsed_ts,
            "side": work[side].astype(str).str.upper(),
            "price": pd.to_numeric(
                work[price],
                errors="coerce",
            ),
            "quantity": pd.to_numeric(
                work[quantity],
                errors="coerce",
            ),
            "instrument": work[instrument].astype(str),
        }
    ).dropna()

    fills = fills.loc[fills["quantity"] > 0].copy()

    rows = []
    for instrument_id, group in fills.groupby(
        "instrument",
        sort=True,
    ):
        open_fill = None
        for row in group.sort_values(
            "timestamp"
        ).itertuples(index=False):
            if "BUY" in row.side:
                if open_fill is not None:
                    raise ValueError(
                        f"{instrument_id}: overlapping Nautilus long fills"
                    )
                open_fill = row
                continue

            if "SELL" not in row.side:
                continue

            if open_fill is None:
                raise ValueError(
                    f"{instrument_id}: Nautilus sell without entry"
                )

            entry_qty = float(open_fill.quantity)
            exit_qty = float(row.quantity)
            if abs(entry_qty - exit_qty) > 1e-12:
                raise ValueError(
                    f"{instrument_id}: entry/exit quantity mismatch "
                    f"{entry_qty} != {exit_qty}"
                )
            if (
                entry_qty <= 0
                or abs(entry_qty - round(entry_qty)) > 1e-12
            ):
                raise ValueError(
                    f"{instrument_id}: fractional Nautilus quantity "
                    f"{entry_qty}"
                )

            rows.append(
                {
                    "replay_symbol":
                        str(instrument_id).split(".")[0].upper(),
                    "entry_time": open_fill.timestamp,
                    "exit_time": row.timestamp,
                    "entry_price": float(open_fill.price),
                    "exit_price": float(row.price),
                    "quantity": int(round(entry_qty)),
                }
            )
            open_fill = None

        if open_fill is not None:
            raise ValueError(
                f"{instrument_id}: open position remains after replay"
            )

    return pd.DataFrame(rows, columns=columns)


def _replay(request: dict, artifact_dir: Path) -> dict:
    from nautilus_trader.backtest.config import BacktestEngineConfig
    from nautilus_trader.backtest.engine import BacktestEngine
    from nautilus_trader.config import LoggingConfig, RiskEngineConfig
    try:
        from nautilus_trader.config import StrategyConfig
    except ImportError:
        from nautilus_trader.trading.config import StrategyConfig

    from nautilus_trader.model.currencies import USD
    from nautilus_trader.model.data import QuoteTick
    from nautilus_trader.model.enums import (
        AccountType,
        OmsType,
        OrderSide,
        TimeInForce,
    )
    from nautilus_trader.model.identifiers import (
        InstrumentId,
        Symbol,
        TraderId,
        Venue,
    )
    from nautilus_trader.model.instruments import Equity
    from nautilus_trader.model.objects import (
        Money,
        Price,
        Quantity,
    )
    from nautilus_trader.trading.strategy import Strategy

    payload = dict(request.get("payload") or {})
    source = Path(
        str(payload["schedule_parquet"])
    ).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    schedule = pd.read_parquet(source)
    execution = _execution_quote_frame(schedule)

    class ReplayConfig(StrategyConfig, frozen=True):
        instrument_id: object
        entry_ns: tuple[int, ...]
        exit_ns: tuple[int, ...]

    class ReplayStrategy(Strategy):
        def __init__(self, config):
            super().__init__(config)
            self.instrument = None

        def on_start(self):
            self.instrument = self.cache.instrument(
                self.config.instrument_id
            )
            if self.instrument is None:
                self.log.error("instrument unavailable")
                self.stop()
                return
            self.subscribe_quote_ticks(
                self.config.instrument_id
            )

        def _market(self, side):
            order = self.order_factory.market(
                instrument_id=self.config.instrument_id,
                order_side=side,
                quantity=self.instrument.make_qty(1),
                time_in_force=TimeInForce.GTC,
            )
            self.submit_order(order)

        def on_quote_tick(self, tick):
            ts = int(tick.ts_event)
            if ts in self.config.exit_ns:
                self._market(OrderSide.SELL)
            elif ts in self.config.entry_ns:
                self._market(OrderSide.BUY)

    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id=TraderId("XENGINE-001"),
            logging=LoggingConfig(log_level="ERROR"),
            risk_engine=RiskEngineConfig(bypass=True),
        )
    )

    venue = Venue("SIM")
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        base_currency=USD,
        starting_balances=[
            Money(1_000_000.0, USD)
        ],
    )

    ticks = []
    instrument_rows = []
    strategy_count = 0

    for replay_symbol, group in execution.groupby(
        "symbol",
        sort=True,
    ):
        replay_symbol = str(replay_symbol).upper()
        symbol = Symbol(replay_symbol)
        instrument_id = InstrumentId(
            symbol=symbol,
            venue=venue,
        )

        instrument = Equity(
            instrument_id=instrument_id,
            raw_symbol=symbol,
            currency=USD,
            price_precision=REPLAY_PRICE_PRECISION,
            price_increment=Price.from_str(
                REPLAY_PRICE_INCREMENT
            ),
            lot_size=Quantity.from_int(1),
            margin_init=Decimal("0"),
            margin_maint=Decimal("0"),
            ts_event=0,
            ts_init=0,
        )
        engine.add_instrument(instrument)

        entry_ns = []
        exit_ns = []

        for row in group.sort_values(
            "date"
        ).itertuples(index=False):
            ts_ns = int(pd.Timestamp(row.date).value)
            px = Price.from_str(
                _price_text(row.open)
            )
            # Zero spread is intentional for pure execution-semantic
            # validation: no synthetic market friction is introduced here.
            ticks.append(
                QuoteTick(
                    instrument_id=instrument.id,
                    bid_price=px,
                    ask_price=px,
                    bid_size=Quantity.from_int(1_000_000),
                    ask_size=Quantity.from_int(1_000_000),
                    ts_event=ts_ns,
                    ts_init=ts_ns,
                )
            )

            if int(row.execute_entry) == 1:
                entry_ns.append(ts_ns)
            if int(row.execute_exit) == 1:
                exit_ns.append(ts_ns)

        instrument_rows.append(
            {
                "replay_symbol": replay_symbol,
                "instrument_id": str(instrument.id),
                "entry_intents": len(entry_ns),
                "exit_intents": len(exit_ns),
                "price_precision":
                    int(instrument.price_precision),
                "size_precision":
                    int(instrument.size_precision),
            }
        )

        engine.add_strategy(
            ReplayStrategy(
                ReplayConfig(
                    instrument_id=instrument.id,
                    entry_ns=tuple(entry_ns),
                    exit_ns=tuple(exit_ns),
                )
            )
        )
        strategy_count += 1

    ticks.sort(
        key=lambda tick: (
            int(tick.ts_event),
            str(tick.instrument_id),
        )
    )
    engine.add_data(ticks)

    intents_path = artifact_dir / "execution_intents.parquet"
    execution.to_parquet(
        intents_path,
        index=False,
    )
    instruments_path = (
        artifact_dir / "replay_instruments.csv"
    )
    pd.DataFrame(instrument_rows).to_csv(
        instruments_path,
        index=False,
    )

    engine.run()

    fills = engine.trader.generate_order_fills_report()
    fills_path = artifact_dir / "fills.csv"
    fills.to_csv(fills_path, index=False)

    normalized = _normalize_fill_report(fills)
    normalized_path = (
        artifact_dir / "normalized_ledger.parquet"
    )
    normalized.to_parquet(
        normalized_path,
        index=False,
    )

    summary = {
        "schema": "nautilus_intent_replay_v2_17_7",
        "engine": "nautilus",
        "mode": "FULL_ENGINE_REPLAY",
        "feed": "SYNTHETIC_ZERO_SPREAD_QUOTE_TICK_AT_CANONICAL_OPEN",
        "execution_semantics":
            "SCHEDULE_DERIVED_EXECUTION_INTENT_AT_OPEN",
        "signals_shifted_rows": 1,
        "quote_ticks": int(len(ticks)),
        "strategies": int(strategy_count),
        "fills": int(len(fills)),
        "trades": int(len(normalized)),
        "order_type": "MARKET",
        "time_in_force": "GTC",
        "replay_price_precision":
            REPLAY_PRICE_PRECISION,
        "whole_shares_only": True,
        "fractional_shares_allowed": False,
        "cross_engine_reselection": False,
        "money_control": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }

    summary_path = artifact_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    engine.dispose()

    return {
        "state": "OK",
        "data": summary,
        "artifacts": [
            artifact_ref(
                normalized_path,
                media_type="application/x-parquet",
            ),
            artifact_ref(
                intents_path,
                media_type="application/x-parquet",
            ),
            artifact_ref(
                fills_path,
                media_type="text/csv",
            ),
            artifact_ref(
                instruments_path,
                media_type="text/csv",
            ),
            artifact_ref(
                summary_path,
                media_type="application/json",
            ),
        ],
    }


def handle(request: dict, artifact_dir: Path) -> dict:
    action = request["action"]
    if action == "health":
        return _health(request)
    if action in {
        "catalog",
        "candle_validate",
    }:
        return base_handle(
            request,
            artifact_dir,
        )
    if action == "replay_intents":
        return _replay(
            request,
            artifact_dir,
        )
    raise ValueError(
        f"unsupported Nautilus v2.17.7 action: {action}"
    )


if __name__ == "__main__":
    run_worker(handle)
