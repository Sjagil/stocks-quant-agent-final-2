from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from stocks.data.canonical import canonicalize_ohlcv


@dataclass(frozen=True)
class StrategySource:
    name: str
    file: str
    roles: tuple[str, ...]
    timeframes: tuple[str, ...]
    research_only: bool = True

    def as_dict(self) -> dict:
        return asdict(self)


def strategy_sources() -> tuple[StrategySource, ...]:
    return (
        StrategySource(
            name="gex_rsi2_bollinger_orderflow",
            file="src/stocks/intelligence_agent/strategy1.py",
            roles=(
                "technical",
                "options",
                "gex",
                "orderflow",
                "mean_reversion",
            ),
            timeframes=("1d", "15m"),
        ),
        StrategySource(
            name="strategy_combo_lab_v2",
            file=(
                "src/stocks/intelligence_agent/"
                "strategy_combo_research_lab.py"
            ),
            roles=(
                "strategy_registry",
                "parameter_search",
                "portfolio_combinations",
                "walk_forward_research",
            ),
            timeframes=("1d",),
        ),
    )


def strategy1_technical_snapshot(
    frame: pd.DataFrame,
    symbol: str,
) -> dict:
    try:
        from stocks.intelligence_agent.strategy1 import (
            StrategyConfig,
            calculate_technical_setup,
        )
    except Exception as exc:
        return {
            "status": "UNAVAILABLE",
            "strategy": "strategy1",
            "error": f"{type(exc).__name__}: {exc}",
        }

    work = canonicalize_ohlcv(frame).reset_index()
    work = work.rename(columns={"timestamp": "date"})

    try:
        output = calculate_technical_setup(
            work,
            StrategyConfig(symbol=symbol),
        )

        warmed = output.dropna(
            subset=(
                "rsi_2",
                "adx_5",
                "bb_lower",
                "bb_upper",
                "sma_200",
                "atr_14",
            )
        )

        if warmed.empty:
            return {
                "status": "NOT_READY",
                "strategy": "strategy1",
                "symbol": symbol,
            }

        row = warmed.iloc[-1]

        return {
            "status": "OK",
            "strategy": "strategy1",
            "symbol": symbol,
            "timestamp": str(row["date"]),
            "close": float(row["close"]),
            "rsi_2": float(row["rsi_2"]),
            "adx_5": float(row["adx_5"]),
            "bb_lower": float(row["bb_lower"]),
            "bb_upper": float(row["bb_upper"]),
            "sma_200": float(row["sma_200"]),
            "atr_14": float(row["atr_14"]),
            "gex_evaluated": False,
            "orderflow_evaluated": False,
        }

    except Exception as exc:
        return {
            "status": "ERROR",
            "strategy": "strategy1",
            "symbol": symbol,
            "error": f"{type(exc).__name__}: {exc}",
        }


def export_daily_lab_dataset(
    frames: dict[str, pd.DataFrame],
    path: Path,
) -> Path:
    rows: list[pd.DataFrame] = []

    for symbol, frame in frames.items():
        work = canonicalize_ohlcv(frame).reset_index()
        work["symbol"] = symbol
        work = work.rename(columns={"timestamp": "date"})
        rows.append(
            work[
                [
                    "symbol",
                    "date",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ]
            ]
        )

    if not rows:
        raise ValueError("no daily frames available")

    combined = pd.concat(rows, ignore_index=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(path, index=False)

    return path


def validate_combo_lab(
    project_root: Path,
    data_path: Path,
    *,
    max_symbols: int = 50,
) -> dict:
    script = (
        project_root
        / "src"
        / "stocks"
        / "intelligence_agent"
        / "strategy_combo_research_lab.py"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "validate",
            "--data",
            str(data_path),
            "--min-bars",
            "200",
            "--max-symbols",
            str(max_symbols),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )

    return {
        "status": "OK" if completed.returncode == 0 else "ERROR",
        "returncode": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-12000:],
        "data_path": str(data_path),
    }
