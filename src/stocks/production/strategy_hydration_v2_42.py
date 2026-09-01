from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.data.canonical import CanonicalMetadata, canonicalize_ohlcv, read_canonical_parquet, write_canonical_parquet
from stocks.research.dynamic_universe_generalization import discover_interval_sources
from .current_session_alignment_v2_42 import align_ibkr_rth_to_eodhd_grid_v242
from .current_session_data_v2_41_2 import cross_provider_close_check, merge_overlay
from .freshness_v2_41 import check_file_freshness
from .ibkr_adapter_v2_41 import IBKRBrokerV241
from .ibkr_historical_v2_43_1 import fetch_historical_batch_v2431


def selected_forward_symbols_v242(root: Path, maximum_symbols: int = 50) -> list[str]:
    matrix_path = root / "artifacts/research_runtime/candidate_strategy_matrix/matrix.csv"
    roster_path = root / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    if not matrix_path.is_file() or not roster_path.is_file():
        return []
    matrix = pd.read_csv(matrix_path)
    roster = pd.read_csv(roster_path)
    if matrix.empty or roster.empty or "hypothesis_id" not in matrix.columns or "hypothesis_id" not in roster.columns:
        return []
    if "roster_status" in roster.columns:
        roster = roster.loc[roster["roster_status"].astype(str) == "BROADLY_VALIDATED_FINALIST"]
    ids = set(roster["hypothesis_id"].astype(str))
    selected = matrix.loc[matrix["hypothesis_id"].astype(str).isin(ids)].copy()
    if "applicability_score" in selected.columns:
        selected = selected.sort_values("applicability_score", ascending=False)
    symbols = []
    for value in selected.get("symbol", pd.Series(dtype=str)).dropna().astype(str).str.upper():
        if value not in symbols:
            symbols.append(value)
        if len(symbols) >= int(maximum_symbols):
            break
    return symbols


def _base_candidates(root: Path, symbol: str) -> list[Path]:
    name = f"{symbol.upper()}_1h.parquet"
    return [root / rel / name for rel in ("data/adjusted", "data/derived", "data/processed", "data/canonical/provider_fabric")]


def _seed_base(root: Path, symbol: str, target: Path) -> Path:
    if target.is_file():
        return target
    for source in _base_candidates(root, symbol):
        if not source.is_file():
            continue
        try:
            frame, meta = read_canonical_parquet(source, verify_hash=False, verify_metadata=False)
        except Exception:
            raw = pd.read_parquet(source)
            if "date" in raw.columns and "timestamp" not in raw.columns:
                raw = raw.rename(columns={"date": "timestamp"})
            frame = canonicalize_ohlcv(raw, drop_duplicate_timestamps=True, drop_missing_required=True)
            meta = None
        source_name = str((meta or {}).get("source") or "LEGACY_CANONICAL")
        if "IBKR" in source_name.upper() and source.parent.name == "provider_fabric":
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        metadata = CanonicalMetadata(
            symbol=symbol.upper(), timeframe="1h", source=source_name,
            exchange=str((meta or {}).get("exchange") or "US"),
            asset_type=(meta or {}).get("asset_type"), currency=(meta or {}).get("currency") or "USD",
            adjustment=str((meta or {}).get("adjustment") or "raw"),
            provenance={**((meta or {}).get("provenance") or {}), "strategy_base_seed_v2_42": True, "seeded_from": str(source)},
        )
        write_canonical_parquet(frame, target, metadata, extra_metadata={"seeded_from": str(source)})
        return target
    raise FileNotFoundError(f"no non-IBKR canonical 1h base source for {symbol}")


