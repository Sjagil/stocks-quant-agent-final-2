from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .context_v2_43 import apply_context_policy_v243
from .market_context_pipeline_v2_43 import load_latest_snapshot_v243


def _load_agent_shadow(root: Path) -> dict[str, Any] | None:
    path = root / "artifacts/research_runtime/agent_shadow_v2_42/latest.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if bool(data.get("direct_broker_control", False)):
        raise ValueError("RL_DIRECT_BROKER_CONTROL_MUST_REMAIN_FALSE")
    return data


def apply_portfolio_context_v243(
    root: str | Path,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    root = Path(root).resolve()
    proposal_path = root / "artifacts/research_runtime/portfolio_decision_v2_7/proposals.csv"
    if not proposal_path.is_file():
        raise FileNotFoundError(proposal_path)
    proposals = pd.read_csv(proposal_path)
    snapshot = load_latest_snapshot_v243(root, cfg)
    contextual = apply_context_policy_v243(
        proposals,
        snapshot=snapshot,
        cfg=cfg,
        agent_shadow=_load_agent_shadow(root),
    )

    artifact_root = root / cfg.get("artifact_root", "artifacts/production_runtime_v2_43")
    artifact_root.mkdir(parents=True, exist_ok=True)
    output = artifact_root / "contextual_proposals.csv"
    contextual.to_csv(output, index=False)

    archive = artifact_root / "decision_archive"
    archive.mkdir(parents=True, exist_ok=True)
    archive_path = archive / f"{snapshot['snapshot_id']}.csv"
    if archive_path.exists():
        old = pd.read_csv(archive_path)
        if old.to_csv(index=False) != contextual.to_csv(index=False):
            raise RuntimeError("IMMUTABLE_CONTEXT_DECISION_ARCHIVE_CONFLICT")
    else:
        contextual.to_csv(archive_path, index=False)

    changed = int(
        (
            contextual.get("decision_before_context", pd.Series(dtype=str)).astype(str)
            != contextual.get("decision_after_context", pd.Series(dtype=str)).astype(str)
        ).sum()
    ) if not contextual.empty else 0
    blocked_buys = int(
        (
            contextual.get("decision_before_context", pd.Series(dtype=str)).astype(str).eq("BUY_NEW")
            & contextual.get("decision_after_context", pd.Series(dtype=str)).astype(str).ne("BUY_NEW")
        ).sum()
    ) if not contextual.empty else 0

    audit = {
        "schema": "contextual_portfolio_v2_43",
        "status": "SUCCEEDED",
        "snapshot_id": snapshot["snapshot_id"],
        "decision_cutoff": snapshot["decision_cutoff"],
        "proposal_rows": len(contextual),
        "decision_changed_rows": changed,
        "context_blocked_buy_rows": blocked_buys,
        "buy_new_after_context": int(
            contextual.get("decision_after_context", pd.Series(dtype=str))
            .astype(str).eq("BUY_NEW").sum()
        ) if not contextual.empty else 0,
        "output": str(output),
        "archive": str(archive_path),
        "ppo_weight": 0.0,
        "sac_mode": "SHADOW_CONTEXT_ONLY",
        "rl_direct_broker_control": False,
        "execution_authority": "NONE",
        "order_calls": 0,
    }
    (artifact_root / "context_policy_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return audit


__all__ = ["apply_portfolio_context_v243"]
