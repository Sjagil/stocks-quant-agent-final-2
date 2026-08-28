from __future__ import annotations

from copy import deepcopy
import re
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.data.canonical import (
    CanonicalMetadata,
    read_canonical_parquet,
    write_canonical_parquet,
)
from .current_session_alignment_v2_42 import align_ibkr_rth_to_eodhd_grid_v242
from .current_session_data_v2_41_2 import (
    closed_latest_session_bars,
    cross_provider_close_check,
    merge_overlay,
)
from .data_refresh_v2_41 import refresh_provider_fabric as refresh_finalized_history_v241
from .freshness_v2_41 import check_file_freshness
from .ibkr_adapter_v2_41 import IBKRBrokerV241
from .ibkr_historical_v2_43 import fetch_historical_batch_v243


def _metadata(
    symbol: str,
    timeframe: str,
    exchange: str,
    *,
    source: str,
    prior: dict[str, Any] | None,
    provenance: dict[str, Any],
) -> CanonicalMetadata:
    prior = prior or {}
    return CanonicalMetadata(
        symbol=symbol.upper(),
        timeframe=timeframe,
        source=source,
        exchange=str(prior.get("exchange") or exchange).upper(),
        asset_type=prior.get("asset_type"),
        currency=prior.get("currency") or "USD",
        adjustment=str(prior.get("adjustment") or "raw"),
        provenance={**(prior.get("provenance") or {}), **provenance},
    )


def _seed_finalized_history_once(root: Path, cfg: dict[str, Any]) -> list[str]:
    data_cfg = cfg["data"]
    final_root = root / data_cfg["provider_root"]
    history_root = root / data_cfg["finalized_history_root"]
    history_root.mkdir(parents=True, exist_ok=True)
    seeded: list[str] = []

    for raw_symbol in data_cfg["symbols"]:
        symbol = str(raw_symbol).upper()
        source = final_root / f"{symbol}_{data_cfg['timeframe']}.parquet"
        target = history_root / source.name
        if target.is_file() or not source.is_file():
            continue
        frame, prior = read_canonical_parquet(source, verify_hash=False, verify_metadata=False)
        prior_source = str((prior or {}).get("source") or "EODHD").upper()
        if "IBKR" in prior_source:
            raise ValueError(
                f"cannot seed finalized EODHD history from already-hybrid source for {symbol}: {prior_source}"
            )
        meta = _metadata(
            symbol,
            data_cfg["timeframe"],
            data_cfg["exchange"],
            source="EODHD",
            prior=prior,
            provenance={
                "production_finalized_history_v2_41_2": True,
                "seeded_from_pre_bridge_provider_fabric": True,
            },
        )
        write_canonical_parquet(
            frame,
            target,
            meta,
            extra_metadata={"seeded_from": str(source)},
        )
        seeded.append(symbol)
    return seeded


def _history_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(cfg)
    out["data"]["provider_root"] = cfg["data"]["finalized_history_root"]
    return out



def _ibkr_source_minutes(data_cfg: dict[str, Any]) -> int:
    explicit = data_cfg.get("ibkr_source_bar_minutes")
    if explicit not in (None, ""):
        value = int(explicit)
        if value <= 0:
            raise ValueError("IBKR_SOURCE_BAR_MINUTES_INVALID")
        return value
    raw = str(data_cfg.get("ibkr_history_bar_size", "")).strip().lower()
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", raw)
    number = float(match.group(1)) if match else 1.0
    if "hour" in raw:
        return int(round(number * 60.0))
    if "min" in raw:
        return int(round(number))
    raise ValueError(f"IBKR_SOURCE_BAR_SIZE_UNRECOGNIZED:{raw}")



