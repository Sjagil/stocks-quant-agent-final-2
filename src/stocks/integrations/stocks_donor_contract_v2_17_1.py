from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml


CONFIG_PATH = Path("config/stocks_donor_integration_v2_17_1.yaml")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(repo: Path, *args: str) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
    except Exception:
        return None


ALLOWED_LOCAL_UNTRACKED = frozenset(
    {
        "requirements.macos.lock.txt",
    }
)


def classify_donor_worktree_status(porcelain: str | None) -> dict[str, Any]:
    raw = str(porcelain or "")
    lines = [
        line
        for line in raw.splitlines()
        if line.strip()
    ]

    allowed = []
    unexpected = []
    for line in lines:
        if line.startswith("?? "):
            relative = line[3:].strip()
            if relative in ALLOWED_LOCAL_UNTRACKED:
                allowed.append(relative)
                continue
        unexpected.append(line)

    return {
        "raw_clean": not lines,
        "clean_for_contract": not unexpected,
        "allowed_local_untracked": sorted(set(allowed)),
        "unexpected_status_lines": unexpected,
    }

def _source_audit(repo: Path, spec: dict[str, Any]) -> dict[str, Any]:
    relative = str(spec["path"])
    path = repo / relative
    exists = path.is_file()
    text = path.read_text(encoding="utf-8", errors="replace") if exists else ""
    required = [str(value) for value in spec.get("required_markers", [])]
    missing = [marker for marker in required if marker not in text]
    return {
        "path": relative,
        "phase": spec.get("phase"),
        "reuse_mode": spec.get("reuse_mode"),
        "exists": exists,
        "sha256": _sha256(path) if exists else None,
        "required_markers": required,
        "missing_markers": missing,
        "contract_ready": bool(exists and not missing),
    }


def _quarantine_audit(repo: Path, spec: dict[str, Any]) -> dict[str, Any]:
    relative = str(spec["path"])
    path = repo / relative
    exists = path.is_file()
    text = path.read_text(encoding="utf-8", errors="replace") if exists else ""
    markers = [str(value) for value in spec.get("forbidden_for_direct_reuse", [])]
    present = [marker for marker in markers if marker in text]
    return {
        "path": relative,
        "reason": str(spec.get("reason") or ""),
        "exists": exists,
        "sha256": _sha256(path) if exists else None,
        "forbidden_markers": markers,
        "detected_forbidden_markers": present,
        "direct_reuse_allowed": False,
        "quarantine_enforced": True,
    }


def _active_worker_audit(root: Path) -> list[dict[str, Any]]:
    specs = (
        (
            "stocks_reference",
            "scripts/workers/stocks_reference_worker.py",
            ("stocks.news", "stocks.screener", "sec_overlay", "orderflow"),
        ),
        (
            "stocks_context_reference",
            "scripts/workers/stocks_context_reference_worker.py",
            ("discovery_context", "market_context"),
        ),
        (
            "stocks_ibkr_reference",
            "scripts/workers/stocks_ibkr_reference_worker.py",
            (
                "broker_snapshot_read_only",
                "capture_snapshot",
                "derive_economic_account_state",
                "write_total",
                "execution_authority",
            ),
        ),
    )
    rows = []
    for integration, relative, markers in specs:
        path = root / relative
        exists = path.is_file()
        text = path.read_text(encoding="utf-8", errors="replace") if exists else ""
        missing = [marker for marker in markers if marker not in text]
        rows.append(
            {
                "integration": integration,
                "worker": relative,
                "exists": exists,
                "sha256": _sha256(path) if exists else None,
                "required_markers": list(markers),
                "missing_markers": missing,
                "active_contract_ready": bool(exists and not missing),
            }
        )
    return rows


def _domain_inventory(repo: Path) -> dict[str, Any]:
    domains = {}
    for name, relative in (
        ("portfolio", "src/stocks/portfolio"),
        ("ibkr", "src/stocks/ibkr"),
        ("research", "src/stocks/research"),
        ("news", "src/stocks/news"),
        ("screener", "src/stocks/screener"),
        ("microstructure", "src/stocks/microstructure"),
        ("live", "src/stocks/live"),
        ("auto_paper", "src/stocks/auto_paper"),
        ("capital", "src/stocks/capital"),
        ("quant_platform", "src/stocks/quant_platform"),
    ):
        path = repo / relative
        files = (
            sorted(
                str(item.relative_to(repo))
                for item in path.rglob("*.py")
                if item.is_file()
            )
            if path.is_dir()
            else []
        )
        domains[name] = {
            "path": relative,
            "exists": path.is_dir(),
            "python_files": len(files),
            "sample": files[:30],
        }
    return domains


