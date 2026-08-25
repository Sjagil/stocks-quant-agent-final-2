from pathlib import Path
import pytest
from stocks.learning.subprocess_runner_v2_40 import run_allowlisted_component_v240


def test_arbitrary_script_is_rejected(tmp_path: Path):
    (tmp_path/".venv/bin").mkdir(parents=True); (tmp_path/".venv/bin/python").write_text("")
    bad=tmp_path/"evil.py"; bad.write_text("print('x')")
    with pytest.raises(ValueError):
        run_allowlisted_component_v240(tmp_path,[str(tmp_path/".venv/bin/python"),str(bad)])
