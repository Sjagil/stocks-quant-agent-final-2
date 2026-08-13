from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

from stocks.integrations import IntegrationRegistry, IntegrationRunner

from .models import CapabilityHealth, CapabilityMode, CapabilitySpec


def _resolve(root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    expanded = Path(os.path.expandvars(value)).expanduser()
    if expanded.is_absolute():
        return Path(os.path.abspath(expanded))
    return Path(os.path.abspath(root / expanded))


class CapabilityRegistry:
    def __init__(
        self,
        specs: dict[str, CapabilitySpec],
        *,
        project_root: Path,
    ) -> None:
        self._specs = dict(specs)
        self.project_root = project_root.resolve()

    @classmethod
    def load(
        cls,
        path: str | Path = "config/capabilities.yaml",
        *,
        project_root: str | Path | None = None,
    ) -> "CapabilityRegistry":
        config_path = Path(path).resolve()
        root = (
            Path(project_root).resolve()
            if project_root is not None
            else config_path.parent.parent.resolve()
        )
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if int(raw.get("schema_version", 0)) != 1:
            raise ValueError("capability config schema_version must be 1")

        specs: dict[str, CapabilitySpec] = {}
        for name, raw_spec in dict(raw.get("capabilities") or {}).items():
            item = dict(raw_spec or {})
            specs[name] = CapabilitySpec(
                name=name,
                mode=CapabilityMode(str(item["mode"])),
                roles=tuple(str(x) for x in item.get("roles", ())),
                description=str(item.get("description", "")),
                repo=_resolve(root, item.get("repo")),
                module=item.get("module"),
                distribution=item.get("distribution"),
                integration=item.get("integration"),
                executable=_resolve(root, item.get("executable")),
                python=_resolve(root, item.get("python")),
                metadata={
                    key: value
                    for key, value in item.items()
                    if key
                    not in {
                        "mode",
                        "roles",
                        "description",
                        "repo",
                        "module",
                        "distribution",
                        "integration",
                        "executable",
                        "python",
                    }
                },
            )
        return cls(specs, project_root=root)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._specs))

    def get(self, name: str) -> CapabilitySpec:
        return self._specs[name]

    def specs(self) -> tuple[CapabilitySpec, ...]:
        return tuple(self.get(name) for name in self.names())

    def usable_for(self, role: str) -> tuple[CapabilitySpec, ...]:
        return tuple(spec for spec in self.specs() if role in spec.roles)

    @staticmethod
    def _git_state(repo: Path | None) -> dict[str, Any]:
        if repo is None or not repo.exists():
            return {"available": False}
        if not (repo / ".git").exists():
            return {
                "available": True,
                "git": False,
                "path": str(repo),
            }
        try:
            commit = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            ).stdout.strip()
            branch = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            ).stdout.strip()
            dirty = bool(
                subprocess.run(
                    ["git", "-C", str(repo), "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10,
                ).stdout.strip()
            )
            return {
                "available": True,
                "git": True,
                "path": str(repo),
                "commit": commit,
                "branch": branch,
                "dirty": dirty,
            }
        except (OSError, subprocess.SubprocessError) as exc:
            return {
                "available": False,
                "path": str(repo),
                "error": str(exc),
            }

    def _direct_health(self, spec: CapabilitySpec) -> CapabilityHealth:
        found = bool(spec.module and importlib.util.find_spec(spec.module))
        details: dict[str, Any] = {
            "module": spec.module,
            "repo": self._git_state(spec.repo),
        }
        if found and spec.distribution:
            try:
                details["version"] = importlib.metadata.version(spec.distribution)
            except importlib.metadata.PackageNotFoundError:
                details["version"] = None
        return CapabilityHealth(
            name=spec.name,
            mode=spec.mode,
            status="OK" if found else "UNAVAILABLE",
            roles=spec.roles,
            details=details,
        )

    def _worker_health(self, spec: CapabilitySpec) -> CapabilityHealth:
        if not spec.integration:
            return CapabilityHealth(
                spec.name,
                spec.mode,
                "UNAVAILABLE",
                spec.roles,
                {"error": "integration name missing"},
            )

        integrations = IntegrationRegistry.load(
            self.project_root / "config" / "integrations.yaml",
            project_root=self.project_root,
        )
        runner = IntegrationRunner(integrations)
        response = runner.health(spec.integration)
        return CapabilityHealth(
            name=spec.name,
            mode=spec.mode,
            status="OK" if response.ok else "UNAVAILABLE",
            roles=spec.roles,
            details={
                "integration": spec.integration,
                "worker": response.to_dict(),
                "repo": self._git_state(spec.repo),
            },
        )

    def _cli_health(self, spec: CapabilitySpec) -> CapabilityHealth:
        executable = spec.executable
        if executable is None or not executable.exists():
            return CapabilityHealth(
                spec.name,
                spec.mode,
                "UNAVAILABLE",
                spec.roles,
                {
                    "executable": str(executable) if executable else None,
                    "repo": self._git_state(spec.repo),
                },
            )
        try:
            result = subprocess.run(
                [str(executable), "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return CapabilityHealth(
                spec.name,
                spec.mode,
                "OK" if result.returncode == 0 else "UNAVAILABLE",
                spec.roles,
                {
                    "executable": str(executable),
                    "version": (result.stdout or result.stderr).strip(),
                    "returncode": result.returncode,
                    "repo": self._git_state(spec.repo),
                },
            )
        except OSError as exc:
            return CapabilityHealth(
                spec.name,
                spec.mode,
                "UNAVAILABLE",
                spec.roles,
                {"error": str(exc), "repo": self._git_state(spec.repo)},
            )

    def _subprocess_reference_health(
        self,
        spec: CapabilitySpec,
    ) -> CapabilityHealth:
        python = spec.python
        repo_state = self._git_state(spec.repo)
        if python is None or not python.exists() or not repo_state.get("available"):
            return CapabilityHealth(
                spec.name,
                spec.mode,
                "UNAVAILABLE",
                spec.roles,
                {
                    "python": str(python) if python else None,
                    "repo": repo_state,
                },
            )
        try:
            result = subprocess.run(
                [str(python), "--version"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            return CapabilityHealth(
                spec.name,
                spec.mode,
                "OK" if result.returncode == 0 else "UNAVAILABLE",
                spec.roles,
                {
                    "python": str(python),
                    "version": (result.stdout or result.stderr).strip(),
                    "repo": repo_state,
                },
            )
        except OSError as exc:
            return CapabilityHealth(
                spec.name,
                spec.mode,
                "UNAVAILABLE",
                spec.roles,
                {"error": str(exc), "repo": repo_state},
            )

    def _donor_health(self, spec: CapabilitySpec) -> CapabilityHealth:
        repo_state = self._git_state(spec.repo)
        return CapabilityHealth(
            spec.name,
            spec.mode,
            "OK" if repo_state.get("available") else "UNAVAILABLE",
            spec.roles,
            {"repo": repo_state},
        )

    def health(self, name: str) -> CapabilityHealth:
        spec = self.get(name)
        if spec.mode is CapabilityMode.DIRECT_PYTHON:
            return self._direct_health(spec)
        if spec.mode is CapabilityMode.INTEGRATION_WORKER:
            return self._worker_health(spec)
        if spec.mode is CapabilityMode.CLI:
            return self._cli_health(spec)
        if spec.mode is CapabilityMode.SUBPROCESS_REFERENCE:
            return self._subprocess_reference_health(spec)
        if spec.mode is CapabilityMode.DONOR:
            return self._donor_health(spec)
        raise RuntimeError(f"unsupported capability mode: {spec.mode}")

    def health_all(self) -> dict[str, CapabilityHealth]:
        return {name: self.health(name) for name in self.names()}
