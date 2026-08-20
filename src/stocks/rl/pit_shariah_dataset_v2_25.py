from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd

from stocks.research.pit_shariah_eligibility_v2_25 import (
    attach_pit_shariah_to_training_frame_v225,
)
from stocks.rl.dataset_v2_21 import PortfolioDatasetBundleV221


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def apply_pit_shariah_mask_v225(
    bundle: PortfolioDatasetBundleV221,
    ledger: pd.DataFrame,
) -> tuple[PortfolioDatasetBundleV221, dict[str, Any]]:
    """Bind PIT Shariah eligibility directly into the RL tradable mask.

    Every observation/symbol is eligible only when the latest Shariah ledger
    state available at that observation is ``trade_eligible=True``. Unknown or
    missing state is false. The base market tradable mask is never widened.
    """
    episode = bundle.episode
    if episode.timestamps is None:
        raise ValueError("RL episode timestamps are required")
    if not {"symbol", "decision_time", "trade_eligible", "status"}.issubset(ledger.columns):
        raise ValueError("PIT Shariah ledger is missing required columns")
    timestamps = pd.to_datetime(np.asarray(episode.timestamps), utc=True)
    rows = [
        {"symbol": symbol, "decision_time": timestamp, "_asset": asset, "_time": time}
        for time, timestamp in enumerate(timestamps)
        for asset, symbol in enumerate(bundle.symbols)
    ]
    decisions = pd.DataFrame(rows)
    joined = attach_pit_shariah_to_training_frame_v225(decisions, ledger)
    mask = np.zeros_like(episode.tradable_mask, dtype=bool)
    known = 0
    eligible = 0
    for row in joined.to_dict(orient="records"):
        value = row.get("shariah_trade_eligible")
        available = row.get("shariah_available_at")
        if available not in (None, "") and not pd.isna(available):
            known += 1
        allowed = bool(value) if isinstance(value, (bool, np.bool_)) else str(value).lower() in {"1", "true", "yes"}
        if allowed:
            eligible += 1
        mask[int(row["_time"]), int(row["_asset"])] = allowed
    base_mask = np.asarray(episode.tradable_mask, dtype=bool)
    if mask.shape != base_mask.shape:
        raise AssertionError("Shariah mask shape does not match RL episode")
    mask &= base_mask
    masked_episode = replace(episode, tradable_mask=mask)
    ledger_payload = (
        ledger.astype(object)
        .where(pd.notna(ledger), None)
        .to_dict(orient="records")
    )
    ledger_sha256 = _hash(ledger_payload)
    dataset_hash = _hash(
        {
            "base_dataset_hash": bundle.dataset_hash,
            "pit_shariah_ledger_sha256": ledger_sha256,
            "tradable_mask_sha256": hashlib.sha256(mask.tobytes()).hexdigest(),
            "unknown_is_ineligible": True,
        }
    )
    masked_bundle = replace(
        bundle,
        episode=masked_episode,
        dataset_hash=dataset_hash,
    )
    audit = {
        "schema": "pit_shariah_rl_dataset_v2_25",
        "valid": True,
        "observations": int(mask.shape[0]),
        "assets": int(mask.shape[1]),
        "known_symbol_observations": int(known),
        "eligible_symbol_observations": int(mask.sum()),
        "unknown_symbol_observations": int(mask.size - known),
        "base_tradable_observations": int(base_mask.sum()),
        "shariah_mask_never_widens_base": bool(np.logical_or(~mask, base_mask).all()),
        "point_in_time": True,
        "unknown_is_ineligible": True,
        "base_dataset_hash": bundle.dataset_hash,
        "pit_shariah_ledger_sha256": ledger_sha256,
        "dataset_hash": dataset_hash,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    return masked_bundle, audit


__all__ = ["apply_pit_shariah_mask_v225"]
