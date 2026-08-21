from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from .contracts_v2_21 import (
    DEPLOYMENT_MODE,
    EXECUTION_AUTHORITY,
    PortfolioEnvironmentConfigV221,
    PortfolioEpisodeV221,
)


@dataclass(frozen=True)
class PortfolioObservationV221:
    local: np.ndarray
    global_context: np.ndarray
    tradable_mask: np.ndarray
    portfolio_weights: np.ndarray
    cash_weight: float
    equity: float
    drawdown: float

    def decentralized_actor_state(self) -> np.ndarray:
        """Append only locally actionable portfolio context to every asset row."""

        asset_count = self.local.shape[0]
        context = np.column_stack(
            [
                self.portfolio_weights,
                np.full(asset_count, self.cash_weight),
                np.full(asset_count, self.drawdown),
                np.full(asset_count, self.portfolio_weights.sum()),
            ]
        ).astype(np.float32)
        return np.concatenate([self.local, context], axis=1).astype(np.float32)

    def centralized_critic_state(self, *, initial_equity: float) -> np.ndarray:
        if initial_equity <= 0:
            raise ValueError("initial_equity must be positive")
        portfolio = np.asarray(
            [
                self.cash_weight,
                self.drawdown,
                self.portfolio_weights.sum(),
                self.equity / initial_equity - 1.0,
            ],
            dtype=np.float32,
        )
        return np.concatenate([self.global_context, portfolio]).astype(np.float32)


@dataclass(frozen=True)
class PortfolioStepV221:
    observation: PortfolioObservationV221
    agent_rewards: np.ndarray
    team_reward: float
    terminated: bool
    truncated: bool
    info: dict[str, object]


def project_long_only_weights(
    actions: np.ndarray,
    tradable_mask: np.ndarray,
    *,
    max_asset_weight: float,
    max_gross_exposure: float,
) -> np.ndarray:
    """Project arbitrary action scores into the deterministic long-only set."""

    raw = np.asarray(actions, dtype=np.float64).reshape(-1)
    mask = np.asarray(tradable_mask, dtype=bool).reshape(-1)
    if raw.shape != mask.shape:
        raise ValueError("actions and tradable_mask must have the same shape")
    if not np.isfinite(raw).all():
        raise ValueError("actions must be finite")
    if not 0 < max_asset_weight <= 1:
        raise ValueError("max_asset_weight must be in (0, 1]")
    if not 0 < max_gross_exposure < 1:
        raise ValueError("max_gross_exposure must be in (0, 1)")

    projected = np.where(mask, np.clip(raw, 0.0, max_asset_weight), 0.0)
    gross = float(projected.sum())
    if gross > max_gross_exposure:
        projected *= max_gross_exposure / gross
    return projected


def one_way_turnover(old_weights: np.ndarray, new_weights: np.ndarray) -> float:
    """Turnover including the cash leg, so buys and sells are counted once."""

    old = np.asarray(old_weights, dtype=np.float64).reshape(-1)
    new = np.asarray(new_weights, dtype=np.float64).reshape(-1)
    if old.shape != new.shape:
        raise ValueError("weight vectors must have the same shape")
    old_cash = 1.0 - float(old.sum())
    new_cash = 1.0 - float(new.sum())
    return float(0.5 * (np.abs(new - old).sum() + abs(new_cash - old_cash)))