def _manifest_hash(payload: dict[str, Any]) -> str:
    stable = {
        "upstream_commit": payload.get("upstream_commit"),
        "approved_sources": [
            {
                "path": row["path"],
                "sha256": row["sha256"],
                "reuse_mode": row["reuse_mode"],
            }
            for row in payload.get("approved_sources", [])
        ],
        "quarantine": [
            {
                "path": row["path"],
                "sha256": row["sha256"],
                "reason": row["reason"],
            }
            for row in payload.get("quarantine", [])
        ],
        "active_workers": [
            {
                "integration": row["integration"],
                "sha256": row["sha256"],
            }
            for row in payload.get("active_workers", [])
        ],
    }
    encoded = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_stocks_donor_contract(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    config_path = root / CONFIG_PATH
    if not config_path.is_file():
        raise FileNotFoundError(config_path)

    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    donor = root / str(config["upstream"]["local_path"])
    if not donor.is_dir():
        return {
            "schema": "stocks_donor_contract_v2_17_1",
            "status": "NO_GO",
            "blockers": ["STOCKS_DONOR_REPOSITORY_MISSING"],
            "execution_authority": "NONE",
            "broker_calls": 0,
            "order_calls": 0,
        }

    origin = _git(donor, "remote", "get-url", "origin") or ""
    commit = _git(donor, "rev-parse", "HEAD")
    porcelain = _git(donor, "status", "--porcelain")
    worktree = classify_donor_worktree_status(porcelain)
    clean = bool(worktree["raw_clean"])
    clean_for_contract = bool(worktree["clean_for_contract"])
    upstream_match = "Sjagil/Stocks" in origin.replace("\\", "/")

    approved = [
        _source_audit(donor, spec)
        for spec in config.get("approved_architecture_sources", [])
    ]
    quarantined = [
        _quarantine_audit(donor, spec)
        for spec in config.get("quarantine", [])
    ]
    active_workers = _active_worker_audit(root)

    portfolio_feature_rows = []
    for relative in config.get("portfolio_feature_sources", []):
        path = donor / str(relative)
        portfolio_feature_rows.append(
            {
                "path": str(relative),
                "exists": path.is_file(),
                "sha256": _sha256(path) if path.is_file() else None,
            }
        )

    blockers: list[str] = []
    if not upstream_match:
        blockers.append("STOCKS_DONOR_UPSTREAM_MISMATCH")
    if not clean_for_contract:
        blockers.append("STOCKS_DONOR_WORKTREE_DIRTY")
    if not commit:
        blockers.append("STOCKS_DONOR_COMMIT_UNAVAILABLE")

    for row in approved:
        if not row["exists"]:
            blockers.append("DONOR_SOURCE_MISSING:" + row["path"])
        if row["missing_markers"]:
            blockers.append(
                "DONOR_CONTRACT_MARKER_MISSING:"
                + row["path"]
                + ":"
                + ",".join(row["missing_markers"])
            )

    for row in active_workers:
        if not row["active_contract_ready"]:
            blockers.append(
                "ACTIVE_DONOR_WORKER_CONTRACT_INCOMPLETE:" + row["integration"]
            )

    policy = dict(config.get("policy") or {})
    required_policy = {
        "whole_shares_only": True,
        "fractional_shares_allowed": False,
        "fixed_euro_order_cap": False,
        "external_donor_broker_writes": False,
        "automatic_live_promotion": False,
        "execution_authority": "NONE",
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            blockers.append(f"DONOR_POLICY_MISMATCH:{key}")

    if policy.get("canonical_broker_writer") != "stocks.live.service.live_submit_authorized":
        blockers.append("CANONICAL_WRITER_MISMATCH")

    payload = {
        "schema": "stocks_donor_contract_v2_17_1",
        "status": "GO" if not blockers else "NO_GO",
        "repository": str(donor),
        "upstream_origin": origin,
        "upstream_match": upstream_match,
        "upstream_commit": commit,
        "worktree_clean": clean,
        "worktree_clean_for_contract": clean_for_contract,
        "allowed_local_untracked": worktree["allowed_local_untracked"],
        "unexpected_status_lines": worktree["unexpected_status_lines"],
        "contract_revision": "v2.17.3",
        "approved_sources": approved,
        "portfolio_feature_sources": portfolio_feature_rows,
        "quarantine": quarantined,
        "active_workers": active_workers,
        "domain_inventory": _domain_inventory(donor),
        "roadmap_mapping": config.get("roadmap_mapping", {}),
        "policy": policy,
        "blockers": sorted(set(blockers)),
        "direct_donor_package_import": False,
        "donor_live_writer_imported": False,
        "donor_broker_writes": 0,
        "canonical_broker_writer": policy.get("canonical_broker_writer"),
        "whole_shares_only": True,
        "fractional_shares_allowed": False,
        "fixed_euro_order_cap": False,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    payload["manifest_hash"] = _manifest_hash(payload)
    return payload


def write_stocks_donor_contract(
    project_root: str | Path,
    output: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    payload = build_stocks_donor_contract(root)
    target = (
        Path(output).resolve()
        if output is not None
        else root / "artifacts/research_runtime/stocks_donor_integration_v2_17_1/audit.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
