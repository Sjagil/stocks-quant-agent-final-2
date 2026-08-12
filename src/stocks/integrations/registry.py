from __future__ import annotations

import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from .contracts import IntegrationKind, IntegrationSpec, PROTOCOL_VERSION

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = value.strip().strip('"').strip("'")
    return values


def _expand_env(value: str, environment: Mapping[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key, default = match.group(1), match.group(2)
        actual = environment.get(key)
        if actual is not None and actual != "":
            return actual
        return default or ""

    expanded = _ENV_PATTERN.sub(repl, value)
    if expanded.startswith("~"):
        home = environment.get("HOME") or str(Path.home())
        expanded = home + expanded[1:]
    return expanded


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(x) for x in value)


def _resolve(root: Path, value: str | None, environment: Mapping[str, str]) -> Path | None:
    if not value:
        return None
    expanded = Path(_expand_env(value, environment))
    return expanded.resolve() if expanded.is_absolute() else (root / expanded).resolve()


def _resolve_executable(root: Path, value: str | None, environment: Mapping[str, str]) -> Path | None:
    """Return an absolute executable path without dereferencing virtualenv symlinks.

    Python virtual environments commonly expose ``bin/python`` as a symlink to the
    base interpreter. Calling ``Path.resolve()`` here would replace the venv path
    with that base interpreter path, causing the child process to lose its venv
    ``sys.prefix`` and all packages installed only inside the isolated environment.
    ``abspath`` normalizes the path while deliberately preserving the symlink.
    """
    if not value:
        return None
    expanded = Path(_expand_env(value, environment)).expanduser()
    candidate = expanded if expanded.is_absolute() else root / expanded
    return Path(os.path.abspath(os.fspath(candidate)))


@dataclass(frozen=True)
class RegistrySnapshot:
    protocol_version: str
    config_sha256: str | None
    specs: tuple[IntegrationSpec, ...]


class IntegrationRegistry:
    """Validated registry for external research engines.

    Paths are resolved once against the project root. Vendor repositories are never
    imported into the main interpreter by this class; isolated integrations are
    always addressed through their configured worker process.
    """

    def __init__(
        self,
        specs: Mapping[str, IntegrationSpec],
        *,
        project_root: Path,
        artifact_root: Path,
        protocol_version: str = PROTOCOL_VERSION,
        config_path: Path | None = None,
        config_sha256: str | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._specs = dict(specs)
        self.project_root = project_root.resolve()
        self.artifact_root = artifact_root.resolve()
        self.protocol_version = protocol_version
        self.config_path = config_path.resolve() if config_path else None
        self.config_sha256 = config_sha256
        self._environment = dict(environment or os.environ)

    @classmethod
    def load(cls, path: str | Path, *, project_root: str | Path | None = None) -> "IntegrationRegistry":
        config_path = Path(path).resolve()
        root = Path(project_root).resolve() if project_root else config_path.parent.parent.resolve()
        config_bytes = config_path.read_bytes()
        config_sha256 = hashlib.sha256(config_bytes).hexdigest()
        raw = yaml.safe_load(config_bytes.decode("utf-8")) or {}
        environment = {**_read_dotenv(root / ".env"), **dict(os.environ)}
        if int(raw.get("schema_version", 0)) != 1:
            raise ValueError("integrations config schema_version must be 1")
        protocol = str(raw.get("protocol_version") or PROTOCOL_VERSION)
        if protocol != PROTOCOL_VERSION:
            raise ValueError(f"unsupported integration protocol: {protocol}")

        defaults = dict(raw.get("defaults") or {})
        artifact_root = _resolve(root, str(raw.get("artifact_root") or "artifacts/integrations"), environment)
        assert artifact_root is not None
        if not artifact_root.is_relative_to(root):
            raise ValueError("artifact_root must stay inside the project root")
        specs: dict[str, IntegrationSpec] = {}
        for name, item_raw in dict(raw.get("integrations") or {}).items():
            item = {**defaults, **dict(item_raw or {})}
            python = _resolve_executable(root, str(item.get("python") or ""), environment)
            worker = _resolve(root, str(item.get("worker") or ""), environment)
            if python is None or worker is None:
                raise ValueError(f"{name}: python and worker are required")
            if not worker.is_relative_to(root):
                raise ValueError(f"{name}: worker must stay inside the project root")
            kind = IntegrationKind(str(item.get("kind") or IntegrationKind.ISOLATED_PYTHON.value))
            specs[name] = IntegrationSpec(
                name=name,
                enabled=bool(item.get("enabled", True)),
                kind=kind,
                python=python,
                worker=worker,
                repo=_resolve(root, item.get("repo"), environment),
                timeout_seconds=int(item.get("timeout_seconds", 120)),
                required=bool(item.get("required", False)),
                inherit_env=_as_tuple(item.get("inherit_env")),
                pass_env=_as_tuple(item.get("pass_env")),
                distributions=_as_tuple(item.get("distributions")),
                imports=_as_tuple(item.get("imports")),
                capabilities=_as_tuple(item.get("capabilities")),
                upgrade=dict(item.get("upgrade") or {}),
            )
        return cls(
            specs,
            project_root=root,
            artifact_root=artifact_root,
            protocol_version=protocol,
            config_path=config_path,
            config_sha256=config_sha256,
            environment=environment,
        )

    def get(self, name: str) -> IntegrationSpec:
        try:
            return self._specs[name]
        except KeyError as exc:
            raise KeyError(f"unknown integration: {name}") from exc

    def names(self, *, enabled_only: bool = False) -> tuple[str, ...]:
        items = self._specs.values()
        if enabled_only:
            items = (spec for spec in items if spec.enabled)
        return tuple(sorted(spec.name for spec in items))

    def specs(self, *, enabled_only: bool = False) -> tuple[IntegrationSpec, ...]:
        return tuple(self.get(name) for name in self.names(enabled_only=enabled_only))

    def snapshot(self) -> RegistrySnapshot:
        return RegistrySnapshot(self.protocol_version, self.config_sha256, self.specs())

    def environment_value(self, key: str) -> str | None:
        """Return a runtime environment value without exposing the environment map."""
        return self._environment.get(key)

    def static_issues(self, name: str) -> tuple[str, ...]:
        spec = self.get(name)
        issues: list[str] = []
        if not spec.enabled:
            issues.append("disabled")
        if not spec.python.exists():
            issues.append(f"python_missing:{spec.python}")
        elif not os.access(spec.python, os.X_OK):
            issues.append(f"python_not_executable:{spec.python}")
        if not spec.worker.is_file():
            issues.append(f"worker_missing:{spec.worker}")
        if spec.repo is not None and not spec.repo.exists():
            issues.append(f"repo_missing:{spec.repo}")
        return tuple(issues)

    def git_state(self, name: str) -> dict[str, Any]:
        spec = self.get(name)
        repo = spec.repo
        if repo is None or not (repo / ".git").exists():
            return {"available": False}
        try:
            commit = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            branch = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            dirty = bool(
                subprocess.run(
                    ["git", "-C", str(repo), "status", "--porcelain"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                ).stdout.strip()
            )
            return {"available": True, "commit": commit, "branch": branch, "dirty": dirty}
        except (OSError, subprocess.SubprocessError) as exc:
            return {"available": False, "error": str(exc)}

    def assert_required_available(self) -> None:
        failures: list[str] = []
        for spec in self.specs(enabled_only=True):
            issues = self.static_issues(spec.name)
            if spec.required and issues:
                failures.append(f"{spec.name}: {', '.join(issues)}")
        if failures:
            raise RuntimeError("required integrations unavailable: " + "; ".join(failures))
