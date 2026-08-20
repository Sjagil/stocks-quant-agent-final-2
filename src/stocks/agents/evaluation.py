from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from stocks.rl.metrics import summarize_returns


@dataclass(frozen=True)
class AgentEvaluation:
    total_return: float
    max_drawdown: float
    sharpe: float
    steps: int
    trades: int
    final_equity: float

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_agent(
    model,
    env,
    *,
    deterministic: bool = True,
) -> AgentEvaluation:
    obs, info = env.reset()
    previous_equity = float(info["equity"])
    returns: list[float] = []
    done = False
    last_trades = int(info.get("trades", 0))

    while not done:
        kwargs = {"deterministic": deterministic}
        if hasattr(env, "action_masks"):
            kwargs["action_masks"] = env.action_masks()

        action, _ = model.predict(obs, **kwargs)

        (
            obs,
            _reward,
            terminated,
            truncated,
            info,
        ) = env.step(action)

        equity = float(info["equity"])
        returns.append(
            equity / max(previous_equity, 1e-12) - 1.0
        )
        previous_equity = equity
        last_trades = int(info.get("trades", last_trades))
        done = bool(terminated or truncated)

    series = pd.Series(returns, dtype=float)
    metrics = summarize_returns(series)

    return AgentEvaluation(
        total_return=float(metrics.total_return),
        max_drawdown=float(metrics.max_drawdown),
        sharpe=float(metrics.sharpe),
        steps=int(len(returns)),
        trades=int(last_trades),
        final_equity=float(previous_equity),
    )


def buy_hold_metrics(
    close: pd.Series,
    *,
    transaction_cost_bps: float,
    slippage_bps: float,
) -> dict:
    series = close.astype(float).pct_change(fill_method=None).dropna()
    if not series.empty:
        cost = (
            float(transaction_cost_bps)
            + float(slippage_bps)
        ) / 10_000.0
        series.iloc[0] -= cost
    metrics = summarize_returns(series)
    return {
        "total_return": float(metrics.total_return),
        "max_drawdown": float(metrics.max_drawdown),
        "sharpe": float(metrics.sharpe),
        "steps": int(len(series)),
    }
