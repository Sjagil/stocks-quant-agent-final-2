from __future__ import annotations

import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pandas_market_calendars as mcal

from stocks.providers.env import load_project_env, secret
from stocks.providers.http import ProviderHTTPClient
from stocks.research.shariah_research_precheck import business_precheck

EODHD_SCREENER_URL = "https://eodhd.com/api/screener"


@dataclass(frozen=True)
class ProductionScreenResultV244:
    status: str
    generated_at: str
    screening_date: str | None
    expected_session: str | None
    fresh: bool
    provider: str
    fetched_rows: int
    candidate_rows: int
    trade_eligible_rows: int
    blockers: tuple[str, ...]
    execution_authority: str = "NONE"
    broker_calls: int = 0
    order_calls: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_production_screener_config_v244(root: str | Path) -> dict[str, Any]:
    path = Path(root) / "config/production_screener_v2_44.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != "production_screener_v2_44":
        raise ValueError("invalid production screener schema")
    if not 1 <= int(raw.get("maximum_candidates", 0)) <= 500:
        raise ValueError("maximum_candidates must be in [1, 500]")
    safety = raw.get("safety") or {}
    if safety.get("automatic_strategy_assignment") is not False:
        raise ValueError("production screener cannot assign strategies")
    if safety.get("automatic_order_submission") is not False:
        raise ValueError("production screener cannot submit orders")
    if safety.get("execution_authority") != "NONE":
        raise ValueError("production screener execution authority must be NONE")
    return raw


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _clip(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _latest_completed_session(now: pd.Timestamp) -> pd.Timestamp | None:
    now = pd.Timestamp(now)
    now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
    calendar = mcal.get_calendar("NYSE")
    schedule = calendar.schedule(
        start_date=(now - pd.Timedelta(days=14)).date().isoformat(),
        end_date=now.date().isoformat(),
    )
    if schedule.empty:
        return None
    closes = pd.to_datetime(schedule["market_close"], utc=True)
    completed = schedule.loc[closes <= now]
    if completed.empty:
        return None
    return pd.Timestamp(completed.index[-1])


def _session_distance(older: pd.Timestamp, newer: pd.Timestamp) -> int:
    if older.normalize() >= newer.normalize():
        return 0
    calendar = mcal.get_calendar("NYSE")
    schedule = calendar.schedule(
        start_date=older.date().isoformat(),
        end_date=newer.date().isoformat(),
    )
    return max(len(schedule) - 1, 0)


def _fetch_lane(
    client: ProviderHTTPClient,
    *,
    api_key: str,
    lane: str,
    lane_config: dict[str, Any],
) -> list[dict[str, Any]]:
    limit = int(lane_config.get("limit", 50))
    if not 1 <= limit <= 500:
        raise ValueError(f"{lane}: limit must be in [1, 500]")
    payload = client.get_json(
        EODHD_SCREENER_URL,
        params={
            "api_token": api_key,
            "fmt": "json",
            "filters": json.dumps(
                lane_config.get("filters") or [], separators=(",", ":")
            ),
            "sort": str(lane_config.get("sort") or "market_capitalization.desc"),
            "limit": limit,
            "offset": 0,
        },
    )
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise TypeError(f"{lane}: invalid EODHD screener response")
    return [
        {**row, "_source_lane": lane}
        for row in payload["data"]
        if isinstance(row, dict)
    ]


def fetch_eodhd_screener_rows_v244(
    config: dict[str, Any],
    *,
    api_key: str,
    client: ProviderHTTPClient | None = None,
) -> list[dict[str, Any]]:
    if not api_key.strip():
        raise ValueError("EODHD_API_KEY_MISSING")
    owned = client is None
    active = client or ProviderHTTPClient(
        timeout=float(config.get("request_timeout_seconds", 30)),
        user_agent="stocks-quant-agent/production-screener-v2.44",
    )
    try:
        rows: list[dict[str, Any]] = []
        for lane, lane_config in (config.get("lanes") or {}).items():
            rows.extend(
                _fetch_lane(
                    active,
                    api_key=api_key,
                    lane=str(lane).upper(),
                    lane_config=dict(lane_config or {}),
                )
            )
        return rows
    finally:
        if owned:
            active.close()


def _load_verified_shariah(
    root: Path,
    *,
    now: pd.Timestamp,
    config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    path = (
        root
        / "artifacts/research_runtime/shariah_financial_verification/verification.csv"
    )
    audit_path = path.parent / "audit.json"
    if not path.is_file() or not audit_path.is_file():
        return {}
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        as_of = pd.Timestamp(audit["as_of"])
        expected = _latest_completed_session(now)
        if (
            expected is None
            or as_of > expected
            or _session_distance(as_of, expected)
            > int(config.get("maximum_shariah_verification_session_age", 30))
        ):
            return {}
    except Exception:  # noqa: BLE001 - invalid/stale external evidence must fail closed
        return {}
    frame = pd.read_csv(path)
    if frame.empty or "symbol" not in frame:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in frame.to_dict(orient="records"):
        symbol = str(row.get("symbol") or "").strip().upper()
        if symbol:
            out[symbol] = row
    return out


def rank_production_screener_rows_v244(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    now: pd.Timestamp | None = None,
    verified_shariah: dict[str, dict[str, Any]] | None = None,
) -> tuple[pd.DataFrame, ProductionScreenResultV244]:
    now_ts = pd.Timestamp(now if now is not None else pd.Timestamp.now(tz="UTC"))
    now_ts = (
        now_ts.tz_localize("UTC") if now_ts.tzinfo is None else now_ts.tz_convert("UTC")
    )
    expected = _latest_completed_session(now_ts)
    verified = verified_shariah or {}
    merged: dict[str, dict[str, Any]] = {}
    fetched_rows = 0

    for raw in rows:
        fetched_rows += 1
        symbol = str(raw.get("code") or raw.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        lane = str(raw.get("_source_lane") or raw.get("lane") or "WATCHLIST").upper()
        existing = merged.get(symbol)
        if existing is None:
            merged[symbol] = {**raw, "_lanes": {lane}}
        else:
            existing["_lanes"].add(lane)

    normalized: list[dict[str, Any]] = []
    maximum_age = int(config.get("maximum_session_age", 2))
    minimums = config.get("minimum_scores") or {}

    for symbol, raw in merged.items():
        price = _finite(raw.get("adjusted_close"))
        market_cap = _finite(raw.get("market_capitalization"))
        volume_1d = _finite(raw.get("avgvol_1d"))
        volume_200d = _finite(raw.get("avgvol_200d"))
        eps = _finite(raw.get("earnings_share"))
        return_1d_pct = _finite(raw.get("refund_1d_p"))
        return_5d_pct = _finite(raw.get("refund_5d_p"))
        session = pd.to_datetime(raw.get("last_day_data_date"), errors="coerce")
        blockers: list[str] = []

        if price is None or price <= 0:
            blockers.append("PRICE_MISSING_OR_INVALID")
        if market_cap is None or market_cap <= 0:
            blockers.append("MARKET_CAP_MISSING_OR_INVALID")
        if volume_200d is None or volume_200d <= 0:
            blockers.append("AVERAGE_VOLUME_MISSING_OR_INVALID")
        if pd.isna(session):
            blockers.append("SCREENING_SESSION_MISSING")

        session_age = None
        if expected is not None and not pd.isna(session):
            session_age = _session_distance(pd.Timestamp(session), expected)
            if session_age > maximum_age:
                blockers.append("STALE_PROVIDER_ROW")

        precheck = business_precheck(
            sector=raw.get("sector"),
            industry=raw.get("industry"),
            name=raw.get("name"),
        )
        if precheck["status"] == "HARD_EXCLUSION_CANDIDATE":
            blockers.append("SHARIAH_BUSINESS_HARD_EXCLUSION")

        verification = verified.get(symbol) or {}
        shariah_verified = bool(verification.get("trade_eligible") is True) or str(
            verification.get("trade_eligible", "")
        ).strip().lower() in {"1", "true", "yes"}
        if shariah_verified:
            shariah_status = "SHARIAH_ELIGIBLE_PIT"
        elif precheck["status"] == "HARD_EXCLUSION_CANDIDATE":
            shariah_status = "SHARIAH_INELIGIBLE_BUSINESS"
        elif precheck["status"] == "MANUAL_REVIEW_REQUIRED":
            shariah_status = "SHARIAH_MANUAL_REVIEW_REQUIRED"
        else:
            shariah_status = "SHARIAH_FINANCIAL_VERIFICATION_REQUIRED"

        r1 = float(return_1d_pct or 0.0)
        r5 = float(return_5d_pct or 0.0)
        dollar_volume = float(price or 0.0) * float(volume_200d or volume_1d or 0.0)
        fundamental_score = _clip(
            55.0 + (20.0 if eps is not None and eps > 0 else -20.0)
        )
        technical_score = _clip(
            50.0 + max(-10.0, min(10.0, r1)) * 2.0 + max(-20.0, min(20.0, r5)) * 1.25
        )
        liquidity_score = _clip(20.0 * math.log10(max(dollar_volume, 1.0)) - 80.0)
        risk_score = _clip(100.0 - min(85.0, abs(r1) * 3.0 + abs(r5) * 1.2))
        total_score = _clip(
            0.25 * fundamental_score
            + 0.40 * technical_score
            + 0.20 * liquidity_score
            + 0.15 * risk_score
        )

        if dollar_volume < float(minimums.get("liquidity_dollar_volume", 1_500_000)):
            blockers.append("DOLLAR_VOLUME_BELOW_FLOOR")

        if total_score >= float(
            minimums.get("high_potential", 70)
        ) and technical_score >= float(minimums.get("technical", 55)):
            classification = "HIGH_POTENTIAL"
        elif total_score >= float(minimums.get("watchlist", 52)):
            classification = "WATCHLIST"
        else:
            classification = "MONITOR"

        lanes = set(raw.get("_lanes") or {"WATCHLIST"})
        if "GEM" in lanes and market_cap is not None and market_cap <= 25_000_000_000:
            lane = "GEM"
        elif "CORE" in lanes:
            lane = "CORE"
        elif "TACTICAL" in lanes:
            lane = "TACTICAL"
        else:
            lane = min(lanes)

        screen_eligible = not blockers and classification in {
            "HIGH_POTENTIAL",
            "WATCHLIST",
        }
        normalized.append(
            {
                "symbol": symbol,
                "name": raw.get("name"),
                "exchange": str(raw.get("exchange") or "US").upper(),
                "sector": raw.get("sector"),
                "industry": raw.get("industry"),
                "lane": lane,
                "matched_lanes": "|".join(sorted(lanes)),
                "classification": classification,
                "last_day_data_date": None
                if pd.isna(session)
                else pd.Timestamp(session).date().isoformat(),
                "session_age": session_age,
                "price": price,
                "market_cap": market_cap,
                "eps": eps,
                "return_1d_pct": return_1d_pct,
                "return_5d_pct": return_5d_pct,
                "avg_volume_1d": volume_1d,
                "avg_volume_200d": volume_200d,
                "dollar_volume_200d": dollar_volume,
                "fundamental_score": round(fundamental_score, 6),
                "technical_score": round(technical_score, 6),
                "liquidity_score": round(liquidity_score, 6),
                "risk_score": round(risk_score, 6),
                "total_score": round(total_score, 6),
                "business_precheck": precheck["status"],
                "shariah_status": shariah_status,
                "shariah_verified": shariah_verified,
                "screen_eligible": screen_eligible,
                "trade_eligible": screen_eligible and shariah_verified,
                "blockers": "|".join(sorted(set(blockers))),
                "strategy_assignment": "NOT_ASSIGNED_BY_SCREENER",
                "execution_authority": "NONE",
                "broker_calls": 0,
                "order_calls": 0,
            }
        )

    frame = pd.DataFrame(normalized)
    if not frame.empty:
        frame = frame.sort_values(
            ["screen_eligible", "trade_eligible", "total_score", "symbol"],
            ascending=[False, False, False, True],
        ).head(int(config["maximum_candidates"]))
        frame = frame.reset_index(drop=True)
        frame["rank"] = range(1, len(frame) + 1)

    screening_dates = (
        [] if frame.empty else frame["last_day_data_date"].dropna().astype(str).tolist()
    )
    screening_date = max(screening_dates) if screening_dates else None
    fresh = bool(expected is not None and screening_date is not None)
    if fresh:
        fresh = _session_distance(pd.Timestamp(screening_date), expected) <= maximum_age
    top_blockers: list[str] = []
    if frame.empty:
        top_blockers.append("NO_CANDIDATES")
    if not fresh:
        top_blockers.append("SCREENER_DATA_STALE_OR_MISSING")
    result = ProductionScreenResultV244(
        status="SUCCEEDED"
        if frame is not None and not frame.empty and fresh
        else "FAILED",
        generated_at=now_ts.isoformat(),
        screening_date=screening_date,
        expected_session=None if expected is None else expected.date().isoformat(),
        fresh=fresh,
        provider=str(config.get("provider") or "EODHD"),
        fetched_rows=fetched_rows,
        candidate_rows=len(frame),
        trade_eligible_rows=int(frame["trade_eligible"].sum())
        if not frame.empty
        else 0,
        blockers=tuple(top_blockers),
    )
    return frame, result


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass


def write_production_screener_v244(
    root: str | Path,
    rows: list[dict[str, Any]],
    *,
    now: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, ProductionScreenResultV244, Path]:
    root = Path(root).resolve()
    config = load_production_screener_config_v244(root)
    frame, result = rank_production_screener_rows_v244(
        rows,
        config,
        now=now,
        verified_shariah=_load_verified_shariah(
            root,
            now=pd.Timestamp(now if now is not None else pd.Timestamp.now(tz="UTC")),
            config=config,
        ),
    )
    output = root / config["artifact_root"]
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "candidates.csv", index=False)
    frame.to_parquet(output / "candidates.parquet", index=False)
    _atomic_text(
        output / "summary.json",
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
    )
    return frame, result, output


def run_production_screener_v244(
    root: str | Path,
    *,
    offline_rows: list[dict[str, Any]] | None = None,
    now: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, ProductionScreenResultV244, Path]:
    root = Path(root).resolve()
    load_project_env(root)
    config = load_production_screener_config_v244(root)
    rows = offline_rows
    if rows is None:
        api_key = secret("EODHD_API_KEY", "EOD_API_KEY", "EODHISTORICALDATA_API_KEY")
        try:
            rows = fetch_eodhd_screener_rows_v244(config, api_key=api_key)
        except Exception as exc:  # noqa: BLE001 - provider failures become a closed artifact
            now_ts = pd.Timestamp(
                now if now is not None else pd.Timestamp.now(tz="UTC")
            )
            now_ts = (
                now_ts.tz_localize("UTC")
                if now_ts.tzinfo is None
                else now_ts.tz_convert("UTC")
            )
            output = root / config["artifact_root"]
            output.mkdir(parents=True, exist_ok=True)
            frame = pd.DataFrame(
                columns=[
                    "rank",
                    "symbol",
                    "lane",
                    "classification",
                    "total_score",
                    "screen_eligible",
                    "shariah_status",
                    "trade_eligible",
                    "blockers",
                    "execution_authority",
                    "broker_calls",
                    "order_calls",
                ]
            )
            result = ProductionScreenResultV244(
                status="FAILED",
                generated_at=now_ts.isoformat(),
                screening_date=None,
                expected_session=None,
                fresh=False,
                provider=str(config.get("provider") or "EODHD"),
                fetched_rows=0,
                candidate_rows=0,
                trade_eligible_rows=0,
                blockers=(f"PROVIDER_{type(exc).__name__.upper()}",),
            )
            frame.to_csv(output / "candidates.csv", index=False)
            frame.to_parquet(output / "candidates.parquet", index=False)
            _atomic_text(
                output / "summary.json",
                json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
            )
            return frame, result, output
    return write_production_screener_v244(root, rows, now=now)


def production_screener_allows_symbol_v244(
    root: str | Path,
    symbol: str,
    *,
    now: pd.Timestamp | None = None,
) -> tuple[bool, str]:
    root = Path(root).resolve()
    config = load_production_screener_config_v244(root)
    if not bool(config.get("enabled", True)) or not bool(
        config.get("required_for_new_entries", True)
    ):
        return True, "SCREENER_GATE_DISABLED"

    output = root / config["artifact_root"]
    summary_path = output / "summary.json"
    candidates_path = output / "candidates.csv"
    if not summary_path.is_file() or not candidates_path.is_file():
        return False, "PRODUCTION_SCREENER_ARTIFACT_MISSING"
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("status") != "SUCCEEDED" or summary.get("fresh") is not True:
            return False, "PRODUCTION_SCREENER_NOT_READY"
        screening_date = pd.Timestamp(summary["screening_date"])
        now_ts = pd.Timestamp(now if now is not None else pd.Timestamp.now(tz="UTC"))
        now_ts = (
            now_ts.tz_localize("UTC")
            if now_ts.tzinfo is None
            else now_ts.tz_convert("UTC")
        )
        expected = _latest_completed_session(now_ts)
        if expected is None or _session_distance(screening_date, expected) > int(
            config.get("maximum_session_age", 2)
        ):
            return False, "PRODUCTION_SCREENER_STALE"
        frame = pd.read_csv(candidates_path)
    except Exception:  # noqa: BLE001 - corrupt external artifacts must fail closed
        return False, "PRODUCTION_SCREENER_ARTIFACT_INVALID"

    match = frame.loc[
        frame.get("symbol", pd.Series(dtype=str)).astype(str).str.upper()
        == symbol.upper()
    ]
    if match.empty:
        return False, "SYMBOL_NOT_IN_CURRENT_PRODUCTION_SCREEN"
    eligible = str(match.iloc[0].get("screen_eligible", "")).strip().lower() in {
        "1",
        "true",
        "yes",
    }
    return (
        (True, "CURRENT_PRODUCTION_SCREEN_PASS")
        if eligible
        else (False, "CURRENT_PRODUCTION_SCREEN_BLOCKED")
    )


__all__ = [
    "ProductionScreenResultV244",
    "fetch_eodhd_screener_rows_v244",
    "load_production_screener_config_v244",
    "production_screener_allows_symbol_v244",
    "rank_production_screener_rows_v244",
    "run_production_screener_v244",
    "write_production_screener_v244",
]
