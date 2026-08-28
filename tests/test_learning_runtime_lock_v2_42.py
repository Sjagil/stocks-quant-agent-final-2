import os
from pathlib import Path
import pytest
from stocks.learning.runtime_lock_v2_40 import exclusive_learning_lock_v240


def test_stale_pid_lock_is_recovered(tmp_path):
    p = tmp_path / "runtime.lock"
    p.write_text("99999999\n")
    with exclusive_learning_lock_v240(p):
        assert p.is_file()
        assert int(p.read_text().strip()) == os.getpid()
    assert not p.exists()


def test_live_pid_lock_fails_closed(tmp_path):
    p = tmp_path / "runtime.lock"
    p.write_text(f"{os.getpid()}\n")
    with pytest.raises(RuntimeError, match="live pid"):
        with exclusive_learning_lock_v240(p):
            pass