def hydrate_strategy_candidates_v242(root: str | Path, production_cfg: dict[str, Any], intelligence_cfg: dict[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    hcfg = intelligence_cfg["strategy_hydration"]
    symbols = selected_forward_symbols_v242(root, int(hcfg.get("maximum_symbols", 50)))
    if not symbols:
        return {
            "status": "FAILED",
            "reason": "NO_SELECTED_FORWARD_SYMBOLS",
            "symbols": [],
            "execution_authority": "NONE",
        }

    provider_root = root / production_cfg["data"]["provider_root"]
    base_root = root / hcfg.get(
        "base_history_root",
        "data/canonical/production_history/strategy_base",
    )
    now = pd.Timestamp.now(tz="UTC")
    min_overlap = int(hcfg.get("minimum_cross_provider_overlap_bars", 10))
    max_bps = float(hcfg.get("maximum_cross_provider_close_disagreement_bps", 50.0))
    tolerance = float(production_cfg["data"].get("freshness_tolerance_minutes", 150))
    source_minutes = int(production_cfg["data"].get("ibkr_source_bar_minutes", 30))
    target_minutes = int(production_cfg["data"].get("production_target_bar_minutes", 60))
    reader = str(production_cfg["data"].get("ibkr_historical_reader", "legacy")).strip()

    results = []
    failures = 0
    write_calls = 0
    frames: dict[str, pd.DataFrame] = {}
    provider_results: dict[str, dict[str, Any]] = {}

    if reader == "stocks_ibkr_reference":
        try:
            batch = fetch_historical_batch_v2431(
                root,
                symbols,
                duration=str(production_cfg["data"].get("ibkr_history_duration", "5 D")),
                bar_size=str(production_cfg["data"].get("ibkr_history_bar_size", "30 mins")),
                what_to_show=str(production_cfg["data"].get("ibkr_history_what_to_show", "TRADES")),
                use_rth=bool(production_cfg["data"].get("ibkr_history_use_rth", True)),
            )
            frames = batch.frames
            provider_results = batch.symbol_results
            write_calls = int(batch.broker_write_calls)
        except Exception as exc:
            return {
                "status": "FAILED",
                "reason": f"IBKR_HISTORICAL_READER_FAILED:{type(exc).__name__}:{exc}",
                "selected_symbols": symbols,
                "successes": 0,
                "failures": len(symbols),
                "symbols": [],
                "broker_write_calls": 0,
                "execution_authority": "NONE",
            }

    def process(symbol: str, raw: pd.DataFrame) -> None:
        nonlocal failures
        try:
            base_path = _seed_base(root, symbol, base_root / f"{symbol}_1h.parquet")
            base, base_meta = read_canonical_parquet(
                base_path,
                verify_hash=False,
                verify_metadata=False,
            )
            aligned, alignment = align_ibkr_rth_to_eodhd_grid_v242(
                raw,
                now=now,
                calendar_name=str(production_cfg["data"].get("market_calendar", "NYSE")),
                source_bar_minutes=source_minutes,
                target_bar_minutes=target_minutes,
                close_lag_seconds=int(production_cfg["data"].get("bar_close_lag_seconds", 120)),
            )
            if aligned.empty:
                raise ValueError("IBKR_ALIGNMENT_NO_CLOSED_BARS")
            cross = cross_provider_close_check(
                base,
                aligned,
                minimum_overlap_bars=min_overlap,
                maximum_close_disagreement_bps=max_bps,
            )
            if not cross.passed:
                raise ValueError(
                    f"{cross.reason}: overlap={cross.overlap_bars} "
                    f"max_bps={cross.max_close_disagreement_bps}"
                )
            overlay = aligned.loc[aligned.index > base.index.max()].copy()
            if overlay.empty:
                latest_session_date = aligned.index.max().date()
                overlay = aligned.loc[aligned.index.date == latest_session_date].copy()
            merged = merge_overlay(base, overlay)
            target = provider_root / f"{symbol}_1h.parquet"
            meta = CanonicalMetadata(
                symbol=symbol,
                timeframe="1h",
                source="STRATEGY_BASE+IBKR30M_ALIGNED",
                exchange=str((base_meta or {}).get("exchange") or "US"),
                asset_type=(base_meta or {}).get("asset_type"),
                currency=(base_meta or {}).get("currency") or "USD",
                adjustment=str((base_meta or {}).get("adjustment") or "raw"),
                provenance={
                    **((base_meta or {}).get("provenance") or {}),
                    "strategy_hydration_v2_43": True,
                    "base_path": str(base_path),
                    "historical_reader": reader,
                },
            )
            write_canonical_parquet(
                merged,
                target,
                meta,
                extra_metadata={
                    "cross_provider": cross.to_dict(),
                    "alignment": alignment.to_dict(),
                },
            )
            fresh = check_file_freshness(
                symbol,
                target,
                now=now,
                calendar_name=str(production_cfg["data"].get("market_calendar", "NYSE")),
                tolerance_minutes=tolerance,
            )
            if not fresh.passed:
                raise ValueError(f"STRATEGY_SOURCE_STALE:{fresh.reason}")
            results.append({
                "symbol": symbol,
                "status": "SUCCEEDED",
                "freshness": fresh.to_dict(),
                "cross_provider": cross.to_dict(),
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
        for symbol in symbols:
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
        with IBKRBrokerV241(production_cfg, readonly=True) as broker:
            for symbol in symbols:
                try:
                    raw = broker.historical_bars(
                        symbol,
                        duration="5 D",
                        bar_size="30 mins",
                        what_to_show="TRADES",
                        use_rth=True,
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
            write_calls = int(broker.write_calls)

    require_all = bool(hcfg.get("require_all_selected_symbols_fresh", True))
    passed = write_calls == 0 and (
        failures == 0 if require_all else failures < len(symbols)
    )
    return {
        "status": "SUCCEEDED" if passed else "FAILED",
        "selected_symbols": symbols,
        "successes": len(symbols) - failures,
        "failures": failures,
        "symbols": results,
        "broker_write_calls": write_calls,
        "historical_reader": reader,
        "execution_authority": "NONE",
    }

