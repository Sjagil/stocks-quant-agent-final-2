from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .oos_observation_validation_v2_39_3 import normalize_oos_observations, stable_hash

_ALLOWED_PROTOCOLS = {"PURGED_WALK_FORWARD", "HOLDOUT", "FORWARD_SHADOW"}


def validate_external_provenance(payload: dict) -> dict:
    required = {
        "selection_protocol", "selected_without_test_labels", "label_overlap_checked",
        "source_engine", "data_as_of",
    }
    missing = sorted(required.difference(payload))
    if missing:
        raise ValueError(f"external OOS provenance missing fields: {missing}")
    protocol = str(payload["selection_protocol"]).upper()
    if protocol not in _ALLOWED_PROTOCOLS:
        raise ValueError("unsupported OOS selection_protocol")
    if payload.get("selected_without_test_labels") is not True:
        raise ValueError("selected_without_test_labels must be true")
    if protocol == "PURGED_WALK_FORWARD" and payload.get("label_overlap_checked") is not True:
        raise ValueError("purged walk-forward requires label_overlap_checked=true")
    if not str(payload.get("source_engine") or "").strip():
        raise ValueError("source_engine required")
    pd.Timestamp(payload["data_as_of"])
    out = dict(payload)
    out["selection_protocol"] = protocol
    out["execution_authority"] = "NONE"
    return out


def load_external_observations(
    observations_file: str | Path,
    provenance_file: str | Path,
    *,
    entity_hypothesis_id: str,
) -> tuple[pd.DataFrame, dict]:
    observations_path = Path(observations_file)
    provenance_path = Path(provenance_file)
    if observations_path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(observations_path)
    else:
        frame = pd.read_csv(observations_path)
    frame = normalize_oos_observations(frame, entity_hypothesis_id=entity_hypothesis_id)
    provenance = validate_external_provenance(json.loads(provenance_path.read_text(encoding="utf-8")))
    file_hash = hashlib.sha256(observations_path.read_bytes()).hexdigest()
    provenance.update({
        "observations_file": str(observations_path.resolve()),
        "observations_sha256": file_hash,
        "rows": int(len(frame)),
        "provenance_file": str(provenance_path.resolve()),
    })
    provenance["provenance_hash"] = stable_hash(provenance)
    return frame, provenance


__all__ = ["validate_external_provenance", "load_external_observations"]
