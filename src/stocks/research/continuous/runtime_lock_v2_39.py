from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import fcntl

@contextmanager
def exclusive_runtime_lock(path: str|Path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a+') as f:
        try: fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc: raise RuntimeError(f'continuous research already running: {p}') from exc
        try: yield
        finally: fcntl.flock(f.fileno(),fcntl.LOCK_UN)

__all__=["exclusive_runtime_lock"]
