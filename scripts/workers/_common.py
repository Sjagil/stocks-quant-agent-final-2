from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata as metadata
import json
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Callable

PROTOCOL_VERSION = "1.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    return parser.parse_args()


def load_request(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if str(raw.get("protocol_version")) != PROTOCOL_VERSION:
        raise ValueError(f"unsupported protocol: {raw.get('protocol_version')}")
    return raw


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")
        temp = Path(handle.name)
    temp.replace(path)


def artifact_ref(path: Path, *, media_type: str, rows: int | None = None, metadata_: dict[str, Any] | None = None) -> dict[str, Any]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return {
        "path": str(path),
        "media_type": media_type,
        "sha256": digest,
        "rows": rows,
        "metadata": metadata_ or {},
    }


def package_version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def import_probe(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        return {
            "module": module_name,
            "ok": True,
            "version": getattr(module, "__version__", None),
            "path": getattr(module, "__file__", None),
        }
    except Exception as exc:
        return {"module": module_name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def git_state(repo: str | Path | None) -> dict[str, Any]:
    if not repo:
        return {"available": False}
    root = Path(repo)
    if not (root / ".git").exists():
        return {"available": False, "path": str(root)}
    try:
        commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=10).stdout.strip()
        branch = subprocess.run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True, timeout=10).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True, check=True, timeout=10).stdout.strip())
        return {"available": True, "path": str(root), "commit": commit, "branch": branch, "dirty": dirty}
    except Exception as exc:
        return {"available": False, "path": str(root), "error": str(exc)}


def repo_catalog(repo: str | Path | None, patterns: tuple[str, ...]) -> dict[str, list[str]]:
    root = Path(repo) if repo else None
    output: dict[str, list[str]] = {}
    if root is None or not root.exists():
        return output
    for pattern in patterns:
        output[pattern] = sorted(str(p.relative_to(root)) for p in root.rglob(pattern))[:500]
    return output


def add_repo_src(repo: str | Path | None) -> None:
    if not repo:
        return
    root = Path(repo)
    for candidate in (root / "src", root):
        if candidate.exists():
            text = str(candidate)
            if text not in sys.path:
                sys.path.insert(0, text)


def base_health(request: dict[str, Any], *, distributions: tuple[str, ...], imports: tuple[str, ...], capabilities: tuple[str, ...]) -> dict[str, Any]:
    repo = (request.get("context") or {}).get("repo_path")
    probes = [import_probe(name) for name in imports]
    state = "OK" if all(item["ok"] for item in probes) else "DEGRADED"
    return {
        "state": state,
        "data": {
            "python": sys.version,
            "executable": sys.executable,
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
            "venv_active": sys.prefix != sys.base_prefix,
            "packages": {name: package_version(name) for name in distributions},
            "imports": probes,
            "repo": git_state(repo),
            "capabilities": list(capabilities),
        },
        "warnings": [item["error"] for item in probes if not item["ok"]],
    }


def response_for(request: dict[str, Any], *, state: str, data: dict[str, Any] | None = None, artifacts: list[dict[str, Any]] | None = None, warnings: list[str] | None = None, error: str | None = None) -> dict[str, Any]:
    return {
        "integration": request["integration"],
        "action": request["action"],
        "request_id": request["request_id"],
        "state": state,
        "data": data or {},
        "artifacts": artifacts or [],
        "warnings": warnings or [],
        "error": error,
        "protocol_version": PROTOCOL_VERSION,
    }


def run_worker(handler: Callable[[dict[str, Any], Path], dict[str, Any]]) -> None:
    args = parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    try:
        request = load_request(args.request)
        result = handler(request, args.artifact_dir)
        response = response_for(
            request,
            state=str(result.get("state") or "OK"),
            data=dict(result.get("data") or {}),
            artifacts=list(result.get("artifacts") or []),
            warnings=list(result.get("warnings") or []),
            error=result.get("error"),
        )
    except Exception as exc:
        request = locals().get("request") or {
            "integration": os.environ.get("STOCKS_INTEGRATION_NAME", "unknown"),
            "action": "unknown",
            "request_id": "unknown",
        }
        response = response_for(
            request,
            state="ERROR",
            error=f"{type(exc).__name__}: {exc}",
            data={"traceback": traceback.format_exc(limit=20)},
        )
    atomic_json(args.response, response)


def require_path(payload: dict[str, Any], key: str) -> Path:
    value = payload.get(key)
    if not value:
        raise ValueError(f"payload.{key} is required")
    path = Path(str(value)).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return path
