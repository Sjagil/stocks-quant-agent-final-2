from __future__ import annotations

from pathlib import Path

from stocks.integrations import IntegrationRegistry


def test_registry_loads_project_paths() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = IntegrationRegistry.load(root / "config" / "integrations.yaml", project_root=root)
    assert {"vnpy", "qlib", "finrl", "moondev", "nautilus"}.issubset(registry.names())
    assert registry.get("qlib").worker == (root / "scripts/workers/qlib_worker.py").resolve()
    assert registry.artifact_root == (root / "artifacts/integrations").resolve()
    assert registry.config_sha256 is not None and len(registry.config_sha256) == 64


def test_registry_rejects_worker_outside_project(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    outside = tmp_path.parent / "outside_worker.py"
    outside.write_text("print('x')\n", encoding="utf-8")
    config = config_dir / "integrations.yaml"
    config.write_text(
        f"""
schema_version: 1
protocol_version: "1.0"
artifact_root: artifacts/integrations
integrations:
  bad:
    enabled: true
    kind: isolated_python
    python: /usr/bin/python3
    worker: {outside}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    import pytest

    with pytest.raises(ValueError, match="worker must stay inside"):
        IntegrationRegistry.load(config, project_root=tmp_path)


def test_registry_reads_local_env_for_path_overrides(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    worker = tmp_path / "worker.py"
    worker.write_text("print('x')\n", encoding="utf-8")
    fake_python = tmp_path / "custom-python"
    fake_python.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_python.chmod(0o755)
    (tmp_path / ".env").write_text(
        f"CUSTOM_PY={fake_python}\nPRIVATE_API_KEY=not-for-manifest\n",
        encoding="utf-8",
    )
    config = config_dir / "integrations.yaml"
    config.write_text(
        """
schema_version: 1
protocol_version: "1.0"
artifact_root: artifacts/integrations
integrations:
  demo:
    enabled: true
    kind: isolated_python
    python: "${CUSTOM_PY}"
    worker: worker.py
    pass_env: [PRIVATE_API_KEY]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    registry = IntegrationRegistry.load(config, project_root=tmp_path)
    assert registry.get("demo").python == fake_python.resolve()
    assert registry.environment_value("PRIVATE_API_KEY") == "not-for-manifest"
    assert "not-for-manifest" not in repr(registry.snapshot())


def test_registry_preserves_virtualenv_python_symlink(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    worker = tmp_path / "worker.py"
    worker.write_text("print('x')\n", encoding="utf-8")

    base_python = tmp_path / "base-python"
    base_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    base_python.chmod(0o755)

    venv_bin = tmp_path / ".venvs" / "demo" / "bin"
    venv_bin.mkdir(parents=True)
    venv_python = venv_bin / "python"
    venv_python.symlink_to(base_python)

    config = config_dir / "integrations.yaml"
    config.write_text(
        """
schema_version: 1
protocol_version: "1.0"
artifact_root: artifacts/integrations
integrations:
  demo:
    enabled: true
    kind: isolated_python
    python: .venvs/demo/bin/python
    worker: worker.py
""".strip()
        + "\n",
        encoding="utf-8",
    )

    registry = IntegrationRegistry.load(config, project_root=tmp_path)
    configured = registry.get("demo").python

    assert configured == venv_python.absolute()
    assert configured != base_python.resolve()
    assert configured.is_symlink()
