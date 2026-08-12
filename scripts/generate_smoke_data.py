from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic OHLCV for an installation smoke test only")
    parser.add_argument("--out", type=Path, default=Path("data/processed/SMOKE_1h.parquet"))
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.rows < 400:
        raise SystemExit("--rows must be >= 400")

    rng = np.random.default_rng(args.seed)
    ret = rng.normal(0.00008, 0.007, args.rows)
    close = 100.0 * np.exp(np.cumsum(ret))
    open_ = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, 0.0015, args.rows))
    spread = np.abs(rng.normal(0.004, 0.0015, args.rows))
    high = np.maximum(open_, close) * (1 + spread)
    low = np.minimum(open_, close) * np.maximum(0.01, 1 - spread)
    volume = rng.lognormal(mean=12.0, sigma=0.45, size=args.rows)
    index = pd.date_range("2020-01-01", periods=args.rows, freq="h", tz="UTC")
    frame = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=index)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(args.out)
    print(f"SMOKE_DATA={args.out} rows={len(frame)}")


if __name__ == "__main__":
    main()
