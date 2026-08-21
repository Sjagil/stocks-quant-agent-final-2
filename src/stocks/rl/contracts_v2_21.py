from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

EXECUTION_AUTHORITY = "NONE"
DEPLOYMENT_MODE = "SHADOW_ONLY"


@dataclass(frozen=True)
class PortfolioEpisodeV221:
    """Point-in-time tensors for one causal multi-asset episode.

    ``asset_returns[t]`` is the return realized between observation rows ``t``
    and ``t + 1``. Observation and tradability tensors therefore contain one
    more row than return tensors. Features must contain only information
    available at ``timestamps[t]``.
    """

    local_observations: np.ndarray
    global_observations: np.ndarray
    asset_returns: np.ndarray
    benchmark_returns: np.ndarray
    tradable_mask: np.ndarray
    timestamps: np.ndarray | None = None
    feature_cutoffs: np.ndarray | None = None

    def __post_init__(self) -> None:
        local = np.asarray(self.local_observations, dtype=np.float32)
        global_obs = np.asarray(self.global_observations, dtype=np.float32)
        returns = np.asarray(self.asset_returns, dtype=np.float64)
        benchmark = np.asarray(self.benchmark_returns, dtype=np.float64)
        mask = np.asarray(self.tradable_mask, dtype=bool)

        if local.ndim != 3:
            raise ValueError(
                "local_observations must have shape [time, asset, feature]"
            )
        if global_obs.ndim != 2:
            raise ValueError("global_observations must have shape [time, feature]")
        if returns.ndim != 2:
            raise ValueError("asset_returns must have shape [time, asset]")
        expected_observation_shape = (returns.shape[0] + 1, returns.shape[1])
        if mask.shape != expected_observation_shape:
            raise ValueError("tradable_mask must have shape [return_time + 1, asset]")
        if local.shape[:2] != expected_observation_shape:
            raise ValueError(
                "local observations must have shape [return_time + 1, asset, feature]"
            )
        if global_obs.shape[0] != returns.shape[0] + 1:
            raise ValueError("global observations need one row beyond the return axis")
        if benchmark.shape != (returns.shape[0],):
            raise ValueError("benchmark_returns must have shape [time]")
        if returns.shape[0] < 2 or returns.shape[1] < 1:
            raise ValueError("episode must contain at least two rows and one asset")
        if not np.isfinite(local).all() or not np.isfinite(global_obs).all():
            raise ValueError("observations must be finite")
        if not np.isfinite(returns).all() or not np.isfinite(benchmark).all():
            raise ValueError("returns must be finite")
        if np.any(returns <= -1.0) or np.any(benchmark <= -1.0):
            raise ValueError("simple returns must be greater than -1")

        if self.timestamps is not None:
            timestamps = np.asarray(self.timestamps)
            if timestamps.shape != (returns.shape[0] + 1,):
                raise ValueError("timestamps must have shape [return_time + 1]")
            if len(timestamps) > 1 and np.any(timestamps[1:] <= timestamps[:-1]):
                raise ValueError("timestamps must be strictly increasing")
        if self.feature_cutoffs is not None:
            if self.timestamps is None:
                raise ValueError("feature_cutoffs require timestamps")
            cutoffs = np.asarray(self.feature_cutoffs)
            timestamps = np.asarray(self.timestamps)
            if cutoffs.shape != timestamps.shape:
                raise ValueError("feature_cutoffs must have shape [time]")
            if np.any(cutoffs > timestamps):
                raise ValueError(
                    "feature cutoff after decision time would introduce lookahead"
                )

        object.__setattr__(self, "local_observations", local)
        object.__setattr__(self, "global_observations", global_obs)
        object.__setattr__(self, "asset_returns", returns)
        object.__setattr__(self, "benchmark_returns", benchmark)
        object.__setattr__(self, "tradable_mask", mask)

    @property
    def steps(self) -> int:
        return int(self.asset_returns.shape[0])

    @property
    def assets(self) -> int:
        return int(self.asset_returns.shape[1])


@dataclass(frozen=True)
class PortfolioEnvironmentConfigV221:
    initial_equity: float = 1_000_000.0
    max_asset_weight: float = 0.30
    max_gross_exposure: float = 0.98
    transaction_cost_bps: float = 4.0
    slippage_bps: float = 4.0
    return_normalizer: float = 0.01
    drawdown_soft_limit: float = 0.05
    drawdown_hard_limit: float = 0.10
    drawdown_penalty: float = 0.25
    turnover_penalty: float = 0.05
    concentration_soft_limit: float = 0.25
    soft_risk_penalty: float = 0.10
    team_reward_share: float = 0.75
    counterfactual_reward_share: float = 0.25

    def __post_init__(self) -> None:
        if self.initial_equity <= 0:
            raise ValueError("initial_equity must be positive")
        if not 0 < self.max_asset_weight <= 1:
            raise ValueError("max_asset_weight must be in (0, 1]")
        if not 0 < self.max_gross_exposure < 1:
            raise ValueError("max_gross_exposure must be in (0, 1)")
        if self.transaction_cost_bps < 0 or self.slippage_bps < 0:
            raise ValueError("cost assumptions cannot be negative")
        if self.return_normalizer <= 0:
            raise ValueError("return_normalizer must be positive")
        if not 0 <= self.drawdown_soft_limit < self.drawdown_hard_limit < 1:
            raise ValueError("drawdown limits must be ordered inside [0, 1)")
        if not 0 <= self.concentration_soft_limit <= self.max_asset_weight:
            raise ValueError(
                "concentration_soft_limit must not exceed max_asset_weight"
            )
        if (
            min(
                self.drawdown_penalty,
                self.turnover_penalty,
                self.soft_risk_penalty,
            )
            < 0
        ):
            raise ValueError("reward penalties cannot be negative")
        if not np.isclose(
            self.team_reward_share + self.counterfactual_reward_share,
            1.0,
        ):
            raise ValueError("team and counterfactual reward shares must sum to one")

    @property
    def one_way_cost_rate(self) -> float:
        return (self.transaction_cost_bps + self.slippage_bps) / 10_000.0


