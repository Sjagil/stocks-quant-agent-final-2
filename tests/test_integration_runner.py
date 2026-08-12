from __future__ import annotations

import sys
from pathlib import Path

from stocks.integrations import IntegrationKind, IntegrationRegistry, IntegrationRunner, IntegrationSpec, IntegrationState


def test_runner_uses_json_file_protocol(tmp_path: Path) -> None:
    worker = tmp_path / "worker.py"
    worker.write_text(
        """
import argparse, json
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--request'); p.add_argument('--response'); p.add_argument('--artifact-dir'); a=p.parse_args()
r=json.loads(Path(a.request).read_text())
out={'integration':r['integration'],'action':r['action'],'request_id':r['request_id'],'state':'OK','data':{'echo':r['payload']},'artifacts':[],'warnings':[],'error':None,'protocol_version':'1.0'}
Path(a.response).write_text(json.dumps(out))
""".strip()
        + "\n",
        encoding="utf-8",
    )
    spec = IntegrationSpec(
        name="dummy",
        enabled=True,
        kind=IntegrationKind.ISOLATED_PYTHON,
        python=Path(sys.executable),
        worker=worker,
        timeout_seconds=10,
    )
    registry = IntegrationRegistry(
        {"dummy": spec},
        project_root=tmp_path,
        artifact_root=tmp_path / "artifacts",
    )
    response = IntegrationRunner(registry).run("dummy", "echo", {"a": 1})
    assert response.state is IntegrationState.OK
    assert response.data == {"echo": {"a": 1}}
    run_dir = tmp_path / "artifacts" / response.request_id
    assert (run_dir / "request.json").exists()
    assert (run_dir / "response.json").exists()
    assert (run_dir / "run_manifest.json").exists()


def test_runner_rejects_secret_bearing_payload(tmp_path: Path) -> None:
    worker = tmp_path / "worker.py"
    worker.write_text("raise SystemExit('must not execute')\n", encoding="utf-8")
    spec = IntegrationSpec(
        name="dummy",
        enabled=True,
        kind=IntegrationKind.ISOLATED_PYTHON,
        python=Path(sys.executable),
        worker=worker,
        timeout_seconds=10,
        capabilities=("echo",),
    )
    registry = IntegrationRegistry(
        {"dummy": spec},
        project_root=tmp_path,
        artifact_root=tmp_path / "artifacts",
    )
    response = IntegrationRunner(registry).run("dummy", "echo", {"api_key": "do-not-persist"})
    assert response.state is IntegrationState.ERROR
    assert "secrets must be passed" in (response.error or "")
    assert not (tmp_path / "artifacts").exists()


def test_runner_timeout_writes_manifest(tmp_path: Path) -> None:
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import time\ntime.sleep(2)\n",
        encoding="utf-8",
    )
    spec = IntegrationSpec(
        name="dummy",
        enabled=True,
        kind=IntegrationKind.ISOLATED_PYTHON,
        python=Path(sys.executable),
        worker=worker,
        timeout_seconds=1,
        capabilities=("wait",),
    )
    registry = IntegrationRegistry(
        {"dummy": spec},
        project_root=tmp_path,
        artifact_root=tmp_path / "artifacts",
    )
    response = IntegrationRunner(registry).run("dummy", "wait")
    assert response.state is IntegrationState.ERROR
    run_dir = tmp_path / "artifacts" / response.request_id
    assert (run_dir / "run_manifest.json").exists()
