from __future__ import annotations

import json
from pathlib import Path

from _common import artifact_ref, run_worker


CAPABILITIES = ("health", "architecture_manifest", "capability_map")


def _project_root(request: dict) -> Path:
    raw = (request.get("context") or {}).get("project_root")
    if not raw:
        raise ValueError("project_root missing")
    root = Path(str(raw)).resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    return root


def _contract(request: dict) -> dict:
    root = _project_root(request)
    from stocks.integrations.stocks_donor_contract_v2_17_1 import (
        build_stocks_donor_contract,
    )
    return build_stocks_donor_contract(root)


def handle(request: dict, artifact_dir: Path) -> dict:
    action = str(request["action"])
    payload = _contract(request)

    if action == "health":
        return {
            "state": "OK" if payload["status"] == "GO" else "DEGRADED",
            "data": {
                "status": payload["status"],
                "upstream_commit": payload.get("upstream_commit"),
                "manifest_hash": payload.get("manifest_hash"),
                "worktree_clean": payload.get("worktree_clean"),
                "worktree_clean_for_contract": payload.get("worktree_clean_for_contract"),
                "blockers": payload.get("blockers", []),
                "capabilities": list(CAPABILITIES),
                "donor_broker_writes": 0,
                "execution_authority": "NONE",
            },
            "warnings": payload.get("blockers", []),
        }

    if action == "architecture_manifest":
        target = artifact_dir / "stocks_donor_architecture_manifest.json"
        target.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return {
            "state": "OK" if payload["status"] == "GO" else "DEGRADED",
            "data": payload,
            "artifacts": [artifact_ref(target, media_type="application/json")],
            "warnings": payload.get("blockers", []),
        }

    if action == "capability_map":
        return {
            "state": "OK" if payload["status"] == "GO" else "DEGRADED",
            "data": {
                "domain_inventory": payload["domain_inventory"],
                "roadmap_mapping": payload["roadmap_mapping"],
                "approved_sources": payload["approved_sources"],
                "quarantine": payload["quarantine"],
                "active_workers": payload["active_workers"],
                "execution_authority": "NONE",
            },
            "warnings": payload.get("blockers", []),
        }

    raise ValueError(f"unsupported Stocks donor action: {action}")


if __name__ == "__main__":
    run_worker(handle)
