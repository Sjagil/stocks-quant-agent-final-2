from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip().splitlines()[0])
    except Exception:
        return None


@contextmanager
def exclusive_learning_lock_v240(path: str | Path):
    """PID-aware lock with stale-lock recovery.

    v2.40 used O_EXCL only; any abrupt process exit could leave a permanent
    lock file and cause launchd to restart/exit forever. A lock whose PID is no
    longer alive is now removed atomically before retrying. A live owner still
    fails closed.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(2):
        try:
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            owner = _read_pid(p)
            if owner is not None and _pid_alive(owner):
                raise RuntimeError(f"learning runtime lock held by live pid {owner}")
            if attempt == 1:
                raise
            try:
                p.unlink()
            except FileNotFoundError:
                pass
    else:  # pragma: no cover
        raise RuntimeError("unable to acquire learning runtime lock")
    try:
        os.write(fd, f"{os.getpid()}\n".encode())
        os.close(fd)
        yield
    finally:
        try:
            p.unlink()
        except FileNotFoundError:
            pass


__all__ = ["exclusive_learning_lock_v240"]
