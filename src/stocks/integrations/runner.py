from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .contracts import IntegrationState, WorkerRequest, WorkerResponse
from .registry import IntegrationRegistry


class IntegrationRunError(RuntimeError):
    pass


_SENSITIVE_EXACT = {"token", "access_token", "auth_token", "bearer_token", "password", "passwd", "secret", "credential", "credentials"}


def _looks_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return (
        normalized in _SENSITIVE_EXACT
        or "api_key" in normalized
        or "apikey" in normalized
        or normalized.endswith("_token")
        or normalized.endswith("_secret")
        or normalized.endswith("_password")
        or normalized.endswith("_credential")
    )


def _find_sensitive_payload_keys(value: Any, prefix: str = "payload") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            child_prefix = f"{prefix}.{key}"
            if _looks_sensitive_key(key_text) and child not in (None, "", False):
                hits.append(child_prefix)
            hits.extend(_find_sensitive_payload_keys(child, child_prefix))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            hits.extend(_find_sensitive_payload_keys(child, f"{prefix}[{index}]"))
    return hits


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = Path(handle.name)
    tmp.replace(path)


class IntegrationRunner:
    """Subprocess boundary for isolated third-party research engines.

    No external framework is imported into the main process. Requests and responses
    are versioned JSON contracts, while larger datasets move through Parquet files.
    """

    def __init__(self, registry: IntegrationRegistry) -> None:
        self.registry = registry

    def _environment(self, name: str) -> dict[str, str]:
        spec = self.registry.get(name)
        keys = set(spec.inherit_env) | set(spec.pass_env)
        env = {key: value for key in keys if (value := self.registry.environment_value(key)) is not None}
        env.setdefault("PYTHONUNBUFFERED", "1")
        env.setdefault("MPLBACKEND", "Agg")
        env.setdefault("TOKENIZERS_PARALLELISM", "false")
        env["STOCKS_INTEGRATION_NAME"] = name
        return env

    def run(
        self,
        name: str,
        action: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout_seconds: int | None = None,
        raise_on_error: bool = False,
    ) -> WorkerResponse:
        spec = self.registry.get(name)
        payload = dict(payload or {})
        sensitive_keys = _find_sensitive_payload_keys(payload)
        if sensitive_keys:
            response = WorkerResponse(
                integration=name,
                action=action,
                request_id="secret-rejected",
                state=IntegrationState.ERROR,
                error="secrets must be passed through the integration environment allow-list, not persisted in payload JSON: "
                + ", ".join(sensitive_keys),
            )
            if raise_on_error:
                raise IntegrationRunError(response.error or "secret-bearing payload rejected")
            return response
        if spec.capabilities and action not in spec.capabilities:
            response = WorkerResponse(
                integration=name,
                action=action,
                request_id="unsupported",
                state=IntegrationState.ERROR,
                error=f"action {action!r} is not enabled for integration {name!r}",
            )
            if raise_on_error:
                raise IntegrationRunError(response.error or "unsupported integration action")
            return response
        if not spec.enabled:
            response = WorkerResponse(
                integration=name,
                action=action,
                request_id="disabled",
                state=IntegrationState.UNAVAILABLE,
                error="integration is disabled",
            )
            if raise_on_error:
                raise IntegrationRunError(response.error or "integration unavailable")
            return response

        issues = self.registry.static_issues(name)
        blocking = tuple(x for x in issues if not x.startswith("repo_missing:"))
        if blocking:
            response = WorkerResponse(
                integration=name,
                action=action,
                request_id="unavailable",
                state=IntegrationState.UNAVAILABLE,
                error="; ".join(blocking),
                warnings=tuple(x for x in issues if x not in blocking),
            )
            if raise_on_error:
                raise IntegrationRunError(response.error or "integration unavailable")
            return response

        run_root = self.registry.artifact_root
        run_root.mkdir(parents=True, exist_ok=True)
        request = WorkerRequest(
            integration=name,
            action=action,
            payload=payload,
            context={
                "project_root": str(self.registry.project_root),
                "repo_path": str(spec.repo) if spec.repo else None,
                "artifact_root": str(run_root),
                "configured_capabilities": list(spec.capabilities),
                "integration_config_sha256": self.registry.config_sha256,
                "git": self.registry.git_state(name),
            },
        )
        run_dir = run_root / request.request_id
        run_dir.mkdir(parents=True, exist_ok=False)
        request_path = run_dir / "request.json"
        response_path = run_dir / "response.json"
        stdout_path = run_dir / "stdout.log"
        stderr_path = run_dir / "stderr.log"
        _write_json_atomic(request_path, request.to_dict())

        command = [
            str(spec.python),
            str(spec.worker),
            "--request",
            str(request_path),
            "--response",
            str(response_path),
            "--artifact-dir",
            str(run_dir),
        ]
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=self.registry.project_root,
                env=self._environment(name),
                capture_output=True,
                text=True,
                timeout=timeout_seconds or spec.timeout_seconds,
                check=False,
            )
            stdout_path.write_text(completed.stdout or "", encoding="utf-8")
            stderr_path.write_text(completed.stderr or "", encoding="utf-8")
        except subprocess.TimeoutExpired as exc:
            stdout_path.write_text(_coerce_text(exc.stdout), encoding="utf-8")
            stderr_path.write_text(_coerce_text(exc.stderr), encoding="utf-8")
            response = WorkerResponse(
                integration=name,
                action=action,
                request_id=request.request_id,
                state=IntegrationState.ERROR,
                error=f"worker timed out after {timeout_seconds or spec.timeout_seconds}s",
            )
            _write_json_atomic(response_path, response.to_dict())
            _write_json_atomic(
                run_dir / "run_manifest.json",
                {
                    "integration": name,
                    "action": action,
                    "request_id": request.request_id,
                    "command": command,
                    "timed_out": True,
                    "duration_seconds": time.monotonic() - started,
                    "state": response.state.value,
                    "ok": False,
                    "git": self.registry.git_state(name),
                    "integration_config_sha256": self.registry.config_sha256,
                    "protocol_version": self.registry.protocol_version,
                    "stdout": str(stdout_path),
                    "stderr": str(stderr_path),
                },
            )
            if raise_on_error:
                raise IntegrationRunError(response.error or "worker timeout") from exc
            return response

        if not response_path.exists():
            message = f"worker exited {completed.returncode} without a response; see {stderr_path}"
            response = WorkerResponse(
                integration=name,
                action=action,
                request_id=request.request_id,
                state=IntegrationState.ERROR,
                error=message,
            )
            _write_json_atomic(response_path, response.to_dict())
        else:
            try:
                response = WorkerResponse.from_dict(json.loads(response_path.read_text(encoding="utf-8")))
            except Exception as exc:
                response = WorkerResponse(
                    integration=name,
                    action=action,
                    request_id=request.request_id,
                    state=IntegrationState.ERROR,
                    error=f"invalid worker response: {exc}",
                )

        if response.request_id != request.request_id or response.integration != name or response.action != action:
            response = WorkerResponse(
                integration=name,
                action=action,
                request_id=request.request_id,
                state=IntegrationState.ERROR,
                error="worker response does not match request identity",
            )
        elif completed.returncode != 0 and response.ok:
            response = WorkerResponse(
                integration=name,
                action=action,
                request_id=request.request_id,
                state=IntegrationState.ERROR,
                error=f"worker returned exit code {completed.returncode} despite an OK response",
                warnings=response.warnings,
            )
        elif response.artifacts:
            bad_artifacts: list[str] = []
            for artifact in response.artifacts:
                artifact_path = Path(artifact.path).expanduser().resolve()
                if not artifact_path.is_relative_to(run_dir.resolve()) or not artifact_path.exists():
                    bad_artifacts.append(str(artifact_path))
            if bad_artifacts:
                response = WorkerResponse(
                    integration=name,
                    action=action,
                    request_id=request.request_id,
                    state=IntegrationState.ERROR,
                    error="worker returned invalid/out-of-run artifact paths: " + ", ".join(bad_artifacts),
                )

        manifest = {
            "integration": name,
            "action": action,
            "request_id": request.request_id,
            "command": command,
            "returncode": completed.returncode,
            "duration_seconds": time.monotonic() - started,
            "state": response.state.value,
            "ok": response.ok,
            "git": self.registry.git_state(name),
            "integration_config_sha256": self.registry.config_sha256,
            "protocol_version": self.registry.protocol_version,
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        }
        _write_json_atomic(run_dir / "run_manifest.json", manifest)

        if raise_on_error and not response.ok:
            raise IntegrationRunError(response.error or f"{name}:{action} failed")
        return response

    def health(self, name: str) -> WorkerResponse:
        return self.run(name, "health")

    def health_all(self) -> dict[str, WorkerResponse]:
        return {name: self.health(name) for name in self.registry.names(enabled_only=True)}
