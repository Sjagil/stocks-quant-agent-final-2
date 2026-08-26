import plistlib
from pathlib import Path
from stocks.production import launchd_v2_41 as mod


def test_launchd_points_to_watch(tmp_path, monkeypatch):
    root=tmp_path/'repo'; (root/'.venv/bin').mkdir(parents=True); (root/'scripts').mkdir()
    (root/'.venv/bin/python').write_text(''); (root/'scripts/run_production_runtime_v2_41.py').write_text('')
    target=tmp_path/'agent.plist'
    monkeypatch.setattr(mod,'launchagent_path_v241',lambda:target)
    out=mod.install_launchagent_v241(root,interval_seconds=300)
    d=plistlib.loads(out.read_bytes())
    assert d['ProgramArguments'][-3:] == ['watch','--interval-seconds','300']
    assert d['KeepAlive'] is True