def refresh_provider_fabric(root: str | Path, cfg: dict[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    data_cfg = cfg["data"]
    final_root = root / data_cfg["provider_root"]
    history_root = root / data_cfg["finalized_history_root"]
    final_root.mkdir(parents=True, exist_ok=True)

    try:
        seeded = _seed_finalized_history_once(root, cfg)
    except Exception as exc:
        return {
            "status": "FAILED",
            "failures": len(data_cfg.get("symbols", [])),
            "reason": f"FINALIZED_HISTORY_SEED_FAILED:{type(exc).__name__}:{exc}",
            "symbols": [],
            "broker_write_calls": 0,
            "execution_authority": "NONE",
        }

    history_result = refresh_finalized_history_v241(root, _history_cfg(cfg))
    if history_result.get("status") != "SUCCEEDED":
        return {
            "status": "FAILED",
            "failures": len(data_cfg.get("symbols", [])),
            "reason": "FINALIZED_HISTORY_REFRESH_FAILED",
            "history_seeded": seeded,
            "history": history_result,
            "symbols": [],
            "broker_write_calls": 0,
            "execution_authority": "NONE",
        }

    now = pd.Timestamp.now(tz="UTC")
    period = pd.Timedelta(hours=1 if data_cfg["timeframe"] == "1h" else 0)
    close_lag = pd.Timedelta(seconds=int(data_cfg.get("bar_close_lag_seconds", 120)))
    duration = str(data_cfg.get("ibkr_history_duration", "5 D"))
    bar_size = str(data_cfg.get("ibkr_history_bar_size", "30 mins"))
    what_to_show = str(data_cfg.get("ibkr_history_what_to_show", "TRADES"))
    use_rth = bool(data_cfg.get("ibkr_history_use_rth", True))
    min_overlap = int(data_cfg.get("minimum_cross_provider_overlap_bars", 3))
    max_disagreement = float(data_cfg.get("maximum_cross_provider_close_disagreement_bps", 50.0))
    tolerance = float(data_cfg.get("freshness_tolerance_minutes", 150))
    calendar_name = str(data_cfg.get("market_calendar", "NYSE"))
    source_bar_minutes = _ibkr_source_minutes(data_cfg)
    target_bar_minutes = int(data_cfg.get("production_target_bar_minutes", 60))
    reader = str(data_cfg.get("ibkr_historical_reader", "legacy")).strip()

    results: list[dict[str, Any]] = []
    failures = 0
    broker_write_calls = 0
    frames: dict[str, pd.DataFrame] = {}
    provider_results: dict[str, dict[str, Any]] = {}

    if reader == "stocks_ibkr_reference":
        try:
            batch = fetch_historical_batch_v243(
                root,
                [str(x).upper() for x in data_cfg["symbols"]],
                duration=duration,
                bar_size=bar_size,
                what_to_show=what_to_show,
                use_rth=use_rth,
            )
            frames = batch.frames
            provider_results = batch.symbol_results
            broker_write_calls = int(batch.broker_write_calls)
        except Exception as exc:
            return {
                "status": "FAILED",
                "failures": len(data_cfg.get("symbols", [])),
                "reason": f"IBKR_HISTORICAL_READER_FAILED:{type(exc).__name__}:{exc}",
                "history_seeded": seeded,
                "history": history_result,
                "symbols": [],
                "broker_write_calls": 0,
                "execution_authority": "NONE",
            }

    def process(symbol: str, ibkr_raw: pd.DataFrame) -> None:
        nonlocal failures
        history_path = history_root / f"{symbol}_{data_cfg['timeframe']}.parquet"
        target = final_root / history_path.name
        try:
            historical, history_meta = read_canonical_parquet(
                history_path, verify_hash=False, verify_metadata=False
            )
            ibkr_recent, alignment = align_ibkr_rth_to_eodhd_grid_v242(
                ibkr_raw,
                now=now,
                calendar_name=calendar_name,
                source_bar_minutes=source_bar_minutes,
                target_bar_minutes=target_bar_minutes,
                close_lag_seconds=int(data_cfg.get("bar_close_lag_seconds", 120)),
            )
            if ibkr_recent.empty:
                raise ValueError("IBKR_ALIGNMENT_NO_CLOSED_BARS")

            cross = cross_provider_close_check(
                historical,
                ibkr_recent,
                minimum_overlap_bars=min_overlap,
                maximum_close_disagreement_bps=max_disagreement,
            )
            if not cross.passed:
                raise ValueError(
                    f"{cross.reason}: overlap={cross.overlap_bars} "
                    f"max_bps={cross.max_close_disagreement_bps}"
                )

            overlay, session = closed_latest_session_bars(
                ibkr_recent,
                now=now,
                calendar_name=calendar_name,
                bar_period=period,
                close_lag=close_lag,
            )
            if overlay.empty:
                raise ValueError("CURRENT_SESSION_NO_CLOSED_IBKR_BARS")

            merged = merge_overlay(historical, overlay)
            meta = _metadata(
                symbol,
                data_cfg["timeframe"],
                data_cfg["exchange"],
                source="EODHD+IBKR",
                prior=history_meta,
                provenance={
                    "production_history_provider": "EODHD",
                    "production_current_session_provider": "IBKR",
                    "current_session_bridge_v2_43": True,
                    "closed_bars_only": True,
                    "regular_trading_hours_only": True,
                    "finalized_history_path": str(history_path),
                    "historical_reader": reader,
                    "bar_start_semantics": "NYSE_SESSION_OPEN_ANCHORED",
                    "bar_end_explicit_in_context_snapshot": True,
                    "decision_available_at_explicit_in_context_snapshot": True,
                },
            )
            write_canonical_parquet(
                merged,
                target,
                meta,
                extra_metadata={
                    "hybrid_refresh_v2_43": True,
                    "ibkr_duration": duration,
                    "ibkr_bar_size": bar_size,
                    "ibkr_what_to_show": what_to_show,
                    "ibkr_use_rth": use_rth,
                    "ibkr_raw_rows": len(ibkr_raw),
                    "ibkr_recent_rows": len(ibkr_recent),
                    "ibkr_closed_session_rows": len(overlay),
                    "alignment": alignment.to_dict(),
                    "session": session.to_dict(),
                    "cross_provider": cross.to_dict(),
                },
            )
            fresh = check_file_freshness(
                symbol,
                target,
                now=now,
                calendar_name=calendar_name,
                tolerance_minutes=tolerance,
            )
            if not fresh.passed:
                raise ValueError(f"PRODUCTION_DATA_STALE:{fresh.reason}")
            results.append({
                "symbol": symbol,
                "status": "SUCCEEDED",
                "freshness": fresh.to_dict(),
                "session": session.to_dict(),
                "cross_provider": cross.to_dict(),
                "ibkr_raw_rows": len(ibkr_raw),
                "ibkr_recent_rows": len(ibkr_recent),
                "ibkr_closed_session_rows": len(overlay),
                "alignment": alignment.to_dict(),
                "historical_reader": reader,
            })
        except Exception as exc:
            failures += 1
            results.append({
                "symbol": symbol,
                "status": "FAILED",
                "reason": f"{type(exc).__name__}:{exc}",
                "provider": provider_results.get(symbol, {}),
            })

    if reader == "stocks_ibkr_reference":
        for raw_symbol in data_cfg["symbols"]:
            symbol = str(raw_symbol).upper()
            frame = frames.get(symbol)
            if frame is None or frame.empty:
                failures += 1
                results.append({
                    "symbol": symbol,
                    "status": "FAILED",
                    "reason": "IBKR_HISTORICAL_SYMBOL_UNAVAILABLE",
                    "provider": provider_results.get(symbol, {}),
                })
                continue
            process(symbol, frame)
    else:
        try:
            with IBKRBrokerV241(cfg, readonly=True) as broker:
                for raw_symbol in data_cfg["symbols"]:
                    symbol = str(raw_symbol).upper()
                    try:
                        raw = broker.historical_bars(
                            symbol,
                            duration=duration,
                            bar_size=bar_size,
                            what_to_show=what_to_show,
                            use_rth=use_rth,
                        )
                    except Exception as exc:
                        failures += 1
                        results.append({
                            "symbol": symbol,
                            "status": "FAILED",
                            "reason": f"{type(exc).__name__}:{exc}",
                        })
                        continue
                    process(symbol, raw)
                broker_write_calls = int(broker.write_calls)
        except Exception as exc:
            return {
                "status": "FAILED",
                "failures": len(data_cfg.get("symbols", [])),
                "reason": f"IBKR_CURRENT_SESSION_BRIDGE_FAILED:{type(exc).__name__}:{exc}",
                "history_seeded": seeded,
                "history": history_result,
                "symbols": results,
                "broker_write_calls": broker_write_calls,
                "execution_authority": "NONE",
            }

    if broker_write_calls != 0:
        return {
            "status": "FAILED",
            "failures": len(data_cfg.get("symbols", [])),
            "reason": "READONLY_IBKR_DATA_BRIDGE_RECORDED_WRITE_CALLS",
            "history_seeded": seeded,
            "history": history_result,
            "symbols": results,
            "broker_write_calls": broker_write_calls,
            "execution_authority": "NONE",
        }

    all_fresh = (
        failures == 0
        and len(results) == len(data_cfg.get("symbols", []))
        and all(
            row.get("status") == "SUCCEEDED"
            and bool(row.get("freshness", {}).get("passed"))
            for row in results
        )
    )
    return {
        "status": "SUCCEEDED" if all_fresh else "FAILED",
        "failures": failures if failures else (0 if all_fresh else len(data_cfg.get("symbols", []))),
        "history_seeded": seeded,
        "history": history_result,
        "symbols": results,
        "broker_write_calls": broker_write_calls,
        "all_symbols_fresh": all_fresh,
        "historical_reader": reader,
        "execution_authority": "NONE",
    }

