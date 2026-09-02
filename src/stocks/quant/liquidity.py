from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd


def dollar_volume(price: pd.Series, volume: pd.Series) -> pd.Series:
    p = pd.to_numeric(price, errors="coerce").astype(float)
    v = pd.to_numeric(volume, errors="coerce").astype(float)
    return p * v


def amihud_illiquidity(
    returns: pd.Series,
    dollar_volume_values: pd.Series,
    *,
    scale: float = 1.0,
) -> float:
    r = pd.to_numeric(returns, errors="coerce").astype(float)
    dv = pd.to_numeric(dollar_volume_values, errors="coerce").astype(float)
    frame = pd.concat([r.rename("r"), dv.rename("dv")], axis=1).dropna()
    frame = frame[frame["dv"] > 0]
    if frame.empty:
        return float("nan")
    return float((frame["r"].abs() / frame["dv"]).mean() * scale)


def participation_rate(order_volume: float, market_volume: float) -> float:
    if order_volume < 0 or market_volume <= 0:
        raise ValueError("require order_volume >= 0 and market_volume > 0")
    return float(order_volume / market_volume)


def square_root_impact(
    *,
    volatility: float,
    order_volume: float,
    market_volume: float,
    coefficient: float = 1.0,
) -> float:
    if volatility < 0 or order_volume < 0 or market_volume <= 0 or coefficient < 0:
        raise ValueError("invalid impact inputs")
    return float(coefficient * volatility * math.sqrt(order_volume / market_volume))


def implementation_shortfall(
    *,
    decision_price: float,
    execution_price: float,
    side: str,
    fees_fraction: float = 0.0,
) -> float:
    if decision_price <= 0 or execution_price <= 0 or fees_fraction < 0:
        raise ValueError("prices must be positive and fees non-negative")
    normalized = side.strip().upper()
    if normalized not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL")
    raw = (
        execution_price / decision_price - 1.0
        if normalized == "BUY"
        else decision_price / execution_price - 1.0
    )
    return float(raw + fees_fraction)
