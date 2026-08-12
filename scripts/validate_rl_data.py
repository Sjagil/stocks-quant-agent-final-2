from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from stocks.data import read_canonical_parquet, validate_canonical
from stocks.rl import build_rl_features, load_rl_yaml


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate canonical closed-candle OHLCV before RL training")
    parser.add_argument("parquet", type=Path)
    parser.add_argument("--config", type=Path, default=Path("config/rl.yaml"))
    parser.add_argument(
        "--max-single-bar-return",
        type=float,
        default=None,
        help="Optional economic sanity gate, e.g. 0.50 after split normalization.",
    )
    args = parser.parse_args()

    _, env_cfg, _, _ = load_rl_yaml(args.config)
    frame, metadata = read_canonical_parquet(args.parquet)
    report = validate_canonical(frame, fail_on_extreme_return=args.max_single_bar_return)

    features = build_rl_features(frame)
    joined = features.assign(__close__=frame["close"]).replace([np.inf, -np.inf], np.nan).dropna()
    minimum = env_cfg.window_size + 3
    if len(joined) < minimum:
        print(f"ERROR insufficient_fully_observed_rows={len(joined)} minimum={minimum}")
        raise SystemExit(2)

    print(
        f"rows={len(frame)} fully_observed_feature_rows={len(joined)} "
        f"features={features.shape[1]} max_abs_close_return={report.max_abs_close_return}"
    )
    if metadata:
        print(
            f"schema={metadata.get('schema_version')} source={metadata.get('source')} "
            f"adjustment={metadata.get('adjustment')}"
        )
    for warning in report.warnings:
        print(f"WARNING {warning}")
    print("DATA_VALIDATION=PASS")


if __name__ == "__main__":
    main()
