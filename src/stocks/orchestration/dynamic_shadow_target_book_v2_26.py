from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from stocks.intelligence_agent.strategy_combo_research_lab import FeatureCache
from stocks.orchestration.validated_portfolio_gateway_v2_24 import (
    build_dynamic_validated_portfolio_intents,
)
from stocks.research.dynamic_universe_generalization import discover_interval_sources
from stocks.research.strategy_factory_1h import prepare_one_hour_frame

SCHEMA = "dynamic_shadow_target_book_v2_26"
AUTHORITY_NONE = "NONE"
DEFAULT_SIGNAL_ROOT = Path(
    "artifacts/research_runtime/dynamic_validated_forward_signal_state_v2_24"
)
DEFAULT_ELIGIBILITY_PATH = Path(
    "artifacts/research_runtime/shariah_financial_verification/verification.csv"
)
DEFAULT_BROKER_SNAPSHOT = Path(
    "artifacts/research_runtime/ibkr_readonly_v2_9/snapshot.json"
)
DEFAULT_OUTPUT_ROOT = Path(
    "artifacts/research_runtime/dynamic_shadow_target_book_v2_26"
)


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def _utc(value: Any, *, field: str) -> datetime:
    try:
        parsed = pd.Timestamp(value)
    except Exception as exc:
        raise ValueError(f"{field} is invalid") from exc
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    else:
        parsed = parsed.tz_convert("UTC")
    return parsed.to_pydatetime()


def _timestamp_candidates(payload: Mapping[str, Any]) -> list[Any]:
    snapshot = payload.get("snapshot") if isinstance(payload.get("snapshot"), Mapping) else {}
    economic = payload.get("economic_account_state") if isinstance(payload.get("economic_account_state"), Mapping) else {}
    values = [
        payload.get("captured_at"),
        payload.get("snapshot_time"),
        payload.get("timestamp"),
        snapshot.get("captured_at"),
        snapshot.get("snapshot_time"),
        snapshot.get("timestamp"),
        economic.get("captured_at"),
        economic.get("timestamp"),
    ]
    return [value for value in values if value not in (None, "")]


@dataclass(frozen=True)
class ShadowSizingPolicyV226:
    signal_max_age_seconds: int = 7200
    broker_snapshot_max_age_seconds: int = 120
    maximum_positions: int = 5
    maximum_single_weight: float = 0.35
    maximum_portfolio_heat: float = 0.06
    cash_floor: float = 0.03
    base_risk_fraction: float = 0.0100
    strong_risk_fraction: float = 0.0125
    strong_conviction_threshold: float = 0.85
    hard_max_risk_fraction: float = 0.0150
    atr_period: int = 14
    stop_atr_multiple: float = 2.0
    minimum_stop_fraction: float = 0.02
    minimum_quantity: int = 1
    require_flat_broker: bool = True
    require_no_open_orders: bool = True

    def __post_init__(self) -> None:
        if min(self.signal_max_age_seconds, self.broker_snapshot_max_age_seconds, self.maximum_positions, self.atr_period, self.minimum_quantity) < 1:
            raise ValueError("positive sizing limits are required")
        if not 0 <= self.cash_floor < 1:
            raise ValueError("cash_floor must be in [0,1)")
        if not 0 < self.maximum_single_weight <= 1:
            raise ValueError("maximum_single_weight must be in (0,1]")
        if not 0 < self.maximum_portfolio_heat <= 1:
            raise ValueError("maximum_portfolio_heat must be in (0,1]")


