from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .screener_v2_44 import production_screener_allows_symbol_v244


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _contextual_proposal_path_v242(root: Path) -> Path | None:
    path = root / "artifacts/production_runtime_v2_43/contextual_proposals.csv"
    pointer = root / "artifacts/production_runtime_v2_43/latest_snapshot_pointer.json"
    if not path.is_file() or not pointer.is_file():
        return None
    try:
        generated = pd.Timestamp(
            json.loads(pointer.read_text(encoding="utf-8")).get("decision_cutoff")
        )
        generated = (
            generated.tz_localize("UTC")
            if generated.tzinfo is None
            else generated.tz_convert("UTC")
        )
        age = (pd.Timestamp.now(tz="UTC") - generated).total_seconds()
        if age < 0 or age > 20 * 60:
            return None
    except Exception:
        return None
    return path


def _raw_proposal_path(root: Path) -> Path:
    return root / "artifacts/research_runtime/portfolio_decision_v2_7/proposals.csv"


def _read(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.is_file():
        return []
    frame = pd.read_csv(path)
    return [] if frame.empty else frame.to_dict(orient="records")


def load_proposals(root: str | Path) -> list[dict[str, Any]]:
    root = Path(root)
    contextual = _contextual_proposal_path_v242(root)
    return _read(contextual or _raw_proposal_path(root))


def _context_paper_ready(root: Path) -> bool:
    path = root / "artifacts/production_runtime_v2_43/context_readiness.json"
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(data.get("system_paper_ready")) and data.get("status") in {"SYSTEM_READY_FOR_PAPER", "READY_FOR_PAPER"}


def eligible_buy_rows(root: str | Path, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(root)
    contextual = _contextual_proposal_path_v242(root)
    if contextual is None or not _context_paper_ready(root):
        return []
    rows = []
    e = cfg["eligibility"]
    for row in _read(contextual):
        if str(row.get("decision_after_context") or row.get("decision") or "").upper() != "BUY_NEW":
            continue
        if not row.get("snapshot_id"):
            continue
        if _bool(row.get("rl_direct_broker_control", False)):
            continue
        if float(row.get("ppo_weight", 1.0) or 0.0) != 0.0:
            continue
        if e.get("require_shariah_verified", True) and not _bool(row.get("shariah_verified", False)):
            continue
        if e.get("require_fresh_entry_trigger", True) and not _bool(row.get("fresh_entry_trigger", False)):
            continue
        if e.get("require_no_proposal_blockers", True) and str(row.get("blockers", "") or "").strip():
            continue
        if e.get("require_current_screener_candidate", True):
            allowed, _ = production_screener_allows_symbol_v244(
                root,
                str(row.get("symbol") or ""),
            )
            if not allowed:
                continue
        rows.append(row)
    rows.sort(
        key=lambda x: float(x.get("adjusted_conviction", x.get("conviction", 0)) or 0),
        reverse=True,
    )
    return rows


def position_state_map(root: str | Path) -> dict[str, bool]:
    root = Path(root)
    rows = _read(_contextual_proposal_path_v242(root))
    if not rows:
        rows = _read(_raw_proposal_path(root))
    out = {}
    for row in rows:
        symbol = str(row.get("symbol", "")).upper()
        if symbol:
            out[symbol] = _bool(row.get("active_position_state", False))
    return out