class CausalMultiAssetPortfolioEnvV221:
    """Dependency-light portfolio simulator for RL research.

    The environment owns accounting, costs and hard constraints. Policies only
    propose target weights. It has no broker, order or live execution interface.
    """

    metadata: ClassVar[dict[str, object]] = {
        "version": "v2.21",
        "deployment_mode": DEPLOYMENT_MODE,
        "execution_authority": EXECUTION_AUTHORITY,
        "broker_calls": 0,
        "order_calls": 0,
    }

    def __init__(
        self,
        episode: PortfolioEpisodeV221,
        *,
        config: PortfolioEnvironmentConfigV221 | None = None,
    ) -> None:
        self.episode = episode
        self.config = config or PortfolioEnvironmentConfigV221()
        self._rng = np.random.default_rng(0)
        self.reset()

    def reset(self, *, seed: int | None = None) -> PortfolioObservationV221:
        if seed is not None:
            self._rng = np.random.default_rng(int(seed))
        self._step = 0
        self._weights = np.zeros(self.episode.assets, dtype=np.float64)
        self._cash_weight = 1.0
        self._equity = float(self.config.initial_equity)
        self._peak_equity = self._equity
        self._cumulative_cost = 0.0
        self._terminated = False
        return self.observe()

    def observe(self) -> PortfolioObservationV221:
        index = self._step
        drawdown = 1.0 - self._equity / max(self._peak_equity, 1e-12)
        return PortfolioObservationV221(
            local=self.episode.local_observations[index].copy(),
            global_context=self.episode.global_observations[index].copy(),
            tradable_mask=self.episode.tradable_mask[index].copy(),
            portfolio_weights=self._weights.astype(np.float32, copy=True),
            cash_weight=float(self._cash_weight),
            equity=float(self._equity),
            drawdown=float(drawdown),
        )

    def _counterfactual_rewards(
        self,
        *,
        target: np.ndarray,
        asset_returns: np.ndarray,
        team_reward: float,
    ) -> np.ndarray:
        contribution = target * asset_returns
        normalized = contribution / self.config.return_normalizer
        return (
            self.config.team_reward_share * team_reward
            + self.config.counterfactual_reward_share * normalized
        ).astype(np.float32)

    def step(self, actions: np.ndarray) -> PortfolioStepV221:
        if self._terminated:
            raise RuntimeError("episode is finished; call reset before step")

        index = self._step
        mask = self.episode.tradable_mask[index]
        target = project_long_only_weights(
            actions,
            mask,
            max_asset_weight=self.config.max_asset_weight,
            max_gross_exposure=self.config.max_gross_exposure,
        )
        turnover = one_way_turnover(self._weights, target)
        transaction_cost = turnover * self.config.one_way_cost_rate
        cash_before_return = 1.0 - float(target.sum()) - transaction_cost
        if cash_before_return < -1e-12:
            raise RuntimeError("cost assumptions exceed the reserved cash buffer")

        asset_returns = self.episode.asset_returns[index]
        benchmark_return = float(self.episode.benchmark_returns[index])
        gross_return = float(np.dot(target, asset_returns))
        net_return = gross_return - transaction_cost
        if net_return <= -1.0:
            raise RuntimeError("portfolio loss exceeded total equity")

        previous_equity = self._equity
        self._equity = previous_equity * (1.0 + net_return)
        self._peak_equity = max(self._peak_equity, self._equity)
        drawdown = 1.0 - self._equity / max(self._peak_equity, 1e-12)

        excess_log_return = np.log1p(net_return) - np.log1p(benchmark_return)
        concentration_excess = np.maximum(
            target - self.config.concentration_soft_limit,
            0.0,
        ).sum()
        drawdown_excess = max(drawdown - self.config.drawdown_soft_limit, 0.0)
        drawdown_penalty = self.config.drawdown_penalty * drawdown_excess
        turnover_penalty = self.config.turnover_penalty * turnover
        soft_risk_penalty = self.config.soft_risk_penalty * float(concentration_excess)
        team_reward = float(
            excess_log_return / self.config.return_normalizer
            - drawdown_penalty
            - turnover_penalty
            - soft_risk_penalty
        )
        agent_rewards = self._counterfactual_rewards(
            target=target,
            asset_returns=asset_returns,
            team_reward=team_reward,
        )

        denominator = 1.0 + net_return
        next_weights = target * (1.0 + asset_returns) / denominator
        next_cash = max(cash_before_return, 0.0) / denominator
        total_weight = float(next_weights.sum() + next_cash)
        if not np.isclose(total_weight, 1.0, atol=1e-9):
            raise RuntimeError("portfolio accounting did not reconcile")

        self._weights = next_weights
        self._cash_weight = next_cash
        self._cumulative_cost += previous_equity * transaction_cost
        self._step += 1
        hard_drawdown = drawdown >= self.config.drawdown_hard_limit
        exhausted = self._step >= self.episode.steps
        self._terminated = bool(hard_drawdown or exhausted)

        info: dict[str, object] = {
            "step": index,
            "target_weights": target.astype(np.float32),
            "gross_exposure": float(target.sum()),
            "turnover": turnover,
            "transaction_cost": transaction_cost,
            "gross_return": gross_return,
            "net_return": net_return,
            "benchmark_return": benchmark_return,
            "excess_log_return": float(excess_log_return),
            "equity": float(self._equity),
            "drawdown": float(drawdown),
            "cumulative_cost": float(self._cumulative_cost),
            "hard_drawdown_stop": bool(hard_drawdown),
            "deployment_mode": DEPLOYMENT_MODE,
            "execution_authority": EXECUTION_AUTHORITY,
            "broker_calls": 0,
            "order_calls": 0,
        }
        return PortfolioStepV221(
            observation=self.observe(),
            agent_rewards=agent_rewards,
            team_reward=team_reward,
            terminated=bool(hard_drawdown),
            truncated=bool(exhausted and not hard_drawdown),
            info=info,
        )
