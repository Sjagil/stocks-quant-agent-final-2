from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def load_proposals(root: str | Path) -> list[dict[str, Any]]:
    path = Path(root) / "artifacts/research_runtime/portfolio_decision_v2_7/proposals.csv"
    if not path.is_file():
        return []
    frame = pd.read_csv(path)
    if frame.empty:
        return []
    return frame.to_dict(orient="records")


def eligible_buy_rows(root: str | Path, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    e = cfg["eligibility"]
    for row in load_proposals(root):
        if str(row.get("decision", "")).upper() != "BUY_NEW":
            continue
        if e.get("require_shariah_verified", True) and not _bool(row.get("shariah_verified", False)):
            continue
        if e.get("require_fresh_entry_trigger", True) and not _bool(row.get("fresh_entry_trigger", False)):
            continue
        if e.get("require_no_proposal_blockers", True) and str(row.get("blockers", "") or "").strip():
            continue
        rows.append(row)
    rows.sort(key=lambda x: float(x.get("conviction", 0) or 0), reverse=True)
    return rows


def position_state_map(root: str | Path) -> dict[str, bool]:
    out = {}
    for row in load_proposals(root):
        symbol = str(row.get("symbol", "")).upper()
        if symbol:
            out[symbol] = _bool(row.get("active_position_state", False))
    return out
