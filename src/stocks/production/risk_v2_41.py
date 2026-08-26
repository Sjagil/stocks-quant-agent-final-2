from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.data.canonical import read_canonical_parquet
from .contracts_v2_41 import ProductionIntent, QuoteSnapshot


def round_to_tick(price: float, tick: float, *, direction: str = "nearest") -> float:
    tick = max(float(tick), 1e-9)
    units = float(price) / tick
    if direction == "down":
        units = math.floor(units + 1e-12)
    elif direction == "up":
        units = math.ceil(units - 1e-12)
    else:
        units = round(units)
    return float(units * tick)


def atr(frame: pd.DataFrame, period: int = 14) -> float:
    if len(frame) < period + 2:
        raise ValueError("insufficient rows for ATR")
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    close = pd.to_numeric(frame["close"], errors="coerce")
    prev = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev).abs(), (low - prev).abs()],
        axis=1,
    ).max(axis=1)
    value = float(tr.rolling(period, min_periods=period).mean().iloc[-1])
    if not math.isfinite(value) or value <= 0:
        raise ValueError("invalid ATR")
    return value


def build_buy_intent(
    *,
    root: Path,
    symbol: str,
    proposal: dict[str, Any],
    quote: QuoteSnapshot,
    net_liquidation_base: float,
    available_funds_base: float,
    fx_base_to_usd: float,
    cfg: dict[str, Any],
) -> tuple[ProductionIntent | None, dict[str, Any]]:
    risk = cfg["risk"]
    if quote.spread_bps > float(risk["maximum_spread_bps"]):
        return None, {"blocker": "SPREAD_TOO_WIDE", "spread_bps": quote.spread_bps}

    data_path = root / cfg["data"]["provider_root"] / f"{symbol.upper()}_{cfg['data']['timeframe']}.parquet"
    frame, _ = read_canonical_parquet(data_path, verify_hash=False, verify_metadata=False)
    atr_value = atr(frame, int(risk["atr_period"]))

    raw_entry = quote.ask * (1.0 + float(risk["entry_limit_slippage_bps"]) / 10_000.0)
    entry = round_to_tick(raw_entry, quote.min_tick, direction="up")
    raw_stop_distance = float(risk["stop_atr_multiplier"]) * atr_value
    stop_bps = raw_stop_distance / entry * 10_000.0
    stop_bps = max(float(risk["minimum_stop_bps"]), min(float(risk["maximum_stop_bps"]), stop_bps))
    stop_distance = entry * stop_bps / 10_000.0
    stop = round_to_tick(entry - stop_distance, quote.min_tick, direction="down")
    if stop <= 0 or stop >= entry:
        return None, {"blocker": "INVALID_PROTECTIVE_STOP", "entry": entry, "stop": stop}

    net_liq_usd = float(net_liquidation_base) * float(fx_base_to_usd)
    available_usd = float(available_funds_base) * float(fx_base_to_usd)
    risk_budget = net_liq_usd * float(risk["max_risk_per_trade_fraction"])
    risk_qty = math.floor(risk_budget / max(entry - stop, quote.min_tick))
    position_cap_usd = net_liq_usd * float(risk["max_position_fraction_of_net_liq"])
    position_qty = math.floor(position_cap_usd / entry)
    cash_cap_usd = max(0.0, available_usd - net_liq_usd * float(risk["minimum_cash_buffer_fraction"]))
    cash_qty = math.floor(cash_cap_usd / entry)

    quantities = [risk_qty, position_qty, cash_qty]
    max_canary_eur = float(risk.get("max_live_canary_notional_eur", 0) or 0)
    if max_canary_eur > 0:
        # The configuration is named EUR for compatibility with the repo's portfolio
        # layer. Use it only when account base currency is EUR; otherwise it should
        # remain zero and risk/equity sizing is authoritative.
        quantities.append(math.floor((max_canary_eur * fx_base_to_usd) / entry))

    qty = int(min(quantities))
    if qty < 1:
        return None, {
            "blocker": "WHOLE_SHARE_SIZE_ZERO",
            "risk_qty": risk_qty,
            "position_qty": position_qty,
            "cash_qty": cash_qty,
        }

    raw = {
        "symbol": symbol.upper(),
        "action": "BUY",
        "quantity": qty,
        "entry_limit": entry,
        "stop_price": stop,
        "source": "portfolio_decision_v2_7",
        "strategy_ids": proposal.get("strategy_ids"),
        "conviction": proposal.get("conviction"),
        "data_latest": frame.index.max().isoformat(),
    }
    intent_id = hashlib.sha256(
        json.dumps(raw, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    intent = ProductionIntent(
        intent_id=intent_id,
        symbol=symbol,
        action="BUY",
        quantity=qty,
        entry_limit=entry,
        stop_price=stop,
        source="portfolio_decision_v2_7",
        rationale=(
            "BUY_NEW",
            "WHOLE_SHARE_RISK_SIZED",
            "PROTECTIVE_STOP_REQUIRED",
        ),
        metadata=raw,
    )
    return intent, {
        "atr": atr_value,
        "entry_limit": entry,
        "stop_price": stop,
        "stop_bps": stop_bps,
        "risk_qty": risk_qty,
        "position_qty": position_qty,
        "cash_qty": cash_qty,
        "final_qty": qty,
        "spread_bps": quote.spread_bps,
    }


def build_exit_intent(symbol: str, quantity: int, quote: QuoteSnapshot, cfg: dict[str, Any]) -> ProductionIntent:
    raw_limit = quote.bid * (1.0 - float(cfg["risk"]["entry_limit_slippage_bps"]) / 10_000.0)
    limit_price = round_to_tick(raw_limit, quote.min_tick, direction="down")
    raw = {"symbol": symbol.upper(), "action": "SELL", "quantity": int(quantity), "limit": limit_price}
    intent_id = hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()
    return ProductionIntent(
        intent_id=intent_id,
        symbol=symbol,
        action="SELL",
        quantity=int(quantity),
        entry_limit=limit_price,
        stop_price=None,
        source="position_management_v2_41",
        rationale=("EXPLICIT_INACTIVE_POSITION_STATE",),
        metadata=raw,
    )
