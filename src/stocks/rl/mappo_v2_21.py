from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .contracts_v2_21 import DEPLOYMENT_MODE, EXECUTION_AUTHORITY, MAPPOConfigV221

try:  # Optional research dependency.
    import torch
    from torch import nn
    from torch.distributions import Beta
except ImportError:  # pragma: no cover
    torch = None
    nn = None
    Beta = None


def _require_torch() -> None:
    if torch is None or nn is None or Beta is None:
        raise ImportError("MAPPO v2.21 requires PyTorch; install the 'rl' extra")


def seed_everything_v221(seed: int) -> np.random.Generator:
    """Seed NumPy and PyTorch without changing execution authority."""

    value = int(seed)
    rng = np.random.default_rng(value)
    if torch is not None:
        torch.manual_seed(value)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(value)
        if hasattr(torch, "use_deterministic_algorithms"):
            torch.use_deterministic_algorithms(True, warn_only=True)
    return rng


def generalized_advantage_estimate(
    *,
    rewards: np.ndarray,
    values: np.ndarray,
    next_values: np.ndarray,
    terminated: np.ndarray,
    truncated: np.ndarray,
    gamma: float,
    gae_lambda: float,
) -> np.ndarray:
    """Compute GAE with correct termination and truncation semantics.

    A time-limit truncation bootstraps the delta from ``next_values`` but stops
    recursive advantage carry into the next reset episode. A true termination
    does neither.
    """

    rewards_array = np.asarray(rewards, dtype=np.float64)
    values_array = np.asarray(values, dtype=np.float64)
    next_array = np.asarray(next_values, dtype=np.float64)
    terminated_array = np.asarray(terminated, dtype=bool)
    truncated_array = np.asarray(truncated, dtype=bool)
    if (
        rewards_array.shape != values_array.shape
        or rewards_array.shape != next_array.shape
    ):
        raise ValueError("rewards, values and next_values must have equal shapes")
    if rewards_array.ndim != 2:
        raise ValueError("GAE inputs must have shape [time, agent]")
    if terminated_array.shape != (rewards_array.shape[0],):
        raise ValueError("terminated must have shape [time]")
    if truncated_array.shape != terminated_array.shape:
        raise ValueError("truncated must match terminated")

    advantages = np.zeros_like(rewards_array)
    accumulator = np.zeros(rewards_array.shape[1], dtype=np.float64)
    for index in range(rewards_array.shape[0] - 1, -1, -1):
        bootstrap = 0.0 if terminated_array[index] else 1.0
        continue_episode = (
            0.0 if (terminated_array[index] or truncated_array[index]) else 1.0
        )
        delta = (
            rewards_array[index]
            + gamma * next_array[index] * bootstrap
            - values_array[index]
        )
        accumulator = delta + gamma * gae_lambda * continue_episode * accumulator
        advantages[index] = accumulator
    return advantages.astype(np.float32)


@dataclass(frozen=True)
class MAPPORolloutTransitionV221:
    local_observations: np.ndarray
    global_observation: np.ndarray
    eligible_mask: np.ndarray
    actions: np.ndarray
    log_probabilities: np.ndarray
    rewards: np.ndarray
    value: float
    terminated: bool
    truncated: bool


