from __future__ import annotations

import pandas as pd


ROLE_COLUMNS = {
    "DQN_TIMING": (
        "log_ret_1", "log_ret_5", "log_ret_20", "gap_ret", "range_pct",
        "body_pct", "upper_wick_pct", "lower_wick_pct", "close_location",
        "rsi_2", "rsi_14", "macd_hist_pct", "adx_14", "di_spread",
        "bb_z_20", "atr_pct", "ema20_dist", "ema50_dist", "roc_5",
        "roc_20", "stoch_k_14", "mfi_14", "obv_slope_10",
        "volume_robust_z", "cmf_20", "rolling_vwap20_dist",
        "donchian_high_dist_20", "donchian_low_dist_20",
    ),
    "SAC_SIZING": (
        "log_ret_5", "log_ret_20", "range_pct", "atr_pct", "adx_14",
        "di_spread", "bb_width_20", "bb_z_20", "realized_vol_10",
        "realized_vol_20", "vol_of_vol_20", "ema20_dist", "ema50_dist",
        "ema100_dist", "ema200_dist", "roc_20", "mfi_14",
        "obv_slope_10", "volume_robust_z", "cmf_20", "rolling_vwap20_dist",
    ),
    "RISK": (
        "log_ret_1", "log_ret_5", "gap_ret", "range_pct", "atr_pct",
        "bb_width_20", "bb_z_20", "realized_vol_10", "realized_vol_20",
        "vol_of_vol_20", "adx_14", "di_spread", "ema20_dist", "ema50_dist",
        "volume_robust_z", "cmf_20", "rolling_vwap20_dist",
    ),
}

ALIASES = {
    "DQN": "DQN_TIMING",
    "ENTRY_EXIT_TIMING": "DQN_TIMING",
    "SAC": "SAC_SIZING",
    "CONTINUOUS_TARGET_EXPOSURE": "SAC_SIZING",
    "MASKABLE_PPO": "RISK",
    "POSITION_RISK_REDUCTION": "RISK",
}


def normalize_role(role: str) -> str:
    key = str(role).strip().upper()
    return ALIASES.get(key, key)


def select_role_features(features: pd.DataFrame, role: str) -> pd.DataFrame:
    normalized = normalize_role(role)
    if normalized not in ROLE_COLUMNS:
        raise ValueError(f"unsupported agent feature role: {role}")
    columns = ROLE_COLUMNS[normalized]
    missing = [column for column in columns if column not in features.columns]
    if missing:
        raise ValueError(f"feature bank missing {normalized} columns: {missing}")
    return features.loc[:, list(columns)].copy()