@dataclass(frozen=True)
class MAPPOConfigV221:
    local_observation_dim: int
    global_observation_dim: int
    actor_hidden_dims: tuple[int, ...] = (128, 128)
    critic_hidden_dims: tuple[int, ...] = (256, 256)
    actor_learning_rate: float = 1e-4
    critic_learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_ratio: float = 0.10
    update_epochs: int = 5
    entropy_coefficient: float = 0.001
    value_coefficient: float = 0.5
    max_gradient_norm: float = 0.5
    target_kl: float = 0.02
    normalize_advantages: bool = True
    normalize_value_targets: bool = True

    def __post_init__(self) -> None:
        if self.local_observation_dim < 1 or self.global_observation_dim < 1:
            raise ValueError("observation dimensions must be positive")
        if not self.actor_hidden_dims or not self.critic_hidden_dims:
            raise ValueError("actor and critic need at least one hidden layer")
        if min(*self.actor_hidden_dims, *self.critic_hidden_dims) < 1:
            raise ValueError("hidden layer dimensions must be positive")
        if self.actor_learning_rate <= 0 or self.critic_learning_rate <= 0:
            raise ValueError("learning rates must be positive")
        if not 0 < self.gamma <= 1 or not 0 <= self.gae_lambda <= 1:
            raise ValueError("invalid discount or GAE lambda")
        if not 0 < self.clip_ratio < 1 or self.update_epochs < 1:
            raise ValueError("invalid PPO update settings")
        if self.entropy_coefficient < 0 or self.value_coefficient < 0:
            raise ValueError("loss coefficients cannot be negative")
        if self.max_gradient_norm <= 0 or self.target_kl <= 0:
            raise ValueError("gradient norm and target KL must be positive")


@dataclass(frozen=True)
class MATD3ConfigV221:
    agents: int
    local_observation_dim: int
    global_observation_dim: int
    hidden_dims: tuple[int, ...] = (256, 256)
    actor_learning_rate: float = 1e-4
    critic_learning_rate: float = 3e-4
    gamma: float = 0.99
    tau: float = 0.005
    policy_delay: int = 2
    target_noise: float = 0.20
    target_noise_clip: float = 0.50

    def __post_init__(self) -> None:
        if (
            min(self.agents, self.local_observation_dim, self.global_observation_dim)
            < 1
        ):
            raise ValueError("agent and observation dimensions must be positive")
        if not self.hidden_dims or min(self.hidden_dims) < 1:
            raise ValueError("hidden dimensions must be positive")
        if self.actor_learning_rate <= 0 or self.critic_learning_rate <= 0:
            raise ValueError("learning rates must be positive")
        if not 0 < self.gamma <= 1 or not 0 < self.tau <= 1:
            raise ValueError("invalid discount or Polyak factor")
        if self.policy_delay < 1:
            raise ValueError("policy_delay must be positive")
        if self.target_noise < 0 or self.target_noise_clip < 0:
            raise ValueError("target noise settings cannot be negative")


@dataclass(frozen=True)
class PromotionPolicyV221:
    required_seeds: tuple[int, ...] = field(default_factory=lambda: tuple(range(10)))
    minimum_positive_fold_ratio: float = 0.75
    minimum_seed_wins: int = 7
    minimum_deflated_sharpe_probability: float = 0.95
    minimum_expectancy_ci_lower_bps: float = 0.0
    maximum_drawdown: float = 0.10
    maximum_concentration: float = 0.30
    minimum_cost_stress_return: float = 0.0
    minimum_severe_stress_return: float = -0.02

    def __post_init__(self) -> None:
        if len(self.required_seeds) != 10 or len(set(self.required_seeds)) != 10:
            raise ValueError("promotion requires exactly ten unique seeds")
        if not 0 <= self.minimum_positive_fold_ratio <= 1:
            raise ValueError("minimum_positive_fold_ratio must be in [0, 1]")
        if not 0 <= self.minimum_seed_wins <= len(self.required_seeds):
            raise ValueError("minimum_seed_wins is outside the seed count")
        if not 0 <= self.minimum_deflated_sharpe_probability <= 1:
            raise ValueError("deflated Sharpe probability must be in [0, 1]")
        if not 0 < self.maximum_drawdown < 1:
            raise ValueError("maximum_drawdown must be in (0, 1)")
        if not 0 < self.maximum_concentration <= 1:
            raise ValueError("maximum_concentration must be in (0, 1]")