class MAPPORolloutBufferV221:
    """On-policy rollout storage with no replay across policy versions."""

    def __init__(self) -> None:
        self._items: list[MAPPORolloutTransitionV221] = []

    def __len__(self) -> int:
        return len(self._items)

    def add(self, transition: MAPPORolloutTransitionV221) -> None:
        local = np.asarray(transition.local_observations, dtype=np.float32)
        mask = np.asarray(transition.eligible_mask, dtype=bool)
        actions = np.asarray(transition.actions, dtype=np.float32)
        log_probs = np.asarray(transition.log_probabilities, dtype=np.float32)
        rewards = np.asarray(transition.rewards, dtype=np.float32)
        if local.ndim != 2:
            raise ValueError("local observations must have shape [agent, feature]")
        expected = (local.shape[0],)
        if any(
            array.shape != expected for array in (mask, actions, log_probs, rewards)
        ):
            raise ValueError(
                "agent tensors must share the local observation agent axis"
            )
        if not np.isfinite(local).all() or not all(
            np.isfinite(array).all() for array in (actions, log_probs, rewards)
        ):
            raise ValueError("rollout tensors must be finite")
        self._items.append(
            MAPPORolloutTransitionV221(
                local_observations=local.copy(),
                global_observation=np.asarray(
                    transition.global_observation,
                    dtype=np.float32,
                ).copy(),
                eligible_mask=mask.copy(),
                actions=actions.copy(),
                log_probabilities=log_probs.copy(),
                rewards=rewards.copy(),
                value=float(transition.value),
                terminated=bool(transition.terminated),
                truncated=bool(transition.truncated),
            )
        )

    def training_batch(
        self,
        *,
        last_value: float,
        gamma: float,
        gae_lambda: float,
    ) -> dict[str, np.ndarray]:
        if not self._items:
            raise ValueError("cannot build a batch from an empty rollout")
        local = np.stack([item.local_observations for item in self._items])
        global_obs = np.stack([item.global_observation for item in self._items])
        masks = np.stack([item.eligible_mask for item in self._items])
        actions = np.stack([item.actions for item in self._items])
        log_probs = np.stack([item.log_probabilities for item in self._items])
        rewards = np.stack([item.rewards for item in self._items])
        values_1d = np.asarray([item.value for item in self._items], dtype=np.float32)
        values = np.repeat(values_1d[:, None], rewards.shape[1], axis=1)
        next_1d = np.concatenate(
            [values_1d[1:], np.asarray([last_value], dtype=np.float32)]
        )
        next_values = np.repeat(next_1d[:, None], rewards.shape[1], axis=1)
        terminated = np.asarray([item.terminated for item in self._items], dtype=bool)
        truncated = np.asarray([item.truncated for item in self._items], dtype=bool)
        advantages = generalized_advantage_estimate(
            rewards=rewards,
            values=values,
            next_values=next_values,
            terminated=terminated,
            truncated=truncated,
            gamma=gamma,
            gae_lambda=gae_lambda,
        )
        return {
            "local_observations": local,
            "global_observations": global_obs,
            "eligible_mask": masks,
            "actions": actions,
            "old_log_probabilities": log_probs,
            "advantages": advantages,
            "returns": advantages + values,
            "old_values": values_1d,
        }

    def clear(self) -> None:
        self._items.clear()


if nn is not None:

    class _MLPV221(nn.Module):
        def __init__(
            self, input_dim: int, hidden_dims: tuple[int, ...], output_dim: int
        ):
            super().__init__()
            layers: list[nn.Module] = []
            previous = input_dim
            for width in hidden_dims:
                layers.extend([nn.Linear(previous, width), nn.Tanh()])
                previous = width
            layers.append(nn.Linear(previous, output_dim))
            self.network = nn.Sequential(*layers)

        def forward(self, inputs):
            return self.network(inputs)

    class SharedBetaActorV221(nn.Module):
        """One decentralized actor shared by every asset."""

        def __init__(self, config: MAPPOConfigV221):
            super().__init__()
            self.config = config
            self.policy = _MLPV221(
                config.local_observation_dim,
                config.actor_hidden_dims,
                2,
            )

        def distribution(self, local_observations):
            parameters = self.policy(local_observations)
            concentrations = torch.nn.functional.softplus(parameters) + 1.01
            return Beta(concentrations[..., 0], concentrations[..., 1])

        def forward(self, local_observations, *, deterministic: bool = False):
            distribution = self.distribution(local_observations)
            if deterministic:
                alpha = distribution.concentration1
                beta = distribution.concentration0
                actions = (alpha - 1.0) / (alpha + beta - 2.0)
            else:
                actions = distribution.rsample()
            actions = actions.clamp(1e-6, 1.0 - 1e-6)
            return actions, distribution.log_prob(actions), distribution.entropy()

        def evaluate_actions(self, local_observations, actions):
            distribution = self.distribution(local_observations)
            safe_actions = actions.clamp(1e-6, 1.0 - 1e-6)
            return distribution.log_prob(safe_actions), distribution.entropy()

    class CentralizedValueCriticV221(nn.Module):
        """Centralized state-value critic with masked asset pooling.

        Actions are intentionally absent from the signature and input tensor.
        """

        def __init__(self, config: MAPPOConfigV221):
            super().__init__()
            embedding_dim = config.critic_hidden_dims[0]
            self.asset_encoder = _MLPV221(
                config.local_observation_dim,
                (embedding_dim,),
                embedding_dim,
            )
            self.value = _MLPV221(
                embedding_dim + config.global_observation_dim,
                config.critic_hidden_dims,
                1,
            )

        def forward(self, local_observations, global_observations, eligible_mask):
            encoded = self.asset_encoder(local_observations)
            mask = eligible_mask.to(encoded.dtype).unsqueeze(-1)
            denominator = mask.sum(dim=1).clamp_min(1.0)
            pooled = (encoded * mask).sum(dim=1) / denominator
            critic_input = torch.cat([pooled, global_observations], dim=-1)
            return self.value(critic_input).squeeze(-1)

