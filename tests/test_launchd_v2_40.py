import plistlib
from pathlib import Path
from stocks.learning import launchd_v2_40


def test_launchd_points_to_safe_watch(tmp_path, monkeypatch):
    home=tmp_path/"home"; monkeypatch.setattr(Path,"home",classmethod(lambda cls: home))
    repo=tmp_path/"repo"; repo.mkdir()
    p=launchd_v2_40.install_launchagent_v240(repo,interval_seconds=900)
    with p.open("rb") as f: d=plistlib.load(f)
    args=d["ProgramArguments"]
    assert "run_autonomous_learning_v2_40.py" in args[1]
    assert "watch" in args
    assert not any("broker" in str(x).lower() for x in args)
