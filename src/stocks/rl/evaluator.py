from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class EvaluationResult:
    total_return: float
    max_drawdown: float
    sharpe: float
    steps: int
    trades: int


def evaluate_policy(model: Any, env: Any, deterministic: bool = True) -> EvaluationResult:
    obs, info = env.reset()
    start_equity = float(info["equity"])
    equity_curve = [start_equity]
    returns: list[float] = []
    done = False
    last_trades = 0

    while not done:
        action, _ = model.predict(obs, deterministic=deterministic)
        obs, _, terminated, truncated, info = env.step(action)
        equity = float(info["equity"])
        returns.append(equity / equity_curve[-1] - 1.0)
        equity_curve.append(equity)
        last_trades = int(info.get("trades", 0))
        done = bool(terminated or truncated)

    curve = np.asarray(equity_curve, dtype=float)
    peaks = np.maximum.accumulate(curve)
    drawdowns = 1.0 - curve / np.maximum(peaks, 1e-12)
    rets = np.asarray(returns, dtype=float)
    sharpe = 0.0 if len(rets) < 2 or rets.std(ddof=1) == 0 else float(np.sqrt(252) * rets.mean() / rets.std(ddof=1))
    return EvaluationResult(
        total_return=float(curve[-1] / curve[0] - 1.0),
        max_drawdown=float(drawdowns.max(initial=0.0)),
        sharpe=sharpe,
        steps=len(returns),
        trades=last_trades,
    )
