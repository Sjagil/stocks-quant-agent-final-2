from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stocks.data.canonical import canonicalize_ohlcv
from stocks.rl.features import build_rl_features

DEFAULT_SYMBOLS = ("SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMD", "GLD", "SLV", "CPER")
FEATURES = (
    "log_ret_1", "log_ret_5", "log_ret_20", "range_pct", "body_pct",
    "ema20_dist", "ema50_dist", "rsi_14", "atr_pct", "macd_hist_pct",
    "adx_14", "di_spread", "bb_z_20", "realized_vol_20", "roc_20",
    "volume_robust_z", "cmf_20",
)


def _normalize_local(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame[list(FEATURES)].copy().astype(float)
    out["rsi_14"] = (out["rsi_14"] - 50.0) / 50.0
    out["adx_14"] = out["adx_14"] / 100.0
    for col in ("bb_z_20", "volume_robust_z"):
        out[col] = out[col].clip(-5, 5) / 5.0
    for col in out.columns:
        out[col] = out[col].clip(-10, 10)
    return out.replace([np.inf, -np.inf], np.nan)


def build_mappo_dataset_v242(
    root: str | Path,
    *,
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    output_path: str | Path = "artifacts/research_runtime/rl_portfolio_control_v2_38/mappo_training.npz",
    transaction_cost_bps: float = 8.0,
) -> dict[str, Any]:
    root = Path(root).resolve()
    local_by_symbol: dict[str, pd.DataFrame] = {}
    close_by_symbol: dict[str, pd.Series] = {}
    for symbol in symbols:
        path = root / "data/canonical/provider_fabric" / f"{symbol}_1h.parquet"
        if not path.is_file():
            raise FileNotFoundError(path)
        market = canonicalize_ohlcv(pd.read_parquet(path)).sort_index()
        feats = _normalize_local(build_rl_features(market))
        joined = feats.join(market["close"].astype(float).rename("close")).dropna()
        if len(joined) < 800:
            raise ValueError(f"insufficient MAPPO history for {symbol}: {len(joined)}")
        local_by_symbol[symbol] = joined.drop(columns=["close"])
        close_by_symbol[symbol] = joined["close"]

    common = None
    for frame in local_by_symbol.values():
        common = frame.index if common is None else common.intersection(frame.index)
    if common is None or len(common) < 512:
        raise ValueError(f"insufficient synchronized MAPPO samples: {0 if common is None else len(common)}")
    common = common.sort_values()

    local_stack = np.stack([local_by_symbol[s].loc[common].to_numpy(dtype=np.float32) for s in symbols], axis=1)
    closes = np.stack([close_by_symbol[s].loc[common].to_numpy(dtype=np.float64) for s in symbols], axis=1)
    returns = np.zeros_like(closes, dtype=np.float64)
    returns[:-1] = closes[1:] / closes[:-1] - 1.0

    # Causal bootstrap behavior policy. Actions at t depend only on observations at t.
    ema_idx = FEATURES.index("ema20_dist")
    mom_idx = FEATURES.index("log_ret_20")
    rsi_idx = FEATURES.index("rsi_14")
    raw_score = 6.0 * local_stack[:, :, ema_idx] + 3.0 * local_stack[:, :, mom_idx] + 0.20 * local_stack[:, :, rsi_idx]
    actions = (1.0 / (1.0 + np.exp(-raw_score))).astype(np.float32)
    actions = np.where(raw_score > -0.05, actions, 0.0).astype(np.float32)
    eligible = np.ones(actions.shape, dtype=bool)
    turnover = np.abs(actions - np.vstack([np.zeros((1, actions.shape[1]), dtype=np.float32), actions[:-1]]))
    one_way_cost = float(transaction_cost_bps) / 10000.0
    rewards = (actions * returns - turnover * one_way_cost).astype(np.float32)

    mean_local = local_stack.mean(axis=1)
    std_local = local_stack.std(axis=1)
    spy_local = local_stack[:, 0, :]
    global_obs = np.concatenate([mean_local, std_local, spy_local], axis=1).astype(np.float32)

    # Last action has no realized t+1 return and is excluded.
    local_stack = local_stack[:-1]
    global_obs = global_obs[:-1]
    actions = actions[:-1]
    rewards = rewards[:-1]
    eligible = eligible[:-1]
    timestamps = np.asarray([str(x) for x in common[:-1]])

    target = Path(output_path)
    if not target.is_absolute():
        target = root / target
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    with tmp.open("wb") as handle:
        np.savez_compressed(
            handle,
            local_obs=local_stack,
            global_obs=global_obs,
            actions=actions,
            rewards=rewards,
            eligible_mask=eligible,
        )
    tmp.replace(target)
    meta = {
        "schema": "mappo_dataset_v2_42",
        "dataset_path": str(target),
        "samples": int(len(local_stack)),
        "agents": len(symbols),
        "symbols": list(symbols),
        "local_features": list(FEATURES),
        "local_dim": int(local_stack.shape[-1]),
        "global_dim": int(global_obs.shape[-1]),
        "start": str(timestamps[0]) if len(timestamps) else None,
        "end": str(timestamps[-1]) if len(timestamps) else None,
        "behavior_policy": "CAUSAL_TREND_BOOTSTRAP_V2_42",
        "reward": "NEXT_BAR_NET_RETURN_MINUS_TURNOVER_COST",
        "transaction_cost_bps": float(transaction_cost_bps),
        "execution_authority": "NONE",
    }
    target.with_suffix(".metadata.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    return meta
