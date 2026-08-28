from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .evidence_production_contracts_v2_39_3 import ProductionInputAuditV2393
from .oos_observation_validation_v2_39_3 import file_fingerprint, stable_hash


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype={"hypothesis_id": str})
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _hypothesis_id(entity_id: str) -> str:
    prefix = "STRATEGY:"
    if not str(entity_id).startswith(prefix):
        raise ValueError("factory replay supports STRATEGY entities only")
    return str(entity_id)[len(prefix):]


def audit_factory_replay_inputs(
    project_root: Path,
    entity: dict,
    *,
    config: dict,
) -> ProductionInputAuditV2393:
    entity_id = str(entity["entity_id"])
    hid = _hypothesis_id(entity_id)
    artifact_root = project_root / config.get("artifact_root", "artifacts/research_runtime/strategy_factory_1h")
    audit_path = artifact_root / "audit.json"
    selected_path = artifact_root / "fold_selected.csv"
    reasons: list[str] = []
    details: dict[str, Any] = {
        "artifact_root": str(artifact_root),
        "audit": file_fingerprint(audit_path),
        "fold_selected": file_fingerprint(selected_path),
    }
    audit = _read_json(audit_path)
    selected = _read_csv(selected_path)
    if not audit:
        reasons.append("FACTORY_AUDIT_MISSING")
    if selected.empty:
        reasons.append("FACTORY_FOLD_SELECTED_MISSING")
    selected_rows = selected.loc[selected.get("hypothesis_id", pd.Series(dtype=str)).astype(str) == hid] if not selected.empty and "hypothesis_id" in selected else pd.DataFrame()
    if config.get("require_selected_test_folds", True) and selected_rows.empty:
        reasons.append("NO_SELECTED_TEST_FOLDS")
    symbols = [str(x).upper() for x in audit.get("symbols", [])]
    sources = audit.get("sources", {}) if isinstance(audit.get("sources"), dict) else {}
    if not symbols:
        reasons.append("FACTORY_SYMBOLS_MISSING")
    missing_sources = [s for s in symbols if not sources.get(s) or not Path(str(sources.get(s))).is_file()]
    if missing_sources:
        reasons.append("FACTORY_SOURCE_DATA_MISSING:" + ",".join(missing_sources))
    metadata = entity.get("metadata", {}) or {}
    strategy = str(metadata.get("strategy") or "").strip()
    params_json = metadata.get("params_json")
    if not strategy:
        reasons.append("ENTITY_STRATEGY_MISSING")
    if not params_json:
        reasons.append("ENTITY_PARAMS_MISSING")
    details.update({
        "hypothesis_id": hid,
        "strategy": strategy,
        "selected_folds": sorted(pd.to_numeric(selected_rows.get("fold", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).unique().tolist()),
        "symbols": symbols,
        "source_paths": sources,
        "base_cost_bps_per_side": audit.get("base_cost_bps_per_side"),
        "fold_count": audit.get("fold_count"),
        "replay_purge_bars": int(config.get("replay_purge_bars", 42)),
    })
    return ProductionInputAuditV2393(
        entity_id=entity_id,
        adapter="STRATEGY_FACTORY_1H_REPLAY",
        status="READY" if not reasons else "BLOCKED",
        ready=not reasons,
        reasons=tuple(reasons),
        details=details,
    )


def _close(a, b, *, abs_tol: float, rel_tol: float) -> bool:
    try:
        aa = float(a); bb = float(b)
    except Exception:
        return False
    if not math.isfinite(aa) and not math.isfinite(bb):
        return True
    if not math.isfinite(aa) or not math.isfinite(bb):
        return False
    return math.isclose(aa, bb, abs_tol=abs_tol, rel_tol=rel_tol)


def replay_factory_oos(
    project_root: Path,
    entity: dict,
    *,
    config: dict,
) -> tuple[pd.DataFrame, dict]:
    input_audit = audit_factory_replay_inputs(project_root, entity, config=config)
    if not input_audit.ready:
        raise RuntimeError(";".join(input_audit.reasons))

    # Imports are deferred so audit-inputs remains usable even when optional research
    # dependencies are unavailable.
    from stocks.research.strategy_factory_1h import (
        OneHourHypothesis,
        build_feature_caches,
        contained_trades,
        eligible_1h_specs,
        evaluate_hypothesis,
        period_metrics,
        prepare_one_hour_frame,
    )
    from stocks.research.walkforward_splits import rolling_periods

    artifact_root = Path(input_audit.details["artifact_root"])
    audit = _read_json(artifact_root / "audit.json")
    selected = _read_csv(artifact_root / "fold_selected.csv")
    hid = input_audit.details["hypothesis_id"]
    selected = selected.loc[selected["hypothesis_id"].astype(str) == hid].copy()
    metadata = entity.get("metadata", {}) or {}
    strategy = str(metadata["strategy"])
    family = str(metadata.get("family") or entity.get("family") or "UNKNOWN")
    params = json.loads(str(metadata["params_json"])) if isinstance(metadata["params_json"], str) else dict(metadata["params_json"])
    horizon = str(metadata.get("horizon") or "UNKNOWN")

    specs = {s.name: s for s in eligible_1h_specs()}
    if strategy not in specs:
        raise RuntimeError("FACTORY_STRATEGY_NOT_REPLAYABLE")
    hypothesis = OneHourHypothesis(
        hypothesis_id=hid,
        strategy=strategy,
        family=family,
        horizon=horizon,
        params=params,
    )

    frames: dict[str, pd.DataFrame] = {}
    data_fingerprints: dict[str, dict] = {}
    for symbol in input_audit.details["symbols"]:
        path = Path(str(input_audit.details["source_paths"][symbol]))
        raw = pd.read_parquet(path)
        frame = prepare_one_hour_frame(raw, symbol)
        if len(frame) < 4000:
            raise RuntimeError(f"{symbol}:FACTORY_REPLAY_REQUIRES_4000_BARS")
        frames[symbol] = frame
        fp = file_fingerprint(path)
        fp.update({
            "rows": int(len(frame)),
            "first": str(frame["date"].min()),
            "last": str(frame["date"].max()),
        })
        data_fingerprints[symbol] = fp

    caches = build_feature_caches(frames)
    trades = evaluate_hypothesis(hypothesis, specs[strategy], frames, caches)
    anchor = str(audit.get("anchor_symbol") or ("SPY" if "SPY" in frames else next(iter(frames))))
    anchor_index = pd.DatetimeIndex(frames[anchor]["date"]).sort_values().drop_duplicates()
    fold_count = int(audit.get("fold_count") or max(2, int(selected["fold"].max())))
    purge_bars = int(config.get("replay_purge_bars", 42))
    folds = rolling_periods(anchor_index, hold_bars=purge_bars, requested_folds=fold_count)
    base_cost = float(audit.get("base_cost_bps_per_side", 3.0))
    abs_tol = float(config.get("metric_abs_tolerance", 1e-6))
    rel_tol = float(config.get("metric_rel_tolerance", 1e-5))

    replay_checks: list[dict] = []
    parts: list[pd.DataFrame] = []
    for row in selected.to_dict(orient="records"):
        fold_no = int(row["fold"])
        if fold_no < 1 or fold_no > len(folds):
            raise RuntimeError("FACTORY_SELECTED_FOLD_OUT_OF_RANGE")
        period = folds[fold_no - 1]["test"]
        metrics = period_metrics(trades, period, cost_bps_per_side=base_cost)
        checks = {
            "fold": fold_no,
            "test_trades": int(metrics["trades"]) == int(float(row.get("test_trades", -1))),
            "test_net_expectancy_bps": _close(metrics["net_expectancy_bps"], row.get("test_net_expectancy_bps"), abs_tol=abs_tol, rel_tol=rel_tol),
            "test_profit_factor": _close(metrics["profit_factor"], row.get("test_profit_factor"), abs_tol=abs_tol, rel_tol=rel_tol),
        }
        checks["passed"] = all(checks.values())
        replay_checks.append(checks)
        part = contained_trades(trades, period).copy()
        if not part.empty:
            part["fold"] = fold_no
            part["test_start"] = period[0]
            part["test_end"] = period[1]
            parts.append(part)

    if config.get("require_replay_metric_verification", True) and (not replay_checks or not all(x["passed"] for x in replay_checks)):
        raise RuntimeError("REPLAY_PROVENANCE_MISMATCH")

    observations = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    provenance = {
        "schema": "factory_oos_replay_provenance_v2_39_3",
        "entity_id": entity["entity_id"],
        "hypothesis_id": hid,
        "strategy": strategy,
        "params": params,
        "anchor_symbol": anchor,
        "fold_count": fold_count,
        "selected_folds": sorted(int(x) for x in selected["fold"].tolist()),
        "purge_bars": purge_bars,
        "base_cost_bps_per_side": base_cost,
        "replay_checks": replay_checks,
        "data_sources": data_fingerprints,
        "factory_audit": file_fingerprint(artifact_root / "audit.json"),
        "fold_selected": file_fingerprint(artifact_root / "fold_selected.csv"),
        "selection_rule": "TEST_OPENED_ONLY_AFTER_TRAIN_VALID_SELECTION",
        "execution_authority": "NONE",
    }
    provenance["provenance_hash"] = stable_hash(provenance)
    return observations, provenance


__all__ = ["audit_factory_replay_inputs", "replay_factory_oos"]