def _position_rows(snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    root = snapshot.get("snapshot") if isinstance(snapshot.get("snapshot"), Mapping) else {}
    positions = root.get("positions") if isinstance(root.get("positions"), Mapping) else {}
    values = positions.get("positions") if isinstance(positions, Mapping) else []
    return [dict(row) for row in (values or []) if isinstance(row, Mapping)]




def _open_order_rows(snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    root = snapshot.get("snapshot") if isinstance(snapshot.get("snapshot"), Mapping) else {}
    orders = (
        root.get("all_api_open_orders")
        if isinstance(root.get("all_api_open_orders"), Mapping)
        else {}
    )
    values = orders.get("open_orders") if isinstance(orders, Mapping) else []
    return [dict(row) for row in (values or []) if isinstance(row, Mapping)]

def _position_map(
    snapshot: Mapping[str, Any],
    *,
    net_liquidation_eur: float,
) -> tuple[dict[str, dict[str, float | None]], dict[str, float], list[str]]:
    """Normalize current holdings without inventing EUR valuations.

    IBKR position ``average_cost``/``market_value`` may be denominated in the
    instrument currency.  v2.26 therefore accepts only explicitly EUR-valued
    fields for portfolio weights.  A non-zero holding without an EUR value is a
    fail-closed blocker rather than an implicit FX assumption.
    """
    output: dict[str, dict[str, float | None]] = {}
    weights: dict[str, float] = {}
    blockers: list[str] = []
    for raw in _position_rows(snapshot):
        symbol = str(raw.get("symbol") or "").upper().strip()
        quantity = _number(
            raw.get("position_quantity")
            if raw.get("position_quantity") is not None
            else raw.get("quantity")
        )
        market_value_eur = _number(
            raw.get("market_value_eur")
            if raw.get("market_value_eur") is not None
            else raw.get("reporting_market_value_eur")
        )
        average_cost = _number(raw.get("average_cost"))
        if not symbol or quantity is None:
            continue
        output[symbol] = {
            "quantity": float(quantity),
            "market_value_eur": market_value_eur,
            "average_cost": average_cost,
        }
        if abs(float(quantity)) <= 1e-12:
            weights[symbol] = 0.0
            continue
        if market_value_eur is None:
            blockers.append(f"POSITION_EUR_VALUATION_MISSING:{symbol}")
            continue
        weights[symbol] = (
            max(0.0, float(market_value_eur) / net_liquidation_eur)
            if net_liquidation_eur > 0
            else 0.0
        )
    return output, weights, blockers


def validate_broker_snapshot_v226(
    payload: Mapping[str, Any],
    *,
    decision_time: datetime,
    maximum_age_seconds: int,
) -> dict[str, Any]:
    blockers: list[str] = []
    economic = payload.get("economic_account_state") if isinstance(payload.get("economic_account_state"), Mapping) else {}
    net_liq = _number(economic.get("reporting_value_eur"))
    capacity = _number(economic.get("execution_sizing_capacity_eur"))
    spendable = _number(economic.get("spendable_eur"))
    if net_liq is None or net_liq <= 0:
        blockers.append("NET_LIQUIDATION_INVALID")
    if capacity is None or capacity < 0:
        blockers.append("EXECUTION_CAPACITY_INVALID")
    if spendable is None or spendable < 0:
        blockers.append("SPENDABLE_CASH_INVALID")
    if str(economic.get("execution_status") or "") != "EXECUTION_ACCOUNT_READY":
        blockers.append("EXECUTION_ACCOUNT_NOT_READY")
    if not _boolean(payload.get("double_snapshot_stable")):
        blockers.append("BROKER_DOUBLE_SNAPSHOT_NOT_STABLE")
    if not _boolean(payload.get("snapshot_components_complete", True)):
        blockers.append("BROKER_SNAPSHOT_COMPONENTS_INCOMPLETE")
    if int(payload.get("broker_write_calls", 0) or 0) != 0:
        blockers.append("BROKER_WRITE_ACTIVITY_PRESENT")

    captured_at: datetime | None = None
    for candidate in _timestamp_candidates(payload):
        try:
            captured_at = _utc(candidate, field="broker_snapshot_time")
            break
        except ValueError:
            continue
    if captured_at is None:
        blockers.append("BROKER_SNAPSHOT_TIMESTAMP_MISSING")
    else:
        age = (decision_time - captured_at).total_seconds()
        if age < -5:
            blockers.append("BROKER_SNAPSHOT_FROM_FUTURE")
        elif age > maximum_age_seconds:
            blockers.append("BROKER_SNAPSHOT_STALE")

    return {
        "valid": not blockers,
        "blockers": blockers,
        "captured_at": captured_at,
        "net_liquidation_eur": net_liq,
        "execution_capacity_eur": capacity,
        "spendable_eur": spendable,
        "execution_authority": AUTHORITY_NONE,
        "broker_write_calls": int(payload.get("broker_write_calls", 0) or 0),
        "order_calls": 0,
    }


def _reference_market_state(root: Path, symbol: str, *, policy: ShadowSizingPolicyV226) -> dict[str, Any]:
    sources = discover_interval_sources(root, "1h")
    path = sources.get(symbol)
    if path is None:
        return {"valid": False, "blocker": "CANONICAL_1H_SOURCE_MISSING"}
    try:
        frame = prepare_one_hour_frame(pd.read_parquet(path), symbol)
        if frame.empty:
            raise ValueError("empty frame")
        cache = FeatureCache(frame)
        price = _number(frame["close"].iloc[-1])
        atr_values = cache.atr(policy.atr_period)
        atr = _number(atr_values[-1]) if len(atr_values) else None
        bar_time = _utc(frame["date"].iloc[-1], field="reference_bar_time")
    except Exception as exc:
        return {"valid": False, "blocker": f"CANONICAL_1H_SOURCE_INVALID:{type(exc).__name__}"}
    if price is None or price <= 0 or atr is None or atr < 0:
        return {"valid": False, "blocker": "PRICE_OR_ATR_NOT_AVAILABLE"}
    stop = max(float(atr) * policy.stop_atr_multiple, float(price) * policy.minimum_stop_fraction)
    return {
        "valid": True,
        "price_eur": float(price),
        "atr_eur": float(atr),
        "stop_distance_eur": float(stop),
        "bar_time": bar_time,
        "canonical_source": str(path),
    }


def _risk_fraction(confidence: float, policy: ShadowSizingPolicyV226) -> float:
    chosen = policy.strong_risk_fraction if confidence >= policy.strong_conviction_threshold else policy.base_risk_fraction
    return min(float(chosen), float(policy.hard_max_risk_fraction))


def build_dynamic_shadow_target_book_v226(
    project_root: str | Path,
    *,
    decision_time: datetime,
    broker_snapshot: Mapping[str, Any],
    signals: pd.DataFrame,
    signal_audit: Mapping[str, Any],
    eligibility: pd.DataFrame,
    policy: ShadowSizingPolicyV226 | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()
    active = policy or ShadowSizingPolicyV226()
    now = decision_time.astimezone(UTC) if decision_time.tzinfo else decision_time.replace(tzinfo=UTC)
    broker = validate_broker_snapshot_v226(
        broker_snapshot,
        decision_time=now,
        maximum_age_seconds=active.broker_snapshot_max_age_seconds,
    )
    if not broker["valid"]:
        return pd.DataFrame(), pd.DataFrame(), {
            "schema": SCHEMA,
            "ready": False,
            "shadow_ready": False,
            "blockers": broker["blockers"],
            "execution_authority": AUTHORITY_NONE,
            "broker_submission_enabled": False,
            "order_calls": 0,
        }
    net_liq = float(broker["net_liquidation_eur"])
    capacity = float(broker["execution_capacity_eur"])
    spendable = float(broker["spendable_eur"])
    positions, current_weights, position_blockers = _position_map(
        broker_snapshot,
        net_liquidation_eur=net_liq,
    )
    nonzero_positions = sorted(
        symbol
        for symbol, row in positions.items()
        if abs(float(row.get("quantity") or 0.0)) > 1e-12
    )
    if active.require_flat_broker and nonzero_positions:
        position_blockers.append(
            "INITIAL_SHADOW_REQUIRES_FLAT_BROKER:" + ",".join(nonzero_positions)
        )
    if active.require_no_open_orders and _open_order_rows(broker_snapshot):
        position_blockers.append("INITIAL_SHADOW_REQUIRES_NO_OPEN_ORDERS")
    if position_blockers:
        return pd.DataFrame(), pd.DataFrame(), {
            "schema": SCHEMA,
            "ready": False,
            "shadow_ready": False,
            "blockers": position_blockers,
            "execution_authority": AUTHORITY_NONE,
            "broker_submission_enabled": False,
            "broker_calls": 0,
            "order_calls": 0,
        }

    # v2.24 gateway independently re-validates dynamic deployment hashes,
    # closed-bar signal contract, Shariah eligibility, long-only and no leverage.
    bundle = build_dynamic_validated_portfolio_intents(
        signals,
        signal_audit,
        eligibility,
        decision_time=now,
        equity_eur=net_liq,
        current_weights=current_weights,
    )

    signal_times = pd.to_datetime(signals.get("signal_bar_time"), utc=True, errors="coerce")
    ready_mask = signals.get("new_entry_ready", pd.Series(False, index=signals.index)).map(_boolean)
    if ready_mask.any():
        ready_times = signal_times.loc[ready_mask]
        if ready_times.isna().any():
            raise ValueError("ready signal contains invalid signal_bar_time")
        if ((pd.Timestamp(now) - ready_times).dt.total_seconds() > active.signal_max_age_seconds).any():
            raise ValueError("STALE_READY_SIGNAL_REACHED_SHADOW_SIZING")

    target_rows: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for target in bundle.projection.targets:
        symbol = target.symbol.upper()
        market = _reference_market_state(root, symbol, policy=active)
        blockers: list[str] = []
        if not market.get("valid"):
            blockers.append(str(market.get("blocker")))
            price = stop = None
            bar_age = None
        else:
            price = float(market["price_eur"])
            stop = float(market["stop_distance_eur"])
            bar_age = (now - market["bar_time"]).total_seconds()
            if bar_age < -5:
                blockers.append("REFERENCE_BAR_FROM_FUTURE")
            elif bar_age > active.signal_max_age_seconds:
                blockers.append("REFERENCE_MARKET_DATA_STALE")
        existing = positions.get(symbol, {"quantity": 0.0, "market_value_eur": 0.0})
        existing_qty = max(0, int(math.floor(float(existing.get("quantity", 0.0)))))
        target_notional = net_liq * min(float(target.target_weight), active.maximum_single_weight)
        desired_qty = int(math.floor(target_notional / price)) if price and price > 0 else 0
        risk_fraction = _risk_fraction(float(target.confidence), active)
        risk_budget = net_liq * risk_fraction
        risk_qty = int(math.floor(risk_budget / stop)) if stop and stop > 0 else 0
        cash_budget = max(0.0, min(capacity, spendable) - net_liq * active.cash_floor)
        cash_qty = int(math.floor(cash_budget / price)) if price and price > 0 else 0
        total_qty = min(desired_qty, risk_qty) if desired_qty and risk_qty else 0
        if total_qty > existing_qty:
            total_qty = min(total_qty, existing_qty + cash_qty)
        total_qty = max(0, total_qty)
        stop_risk = float(total_qty * stop) if stop else 0.0
        candidates.append(
            {
                "symbol": symbol,
                "target": target,
                "market": market,
                "blockers": blockers,
                "existing_qty": existing_qty,
                "desired_qty": desired_qty,
                "risk_qty": risk_qty,
                "cash_qty": cash_qty,
                "provisional_qty": total_qty,
                "stop_risk": stop_risk,
                "target_notional_eur": target_notional,
                "risk_budget_eur": risk_budget,
            }
        )

    # Allocate risk heat deterministically: strongest confidence first, then symbol.
    heat_budget_eur = net_liq * active.maximum_portfolio_heat
    heat_used_eur = 0.0
    selected_positions = 0
    for item in sorted(candidates, key=lambda value: (-float(value["target"].confidence), value["symbol"])):
        blockers = list(item["blockers"])
        quantity = int(item["provisional_qty"])
        if selected_positions >= active.maximum_positions and quantity > 0:
            blockers.append("MAXIMUM_POSITION_COUNT_REACHED")
            quantity = 0
        stop = _number(item["market"].get("stop_distance_eur")) if item["market"].get("valid") else None
        if quantity > 0 and stop:
            remaining_heat = max(0.0, heat_budget_eur - heat_used_eur)
            heat_qty = int(math.floor(remaining_heat / stop))
            quantity = min(quantity, heat_qty)
            if quantity < active.minimum_quantity:
                blockers.append("PORTFOLIO_HEAT_EXHAUSTED")
                quantity = 0
        if quantity > 0:
            heat_used_eur += quantity * float(stop)
            selected_positions += 1
        existing_qty = int(item["existing_qty"])
        delta = quantity - existing_qty
        action = "BUY" if delta > 0 else ("SELL" if delta < 0 else "HOLD")
        if action == "SELL":
            delta = max(delta, -existing_qty)
        target = item["target"]
        price = _number(item["market"].get("price_eur")) if item["market"].get("valid") else None
        row = {
            "symbol": item["symbol"],
            "decision_id": bundle.decision_id,
            "target_weight": float(target.target_weight),
            "confidence": float(target.confidence),
            "strategy_ids": "|".join(target.strategy_ids),
            "hypothesis_ids": "|".join(target.hypothesis_ids),
            "reference_price_eur": price,
            "atr_eur": item["market"].get("atr_eur"),
            "stop_distance_eur": stop,
            "existing_quantity": existing_qty,
            "target_quantity": quantity,
            "delta_quantity": int(delta),
            "shadow_action": action,
            "target_notional_eur": float(quantity * price) if price else 0.0,
            "estimated_stop_risk_eur": float(quantity * stop) if stop else 0.0,
            "risk_budget_eur": item["risk_budget_eur"],
            "portfolio_heat_after_eur": heat_used_eur,
            "sizing_ready": not blockers,
            "blockers": "|".join(dict.fromkeys(blockers)),
            "quantity_mode": "WHOLE_SHARES",
            "fractional_shares_allowed": False,
            "broker_submission_enabled": False,
            "execution_authority": AUTHORITY_NONE,
            "broker_calls": 0,
            "order_calls": 0,
        }
        target_rows.append(row)

    target_book = pd.DataFrame(target_rows)
    shadow_orders = (
        target_book.loc[target_book["shadow_action"].isin(["BUY", "SELL"]) & target_book["sizing_ready"]].copy()
        if not target_book.empty
        else pd.DataFrame()
    )
    if not shadow_orders.empty:
        shadow_orders["order_type"] = "SHADOW_ONLY"
        shadow_orders["transmit"] = False
        shadow_orders["order_id"] = [
            _hash({"decision_id": bundle.decision_id, "symbol": row["symbol"], "action": row["shadow_action"], "quantity": int(row["delta_quantity"])})
            for row in shadow_orders.to_dict(orient="records")
        ]

    audit = {
        "schema": SCHEMA,
        "ready": True,
        "shadow_ready": True,
        "decision_id": bundle.decision_id,
        "decision_time": now.isoformat(),
        "input_signal_rows": int(len(signals)),
        "verified_eligibility_rows": int(eligibility.get("trade_eligible", pd.Series(dtype=bool)).map(_boolean).sum()) if not eligibility.empty else 0,
        "projected_positions": int(len(bundle.projection.targets)),
        "target_book_rows": int(len(target_book)),
        "shadow_order_rows": int(len(shadow_orders)),
        "net_liquidation_eur": net_liq,
        "execution_capacity_eur": capacity,
        "spendable_eur": spendable,
        "portfolio_heat_eur": heat_used_eur,
        "portfolio_heat_fraction": heat_used_eur / net_liq if net_liq > 0 else None,
        "maximum_portfolio_heat": active.maximum_portfolio_heat,
        "whole_shares_only": True,
        "long_only": True,
        "shariah_only": True,
        "leverage_allowed": False,
        "signal_freshness_enforced": True,
        "broker_snapshot_freshness_enforced": True,
        "broker_snapshot_stable": True,
        "automatic_live_promotion": False,
        "broker_submission_enabled": False,
        "execution_authority": AUTHORITY_NONE,
        "broker_calls": 0,
        "order_calls": 0,
    }
    return target_book, shadow_orders, audit


def build_dynamic_shadow_target_book_from_project_v226(
    project_root: str | Path,
    *,
    decision_time: datetime,
    broker_snapshot_path: str | Path | None = None,
    eligibility_path: str | Path | None = None,
    policy: ShadowSizingPolicyV226 | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()
    signal_root = root / DEFAULT_SIGNAL_ROOT
    snapshot_path = Path(broker_snapshot_path).resolve() if broker_snapshot_path else root / DEFAULT_BROKER_SNAPSHOT
    eligible_path = Path(eligibility_path).resolve() if eligibility_path else root / DEFAULT_ELIGIBILITY_PATH
    for path in (signal_root / "signals.csv", signal_root / "audit.json", snapshot_path, eligible_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    signals = pd.read_csv(signal_root / "signals.csv", dtype={"hypothesis_id": str})
    signal_audit = json.loads((signal_root / "audit.json").read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    # The v2.9 worker validates broker-internal snapshot age while deriving
    # economic_account_state.  Its serialized payload does not currently expose
    # a top-level capture timestamp, so bind freshness to the newly copied
    # artifact mtime as a second, local freshness check.
    if not _timestamp_candidates(snapshot):
        snapshot["captured_at"] = datetime.fromtimestamp(
            snapshot_path.stat().st_mtime,
            tz=UTC,
        ).isoformat()
        snapshot["snapshot_timestamp_source"] = "ARTIFACT_MTIME_AFTER_READONLY_CAPTURE"
    eligibility = pd.read_csv(eligible_path)
    return build_dynamic_shadow_target_book_v226(
        root,
        decision_time=decision_time,
        broker_snapshot=snapshot,
        signals=signals,
        signal_audit=signal_audit,
        eligibility=eligibility,
        policy=policy,
    )


def write_dynamic_shadow_target_book_v226(
    target_book: pd.DataFrame,
    shadow_orders: pd.DataFrame,
    audit: Mapping[str, Any],
    output_root: str | Path,
) -> Path:
    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=True)
    target_book.to_csv(output / "target_book.csv", index=False)
    shadow_orders.to_csv(output / "shadow_orders.csv", index=False)
    (output / "audit.json").write_text(
        json.dumps(dict(audit), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return output


__all__ = [
    "ShadowSizingPolicyV226",
    "validate_broker_snapshot_v226",
    "build_dynamic_shadow_target_book_v226",
    "build_dynamic_shadow_target_book_from_project_v226",
    "write_dynamic_shadow_target_book_v226",
]
