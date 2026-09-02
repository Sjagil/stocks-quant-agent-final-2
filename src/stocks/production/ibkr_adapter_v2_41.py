from __future__ import annotations

import math
import os
from datetime import datetime, timezone
from typing import Any

from .contracts_v2_41 import BrokerSnapshot, QuoteSnapshot


def _finite(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and x > 0 else None


class IBKRBrokerV241:
    def __init__(self, cfg: dict[str, Any], *, readonly: bool):
        try:
            from ib_async import IB, Stock, Forex, LimitOrder, StopOrder  # noqa
        except Exception as exc:
            raise ImportError("ib_async==2.1.0 is required for production broker access") from exc

        self.cfg = cfg
        self.readonly = bool(readonly)
        self.IB = IB
        self.Stock = Stock
        self.Forex = Forex
        self.LimitOrder = LimitOrder
        self.StopOrder = StopOrder
        self.ib = IB()
        self.write_calls = 0
        self._connect()

    def _connect(self) -> None:
        b = self.cfg["broker"]
        environment = os.environ.get(b["environment_env"], "PAPER").strip().upper()
        if environment not in {"PAPER", "LIVE"}:
            raise ValueError("IBKR_ENVIRONMENT must be PAPER or LIVE")

        host = os.environ.get(b["host_env"], b.get("default_host", "127.0.0.1"))
        default_port = b["default_live_port"] if environment == "LIVE" else b["default_paper_port"]
        port = int(os.environ.get(b["port_env"], default_port))
        client_id = int(os.environ.get(b["client_id_env"], b.get("default_client_id", 41)))
        account = os.environ.get(b["account_env"], "").strip()

        self.environment = environment
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib.connect(
            host,
            port,
            clientId=client_id,
            timeout=float(self.cfg["runtime"].get("broker_snapshot_timeout_seconds", 8)),
            readonly=self.readonly,
            account=account,
            raiseSyncErrors=True,
        )
        accounts = list(self.ib.managedAccounts())
        if not accounts:
            raise RuntimeError("IBKR returned no managed accounts")
        if account:
            if account not in accounts:
                raise RuntimeError(f"configured IBKR_ACCOUNT {account} not in managed accounts")
            self.account = account
        elif len(accounts) == 1:
            self.account = accounts[0]
        else:
            raise RuntimeError("multiple IBKR accounts available; set IBKR_ACCOUNT explicitly")

    def close(self) -> None:
        if self.ib.isConnected():
            self.ib.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def _account_number(self, values: list[Any], tag: str, *, currency: str | None = None, default: float = 0.0) -> float:
        candidates = [v for v in values if str(getattr(v, "tag", "")) == tag]
        if currency:
            exact = [v for v in candidates if str(getattr(v, "currency", "")).upper() == currency.upper()]
            if exact:
                candidates = exact
        for v in candidates:
            try:
                x = float(v.value)
                if math.isfinite(x):
                    return x
            except Exception:
                pass
        return float(default)

    def _base_currency(self, values: list[Any]) -> str:
        net = [v for v in values if str(getattr(v, "tag", "")) == "NetLiquidation"]
        reported = next((str(getattr(v, "currency", "")).strip().upper() for v in net if str(getattr(v, "currency", "")).strip()), "")
        configured = os.environ.get("IBKR_BASE_CURRENCY", "").strip().upper()
        if configured and reported and configured != reported:
            raise RuntimeError(f"IBKR_BASE_CURRENCY mismatch: configured={configured} broker={reported}")
        base = configured or reported
        if not base:
            raise RuntimeError("unable to determine IBKR account base currency; set IBKR_BASE_CURRENCY")
        return base
    def snapshot(self) -> BrokerSnapshot:
        positions: dict[str, float] = {}
        for p in self.ib.positions(self.account):
            contract = p.contract
            if str(getattr(contract, "secType", "")).upper() != "STK":
                continue
            symbol = str(getattr(contract, "symbol", "")).upper()
            if symbol:
                positions[symbol] = positions.get(symbol, 0.0) + float(p.position)

        open_orders = []
        for trade in self.ib.openTrades():
            order = trade.order
            contract = trade.contract
            open_orders.append({
                "order_id": int(getattr(order, "orderId", 0)),
                "perm_id": int(getattr(order, "permId", 0)),
                "parent_id": int(getattr(order, "parentId", 0)),
                "order_ref": str(getattr(order, "orderRef", "") or ""),
                "action": str(getattr(order, "action", "")),
                "quantity": float(getattr(order, "totalQuantity", 0.0)),
                "order_type": str(getattr(order, "orderType", "")),
                "status": str(getattr(trade.orderStatus, "status", "")),
                "symbol": str(getattr(contract, "symbol", "")).upper(),
            })

        fills = []
        for f in self.ib.fills():
            ex = f.execution
            fills.append({
                "exec_id": str(ex.execId),
                "broker_order_id": int(ex.orderId),
                "order_ref": str(getattr(ex, "orderRef", "") or ""),
                "symbol": str(getattr(f.contract, "symbol", "")).upper(),
                "side": str(ex.side),
                "shares": float(ex.shares),
                "price": float(ex.price),
                "filled_at": getattr(ex.time, "isoformat", lambda: str(ex.time))(),
            })

        values = list(self.ib.accountSummary(self.account))
        base_currency = self._base_currency(values)
        current = self.ib.reqCurrentTime()
        return BrokerSnapshot(
            connected=bool(self.ib.isConnected()),
            account=self.account,
            environment=self.environment,
            net_liquidation=self._account_number(values, "NetLiquidation", currency=base_currency),
            available_funds=self._account_number(values, "AvailableFunds", currency=base_currency),
            total_cash=self._account_number(values, "TotalCashValue", currency=base_currency),
            base_currency=base_currency,
            positions=positions,
            open_orders=tuple(open_orders),
            fills=tuple(fills),
            current_time=current.astimezone(timezone.utc).isoformat() if hasattr(current, "astimezone") else str(current),
            broker_write_calls=self.write_calls,
        )

    def stock_contract(self, symbol: str):
        b = self.cfg["broker"]
        contract = self.Stock(symbol.upper(), b.get("exchange", "SMART"), b.get("currency", "USD"))
        qualified = self.ib.qualifyContracts(contract)
        if len(qualified) != 1:
            raise RuntimeError(f"unable to uniquely qualify stock contract {symbol}")
        return qualified[0]

    def historical_bars(
        self,
        symbol: str,
        *,
        duration: str = "5 D",
        bar_size: str = "1 hour",
        what_to_show: str = "TRADES",
        use_rth: bool = True,
    ):
        """Read recent historical bars without broker order authority.

        formatDate=2 asks ib_async/IBKR for timezone-aware UTC datetimes.
        This method never increments write_calls and never places/cancels orders.
        """
        import pandas as pd

        contract = self.stock_contract(symbol)
        try:
            self.ib.reqMarketDataType(int(self.cfg["broker"].get("market_data_type", 1)))
        except Exception:
            pass
        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr=str(duration),
            barSizeSetting=str(bar_size),
            whatToShow=str(what_to_show),
            useRTH=bool(use_rth),
            formatDate=2,
            keepUpToDate=False,
            timeout=float(self.cfg["runtime"].get("broker_snapshot_timeout_seconds", 8)),
        )
        if not bars:
            raise RuntimeError(f"IBKR returned no historical bars for {symbol}")

        rows = []
        for bar in bars:
            ts = pd.Timestamp(getattr(bar, "date", None))
            if pd.isna(ts):
                raise ValueError(f"IBKR historical bar has invalid timestamp for {symbol}")
            ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
            rows.append({
                "timestamp": ts,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
            })
        frame = pd.DataFrame(rows).set_index("timestamp").sort_index(kind="stable")
        frame.index = pd.DatetimeIndex(frame.index, tz="UTC", name="timestamp")
        return frame

    def quote(self, symbol: str) -> QuoteSnapshot:
        contract = self.stock_contract(symbol)
        try:
            self.ib.reqMarketDataType(int(self.cfg["broker"].get("market_data_type", 1)))
        except Exception:
            pass
        tickers = self.ib.reqTickers(contract)
        if len(tickers) != 1:
            raise RuntimeError(f"no quote for {symbol}")
        t = tickers[0]
        bid = _finite(getattr(t, "bid", None))
        ask = _finite(getattr(t, "ask", None))
        last = _finite(getattr(t, "last", None))
        if bid is None or ask is None or ask < bid:
            raise RuntimeError(f"invalid bid/ask for {symbol}: bid={bid} ask={ask}")
        details = self.ib.reqContractDetails(contract)
        min_tick = 0.01
        if details:
            mt = _finite(getattr(details[0], "minTick", None))
            if mt is not None:
                min_tick = mt
        return QuoteSnapshot(
            symbol=symbol.upper(),
            bid=bid,
            ask=ask,
            last=last,
            min_tick=min_tick,
            observed_at=datetime.now(timezone.utc).isoformat(),
        )

    def fx_to_asset_currency(self, base_currency: str, asset_currency: str = "USD") -> float:
        base = base_currency.upper()
        quote = asset_currency.upper()
        if base == quote:
            return 1.0
        pair = f"{base}{quote}"
        contract = self.Forex(pair)
        qualified = self.ib.qualifyContracts(contract)
        if not qualified:
            raise RuntimeError(f"cannot qualify FX pair {pair}")
        ticker = self.ib.reqTickers(qualified[0])[0]
        bid = _finite(getattr(ticker, "bid", None))
        ask = _finite(getattr(ticker, "ask", None))
        last = _finite(getattr(ticker, "last", None))
        if bid and ask:
            return (bid + ask) / 2.0
        if last:
            return last
        raise RuntimeError(f"no usable FX quote for {pair}")

    def what_if_buy(self, symbol: str, quantity: int, limit_price: float, order_ref: str) -> dict[str, Any]:
        contract = self.stock_contract(symbol)
        order = self.LimitOrder(
            "BUY", int(quantity), float(limit_price), tif="DAY", outsideRth=False, orderRef=order_ref
        )
        state = self.ib.whatIfOrder(contract, order)
        return {
            "commission": getattr(state, "commission", None),
            "min_commission": getattr(state, "minCommission", None),
            "max_commission": getattr(state, "maxCommission", None),
            "init_margin_change": getattr(state, "initMarginChange", None),
            "maint_margin_change": getattr(state, "maintMarginChange", None),
            "equity_with_loan_change": getattr(state, "equityWithLoanChange", None),
            "warning_text": str(getattr(state, "warningText", "") or ""),
        }

    def submit_protected_buy(
        self, *, symbol: str, quantity: int, entry_limit: float, stop_price: float, order_ref: str
    ) -> list[dict[str, Any]]:
        if self.readonly:
            raise RuntimeError("broker connection is read-only")
        contract = self.stock_contract(symbol)
        parent_id = self.ib.client.getReqId()
        parent = self.LimitOrder(
            "BUY", int(quantity), float(entry_limit),
            orderId=parent_id, transmit=False, tif="DAY", outsideRth=False, orderRef=order_ref,
        )
        stop = self.StopOrder(
            "SELL", int(quantity), float(stop_price),
            orderId=self.ib.client.getReqId(), parentId=parent_id,
            transmit=True, tif="GTC", outsideRth=False, orderRef=order_ref,
        )
        trades = []
        parent_placed = False
        try:
            for role, order in (("ENTRY", parent), ("PROTECTIVE_STOP", stop)):
                trade = self.ib.placeOrder(contract, order)
                self.write_calls += 1
                if role == "ENTRY":
                    parent_placed = True
                trades.append({
                    "role": role,
                    "broker_order_id": int(order.orderId),
                    "status": str(trade.orderStatus.status),
                    "order_ref": order_ref,
                    "symbol": symbol.upper(),
                    "action": str(order.action),
                    "quantity": float(order.totalQuantity),
                    "order_type": str(order.orderType),
                })
            return trades
        except Exception:
            # Parent is transmit=False. If the protective child cannot be staged,
            # explicitly cancel the parent so a later TWS action cannot transmit an
            # unprotected entry. Reconciliation will still block on any residue.
            if parent_placed:
                try:
                    self.ib.cancelOrder(parent)
                    self.write_calls += 1
                except Exception:
                    pass
            raise

    def submit_exit(self, *, symbol: str, quantity: int, limit_price: float, order_ref: str) -> dict[str, Any]:
        if self.readonly:
            raise RuntimeError("broker connection is read-only")
        contract = self.stock_contract(symbol)
        order = self.LimitOrder(
            "SELL", int(quantity), float(limit_price),
            tif="DAY", outsideRth=False, orderRef=order_ref,
        )
        trade = self.ib.placeOrder(contract, order)
        self.write_calls += 1
        return {
            "role": "EXIT",
            "broker_order_id": int(order.orderId),
            "status": str(trade.orderStatus.status),
            "order_ref": order_ref,
            "symbol": symbol.upper(),
            "action": "SELL",
            "quantity": int(quantity),
            "order_type": str(order.orderType),
        }


    def cancel_managed_orders_for_symbol(self, symbol: str) -> list[dict[str, Any]]:
        if self.readonly:
            raise RuntimeError("broker connection is read-only")
        symbol = symbol.upper()
        cancelled: list[dict[str, Any]] = []
        for trade in list(self.ib.openTrades()):
            contract_symbol = str(getattr(trade.contract, "symbol", "")).upper()
            order = trade.order
            order_ref = str(getattr(order, "orderRef", "") or "")
            if contract_symbol != symbol or not order_ref.startswith("SQA:"):
                continue
            self.ib.cancelOrder(order)
            self.write_calls += 1
            cancelled.append({
                "broker_order_id": int(getattr(order, "orderId", 0)),
                "order_ref": order_ref,
                "symbol": symbol,
                "status": "CANCEL_REQUESTED",
            })
        return cancelled