else:

    class SharedBetaActorV221:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            _require_torch()

    class CentralizedValueCriticV221:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            _require_torch()


@dataclass(frozen=True)
class MAPPOActionV221:
    actions: np.ndarray
    log_probabilities: np.ndarray
    value: float


class MAPPOTrainerV221:
    """MAPPO update loop with decentralized actors and centralized value critic."""

    def __init__(
        self,
        config: MAPPOConfigV221,
        *,
        seed: int = 0,
        device: str = "cpu",
    ) -> None:
        _require_torch()
        seed_everything_v221(seed)
        self.config = config
        self.device = torch.device(device)
        self.actor = SharedBetaActorV221(config).to(self.device)
        self.critic = CentralizedValueCriticV221(config).to(self.device)
        self.actor_optimizer = torch.optim.Adam(
            self.actor.parameters(),
            lr=config.actor_learning_rate,
        )
        self.critic_optimizer = torch.optim.Adam(
            self.critic.parameters(),
            lr=config.critic_learning_rate,
        )

    def act(
        self,
        local_observations: np.ndarray,
        global_observation: np.ndarray,
        eligible_mask: np.ndarray,
        *,
        deterministic: bool = False,
    ) -> MAPPOActionV221:
        local = torch.as_tensor(
            local_observations,
            dtype=torch.float32,
            device=self.device,
        )
        global_obs = torch.as_tensor(
            global_observation,
            dtype=torch.float32,
            device=self.device,
        )
        mask = torch.as_tensor(eligible_mask, dtype=torch.bool, device=self.device)
        if local.ndim != 2 or global_obs.ndim != 1 or mask.shape != local.shape[:1]:
            raise ValueError("invalid observation shapes for MAPPO action")
        with torch.no_grad():
            actions, log_probs, _ = self.actor(local, deterministic=deterministic)
            actions = torch.where(mask, actions, torch.zeros_like(actions))
            log_probs = torch.where(mask, log_probs, torch.zeros_like(log_probs))
            value = self.critic(
                local.unsqueeze(0),
                global_obs.unsqueeze(0),
                mask.unsqueeze(0),
            )[0]
        return MAPPOActionV221(
            actions=actions.cpu().numpy().astype(np.float32),
            log_probabilities=log_probs.cpu().numpy().astype(np.float32),
            value=float(value.cpu()),
        )

    def update(self, batch: dict[str, np.ndarray]) -> dict[str, float | int | bool]:
        required = {
            "local_observations",
            "global_observations",
            "eligible_mask",
            "actions",
            "old_log_probabilities",
            "advantages",
            "returns",
            "old_values",
        }
        missing = sorted(required - set(batch))
        if missing:
            raise ValueError(f"MAPPO batch missing fields: {missing}")

        local = torch.as_tensor(
            batch["local_observations"],
            dtype=torch.float32,
            device=self.device,
        )
        global_obs = torch.as_tensor(
            batch["global_observations"],
            dtype=torch.float32,
            device=self.device,
        )
        eligible = torch.as_tensor(
            batch["eligible_mask"],
            dtype=torch.bool,
            device=self.device,
        )
        actions = torch.as_tensor(
            batch["actions"], dtype=torch.float32, device=self.device
        )
        old_log_probs = torch.as_tensor(
            batch["old_log_probabilities"],
            dtype=torch.float32,
            device=self.device,
        )
        advantages = torch.as_tensor(
            batch["advantages"],
            dtype=torch.float32,
            device=self.device,
        )
        returns = torch.as_tensor(
            batch["returns"], dtype=torch.float32, device=self.device
        )
        old_values = torch.as_tensor(
            batch["old_values"],
            dtype=torch.float32,
            device=self.device,
        )
        if local.ndim != 3 or eligible.shape != local.shape[:2]:
            raise ValueError(
                "local observations must have shape [time, agent, feature]"
            )
        if any(
            tensor.shape != eligible.shape
            for tensor in (actions, old_log_probs, advantages, returns)
        ):
            raise ValueError("policy tensors must match the time and agent axes")
        if global_obs.shape[0] != local.shape[0] or old_values.shape != (
            local.shape[0],
        ):
            raise ValueError("critic tensors must match the rollout time axis")
        if not bool(eligible.any()):
            raise ValueError("rollout has no eligible policy samples")
        numeric_tensors = (
            local,
            global_obs,
            actions,
            old_log_probs,
            advantages,
            returns,
            old_values,
        )
        if not all(bool(torch.isfinite(value).all()) for value in numeric_tensors):
            raise ValueError("MAPPO batch contains non-finite values")

        actor_local = local[eligible]
        actor_actions = actions[eligible]
        actor_old_log_probs = old_log_probs[eligible]
        actor_advantages = advantages[eligible]
        if self.config.normalize_advantages:
            actor_advantages = (actor_advantages - actor_advantages.mean()) / (
                actor_advantages.std(unbiased=False) + 1e-8
            )

        eligible_float = eligible.to(returns.dtype)
        critic_targets = (returns * eligible_float).sum(dim=1) / eligible_float.sum(
            dim=1
        ).clamp_min(1.0)
        final_metrics: dict[str, float | int | bool] = {}
        early_stopped = False
        epochs_completed = 0
        for epoch in range(self.config.update_epochs):
            new_log_probs, entropy = self.actor.evaluate_actions(
                actor_local, actor_actions
            )
            log_ratio = new_log_probs - actor_old_log_probs
            ratio = log_ratio.exp()
            unclipped = ratio * actor_advantages
            clipped = (
                ratio.clamp(
                    1.0 - self.config.clip_ratio,
                    1.0 + self.config.clip_ratio,
                )
                * actor_advantages
            )
            policy_loss = -torch.minimum(unclipped, clipped).mean()
            entropy_mean = entropy.mean()
            actor_loss = policy_loss - self.config.entropy_coefficient * entropy_mean

            self.actor_optimizer.zero_grad(set_to_none=True)
            actor_loss.backward()
            actor_grad_norm = torch.nn.utils.clip_grad_norm_(
                self.actor.parameters(),
                self.config.max_gradient_norm,
            )
            self.actor_optimizer.step()

            predicted_values = self.critic(local, global_obs, eligible)
            clipped_values = old_values + (predicted_values - old_values).clamp(
                -self.config.clip_ratio,
                self.config.clip_ratio,
            )
            if self.config.normalize_value_targets:
                target_mean = critic_targets.mean()
                target_std = critic_targets.std(unbiased=False).clamp_min(1e-4)
                error = (predicted_values - target_mean) / target_std - (
                    critic_targets - target_mean
                ) / target_std
                clipped_error = (clipped_values - target_mean) / target_std - (
                    critic_targets - target_mean
                ) / target_std
            else:
                error = predicted_values - critic_targets
                clipped_error = clipped_values - critic_targets
            value_loss = (
                0.5 * torch.maximum(error.square(), clipped_error.square()).mean()
            )
            critic_loss = self.config.value_coefficient * value_loss

            self.critic_optimizer.zero_grad(set_to_none=True)
            critic_loss.backward()
            critic_grad_norm = torch.nn.utils.clip_grad_norm_(
                self.critic.parameters(),
                self.config.max_gradient_norm,
            )
            self.critic_optimizer.step()

            approximate_kl = float(((ratio - 1.0) - log_ratio).mean().detach().cpu())
            clip_fraction = float(
                ((ratio - 1.0).abs() > self.config.clip_ratio)
                .to(torch.float32)
                .mean()
                .detach()
                .cpu()
            )
            epochs_completed = epoch + 1
            final_metrics = {
                "policy_loss": float(policy_loss.detach().cpu()),
                "value_loss": float(value_loss.detach().cpu()),
                "entropy": float(entropy_mean.detach().cpu()),
                "approximate_kl": approximate_kl,
                "clip_fraction": clip_fraction,
                "actor_gradient_norm": float(actor_grad_norm.detach().cpu()),
                "critic_gradient_norm": float(critic_grad_norm.detach().cpu()),
            }
            if approximate_kl > self.config.target_kl:
                early_stopped = True
                break

        final_metrics.update(
            {
                "epochs_completed": epochs_completed,
                "early_stopped_for_kl": early_stopped,
                "policy_samples": int(eligible.sum().detach().cpu()),
            }
        )
        return final_metrics

    def manifest(self) -> dict[str, Any]:
        return {
            "algorithm": "MAPPO",
            "version": "v2.21",
            "centralized_value_critic": True,
            "decentralized_shared_actor": True,
            "off_policy_replay": False,
            "configuration": asdict(self.config),
            "deployment_mode": DEPLOYMENT_MODE,
            "automatic_live_promotion": False,
            "execution_authority": EXECUTION_AUTHORITY,
            "broker_calls": 0,
            "order_calls": 0,
        }
