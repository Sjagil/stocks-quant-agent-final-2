from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

_REQUIRED = (
    "hypothesis_id", "fold", "symbol", "entry_time", "exit_time", "gross_return",
)


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_fingerprint(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_file():
        return {"path": str(p), "exists": False}
    st = p.stat()
    return {
        "path": str(p.resolve()),
        "exists": True,
        "size": int(st.st_size),
        "mtime_ns": int(st.st_mtime_ns),
    }


def normalize_oos_observations(frame: pd.DataFrame, *, entity_hypothesis_id: str) -> pd.DataFrame:
    missing = [c for c in _REQUIRED if c not in frame.columns]
    if missing:
        raise ValueError(f"OOS observation schema missing columns: {missing}")
    work = frame.copy()
    work["hypothesis_id"] = work["hypothesis_id"].astype(str)
    if set(work["hypothesis_id"].dropna().unique()) != {str(entity_hypothesis_id)}:
        raise ValueError("OOS observations contain a different hypothesis_id")
    work["entry_time"] = pd.to_datetime(work["entry_time"], utc=True, errors="coerce")
    work["exit_time"] = pd.to_datetime(work["exit_time"], utc=True, errors="coerce")
    work["gross_return"] = pd.to_numeric(work["gross_return"], errors="coerce")
    work["fold"] = pd.to_numeric(work["fold"], errors="coerce").astype("Int64")
    work = work.dropna(subset=["entry_time", "exit_time", "gross_return", "fold"]).copy()
    work = work.loc[np.isfinite(work["gross_return"].to_numpy(dtype=float))]
    if (work["gross_return"] <= -1.0).any():
        raise ValueError("OOS gross_return must be greater than -1")
    if (work["fold"] < 1).any():
        raise ValueError("OOS fold identifiers must be >= 1")
    if (work["exit_time"] < work["entry_time"]).any():
        raise ValueError("OOS observation exit_time precedes entry_time")
    work["symbol"] = work["symbol"].astype(str).str.upper()
    # One physical trade may not become multiple observations through repeated artifact rows.
    keys = ["hypothesis_id", "fold", "symbol", "entry_time", "exit_time"]
    work = work.drop_duplicates(keys, keep="last")
    return work.sort_values(["entry_time", "exit_time", "symbol", "fold"]).reset_index(drop=True)


def effective_nonoverlap_observations(frame: pd.DataFrame) -> int:
    """Conservative event-cluster count across all symbols.

    Any concurrently open trades belong to one temporal cluster. This intentionally avoids
    calling overlapping cross-asset trades statistically independent observations.
    """
    if frame.empty:
        return 0
    work = frame.sort_values(["entry_time", "exit_time"])
    clusters = 0
    cluster_end = None
    for row in work.itertuples(index=False):
        start = pd.Timestamp(row.entry_time)
        end = pd.Timestamp(row.exit_time)
        if cluster_end is None or start > cluster_end:
            clusters += 1
            cluster_end = end
        elif end > cluster_end:
            cluster_end = end
    return int(clusters)


def profit_factor(values: Iterable[float]) -> float:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    gains = float(arr[arr > 0].sum())
    losses = float(-arr[arr < 0].sum())
    if losses > 0:
        return gains / losses
    if gains > 0:
        return math.inf
    return 0.0


def write_json(path: str | Path, payload) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


__all__ = [
    "canonical_json", "stable_hash", "file_fingerprint", "normalize_oos_observations",
    "effective_nonoverlap_observations", "profit_factor", "write_json",
]
