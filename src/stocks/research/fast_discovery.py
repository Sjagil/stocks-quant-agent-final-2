from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from stocks.data.canonical import canonicalize_ohlcv


@dataclass(frozen=True)
class ScreenResult:
    engine: str
    strategy: str
    fast_window: int
    slow_window: int
    total_return: float
    sharpe: float
    max_drawdown: float
    trades: int
    observations: int

    def as_dict(self) -> dict:
        return asdict(self)


def annualization_factor(index: pd.Index) -> float:
    timestamps = pd.DatetimeIndex(index).sort_values().unique()

    if len(timestamps) < 2:
        return 252.0

    elapsed_years = max(
        (timestamps[-1] - timestamps[0]).total_seconds()
        / (365.2425 * 24 * 60 * 60),
        1 / 365.2425,
    )

    return max((len(timestamps) - 1) / elapsed_years, 1.0)


def performance_metrics(
    returns: pd.Series,
    position: pd.Series,
) -> tuple[float, float, float, int]:
    clean = returns.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    equity = (1.0 + clean).cumprod()

    total_return = float(equity.iloc[-1] - 1.0)

    peak = equity.cummax()
    drawdown = equity / peak - 1.0
    max_drawdown = float(drawdown.min())

    std = float(clean.std(ddof=0))
    sharpe = (
        float(clean.mean() / std * math.sqrt(annualization_factor(clean.index)))
        if std > 0
        else 0.0
    )

    entries = position.diff().fillna(position).gt(0)
    trades = int(entries.sum())

    return total_return, sharpe, max_drawdown, trades


def _strategy_returns(
    close: pd.Series,
    position: pd.Series,
    *,
    cost_bps: float,
) -> pd.Series:
    market_returns = close.pct_change(fill_method=None).fillna(0.0)

    delayed = position.shift(1).fillna(0.0).astype(float)
    turnover = delayed.diff().abs().fillna(delayed.abs())

    costs = turnover * (float(cost_bps) / 10_000.0)

    return delayed * market_returns - costs


def vectorbt_ma_screen(
    frame: pd.DataFrame,
    *,
    fast_windows: tuple[int, ...] = (5, 10, 20),
    slow_windows: tuple[int, ...] = (30, 50, 100),
    cost_bps: float = 10.0,
) -> list[ScreenResult]:
    import vectorbt as vbt

    work = canonicalize_ohlcv(frame)
    close = work["close"].astype(float)

    results: list[ScreenResult] = []

    for fast in fast_windows:
        for slow in slow_windows:
            if fast >= slow or len(close) <= slow + 5:
                continue

            fast_ma = vbt.MA.run(close, window=fast).ma
            slow_ma = vbt.MA.run(close, window=slow).ma

            if isinstance(fast_ma, pd.DataFrame):
                fast_ma = fast_ma.iloc[:, 0]

            if isinstance(slow_ma, pd.DataFrame):
                slow_ma = slow_ma.iloc[:, 0]

            position = (
                pd.Series(fast_ma, index=close.index)
                > pd.Series(slow_ma, index=close.index)
            ).astype(float)

            returns = _strategy_returns(
                close,
                position,
                cost_bps=cost_bps,
            )

            total_return, sharpe, drawdown, trades = performance_metrics(
                returns,
                position,
            )

            results.append(
                ScreenResult(
                    engine="vectorbt",
                    strategy="ma_trend",
                    fast_window=fast,
                    slow_window=slow,
                    total_return=total_return,
                    sharpe=sharpe,
                    max_drawdown=drawdown,
                    trades=trades,
                    observations=len(close),
                )
            )

    return sorted(
        results,
        key=lambda result: (
            result.sharpe,
            result.total_return,
        ),
        reverse=True,
    )


def optuna_ma_search(
    frame: pd.DataFrame,
    *,
    n_trials: int = 40,
    cost_bps: float = 10.0,
    seed: int = 20260813,
) -> dict:
    import optuna

    work = canonicalize_ohlcv(frame)
    close = work["close"].astype(float)

    if len(close) < 150:
        raise ValueError("at least 150 observations required for Optuna search")

    train_end = int(len(close) * 0.60)
    valid_end = int(len(close) * 0.80)

    validation_index = close.index[train_end:valid_end]
    test_index = close.index[valid_end:]

    max_slow = min(200, max(30, len(close) // 3))

    def build_returns(fast: int, slow: int) -> tuple[pd.Series, pd.Series]:
        fast_ma = close.rolling(fast).mean()
        slow_ma = close.rolling(slow).mean()

        position = (fast_ma > slow_ma).astype(float)

        returns = _strategy_returns(
            close,
            position,
            cost_bps=cost_bps,
        )

        return returns, position

    def objective(trial: optuna.Trial) -> float:
        fast = trial.suggest_int("fast_window", 3, min(40, max_slow - 5))
        slow = trial.suggest_int(
            "slow_window",
            max(fast + 5, 20),
            max_slow,
        )

        returns, position = build_returns(fast, slow)

        validation_returns = returns.loc[validation_index]
        validation_position = position.loc[validation_index]

        _, sharpe, _, _ = performance_metrics(
            validation_returns,
            validation_position,
        )

        return sharpe

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=seed),
    )

    study.optimize(objective, n_trials=n_trials)

    fast = int(study.best_params["fast_window"])
    slow = int(study.best_params["slow_window"])

    returns, position = build_returns(fast, slow)

    segments = {
        "train": close.index[:train_end],
        "validation": validation_index,
        "test": test_index,
    }

    metrics = {}

    for name, index in segments.items():
        values = performance_metrics(
            returns.loc[index],
            position.loc[index],
        )

        metrics[name] = {
            "total_return": values[0],
            "sharpe": values[1],
            "max_drawdown": values[2],
            "trades": values[3],
            "observations": len(index),
        }

    return {
        "engine": "optuna",
        "strategy": "ma_trend",
        "best_params": {
            "fast_window": fast,
            "slow_window": slow,
        },
        "best_validation_objective": float(study.best_value),
        "n_trials": len(study.trials),
        "metrics": metrics,
        "test_used_for_optimization": False,
    }
