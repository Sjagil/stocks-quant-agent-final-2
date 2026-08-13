from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .metrics import summarize_returns


@dataclass(frozen=True)
class EvaluationResult:
    total_return: float
    max_drawdown: float
    sharpe: float
    steps: int
    trades: int


def evaluate_policy(
    model: Any,
    env: Any,
    deterministic: bool = True,
) -> EvaluationResult:
    obs, info = env.reset()

    previous_equity = float(
        info["equity"]
    )

    returns: list[float] = []

    done = False
    last_trades = 0

    while not done:
        action, _ = model.predict(
            obs,
            deterministic=deterministic,
        )

        (
            obs,
            _,
            terminated,
            truncated,
            info,
        ) = env.step(action)

        equity = float(
            info["equity"]
        )

        simple_return = (
            equity /
            previous_equity -
            1.0
        )

        returns.append(
            simple_return
        )

        previous_equity = equity

        last_trades = int(
            info.get(
                "trades",
                0,
            )
        )

        done = bool(
            terminated or truncated
        )

    close = getattr(
        env,
        "close",
        None,
    )

    if close is not None:
        start = int(
            getattr(
                env,
                "_start",
                0,
            )
        ) + 1

        index = close.index[
            start:
            start + len(returns)
        ]

        if len(index) != len(returns):
            index = pd.RangeIndex(
                len(returns)
            )
    else:
        index = pd.RangeIndex(
            len(returns)
        )

    metrics = summarize_returns(
        pd.Series(
            returns,
            index=index,
            dtype=float,
        )
    )

    return EvaluationResult(
        total_return=metrics.total_return,
        max_drawdown=metrics.max_drawdown,
        sharpe=metrics.sharpe,
        steps=len(returns),
        trades=last_trades,
    )
