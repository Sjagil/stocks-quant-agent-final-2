from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .contracts_v2_21 import DEPLOYMENT_MODE, EXECUTION_AUTHORITY, MATD3ConfigV221
from .mappo_v2_21 import _require_torch, seed_everything_v221

try:  # Optional research dependency.
    import torch
    from torch import nn
except ImportError:  # pragma: no cover
    torch = None
    nn = None


@dataclass(frozen=True)
class MATD3TransitionV221:
    local_observations: np.ndarray
    global_observation: np.ndarray
    eligible_mask: np.ndarray
    actions: np.ndarray
    reward: float
    next_local_observations: np.ndarray
    next_global_observation: np.ndarray
    next_eligible_mask: np.ndarray
    terminated: bool


class MATD3ReplayBufferV221:
    """Fixed-size off-policy buffer used only by the MATD3 benchmark."""

    def __init__(self, capacity: int, *, seed: int = 0) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = int(capacity)
        self._rng = np.random.default_rng(int(seed))
        self._items: list[MATD3TransitionV221] = []
        self._cursor = 0

    def __len__(self) -> int:
        return len(self._items)

    def add(self, transition: MATD3TransitionV221) -> None:
        local = np.asarray(transition.local_observations, dtype=np.float32)
        next_local = np.asarray(transition.next_local_observations, dtype=np.float32)
        mask = np.asarray(transition.eligible_mask, dtype=bool)
        next_mask = np.asarray(transition.next_eligible_mask, dtype=bool)
        actions = np.asarray(transition.actions, dtype=np.float32)
        if local.ndim != 2 or next_local.shape != local.shape:
            raise ValueError("local observations must share shape [agent, feature]")
        if any(
            array.shape != (local.shape[0],) for array in (mask, next_mask, actions)
        ):
            raise ValueError("mask and action arrays must match the agent axis")
        clean = MATD3TransitionV221(
            local_observations=local.copy(),
            global_observation=np.asarray(
                transition.global_observation,
                dtype=np.float32,
            ).copy(),
            eligible_mask=mask.copy(),
            actions=actions.copy(),
            reward=float(transition.reward),
            next_local_observations=next_local.copy(),
            next_global_observation=np.asarray(
                transition.next_global_observation,
                dtype=np.float32,
            ).copy(),
            next_eligible_mask=next_mask.copy(),
            terminated=bool(transition.terminated),
        )
        if len(self._items) < self.capacity:
            self._items.append(clean)
        else:
            self._items[self._cursor] = clean
        self._cursor = (self._cursor + 1) % self.capacity

    def sample(self, batch_size: int) -> dict[str, np.ndarray]:
        if batch_size < 1 or batch_size > len(self._items):
            raise ValueError("batch_size must be inside the stored transition count")
        indices = self._rng.choice(len(self._items), size=batch_size, replace=False)
        items = [self._items[int(index)] for index in indices]
        return {
            "local_observations": np.stack([item.local_observations for item in items]),
            "global_observations": np.stack(
                [item.global_observation for item in items]
            ),
            "eligible_mask": np.stack([item.eligible_mask for item in items]),
            "actions": np.stack([item.actions for item in items]),
            "rewards": np.asarray([item.reward for item in items], dtype=np.float32),
            "next_local_observations": np.stack(
                [item.next_local_observations for item in items]
            ),
            "next_global_observations": np.stack(
                [item.next_global_observation for item in items]
            ),
            "next_eligible_mask": np.stack([item.next_eligible_mask for item in items]),
            "terminated": np.asarray(
                [item.terminated for item in items],
                dtype=np.float32,
            ),
        }


if nn is not None:

    class _MLPV221(nn.Module):
        def __init__(
            self, input_dim: int, hidden_dims: tuple[int, ...], output_dim: int
        ):
            super().__init__()
            layers: list[nn.Module] = []
            previous = input_dim
            for width in hidden_dims:
                layers.extend([nn.Linear(previous, width), nn.ReLU()])
                previous = width
            layers.append(nn.Linear(previous, output_dim))
            self.network = nn.Sequential(*layers)

        def forward(self, inputs):
            return self.network(inputs)

    class SharedDeterministicActorV221(nn.Module):
        """Shared decentralized actor for continuous target-weight scores."""

        def __init__(self, config: MATD3ConfigV221):
            super().__init__()
            self.policy = _MLPV221(
                config.local_observation_dim,
                config.hidden_dims,
                1,
            )

        def forward(self, local_observations, eligible_mask):
            actions = torch.sigmoid(self.policy(local_observations).squeeze(-1))
            return torch.where(eligible_mask, actions, torch.zeros_like(actions))

    class CentralizedTwinCriticV221(nn.Module):
        """Twin centralized action-value critics for clipped double Q learning."""

        def __init__(self, config: MATD3ConfigV221):
            super().__init__()
            state_dim = (
                config.agents * config.local_observation_dim
                + config.global_observation_dim
                + config.agents
            )
            self.q1 = _MLPV221(state_dim, config.hidden_dims, 1)
            self.q2 = _MLPV221(state_dim, config.hidden_dims, 1)

        @staticmethod
        def _inputs(local_observations, global_observations, actions):
            return torch.cat(
                [
                    local_observations.flatten(start_dim=1),
                    global_observations,
                    actions,
                ],
                dim=-1,
            )

        def forward(self, local_observations, global_observations, actions):
            inputs = self._inputs(local_observations, global_observations, actions)
            return self.q1(inputs).squeeze(-1), self.q2(inputs).squeeze(-1)

        def first(self, local_observations, global_observations, actions):
            inputs = self._inputs(local_observations, global_observations, actions)
            return self.q1(inputs).squeeze(-1)

else:

    class SharedDeterministicActorV221:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            _require_torch()

    class CentralizedTwinCriticV221:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            _require_torch()


def clipped_double_q_target(q1, q2):
    """Return the conservative TD3 target used to control overestimation."""

    _require_torch()
    return torch.minimum(q1, q2)


class MATD3BenchmarkV221:
    """Separate MATD3 benchmark with twin critics and delayed policy updates."""

    def __init__(
        self,
        config: MATD3ConfigV221,
        *,
        seed: int = 0,
        device: str = "cpu",
    ) -> None:
        _require_torch()
        seed_everything_v221(seed)
        self.config = config
        self.device = torch.device(device)
        self.actor = SharedDeterministicActorV221(config).to(self.device)
        self.actor_target = SharedDeterministicActorV221(config).to(self.device)
        self.critic = CentralizedTwinCriticV221(config).to(self.device)
        self.critic_target = CentralizedTwinCriticV221(config).to(self.device)
        self.actor_target.load_state_dict(self.actor.state_dict())
        self.critic_target.load_state_dict(self.critic.state_dict())
        self.actor_optimizer = torch.optim.Adam(
            self.actor.parameters(),
            lr=config.actor_learning_rate,
        )
        self.critic_optimizer = torch.optim.Adam(
            self.critic.parameters(),
            lr=config.critic_learning_rate,
        )
        self._updates = 0

    def select_actions(
        self,
        local_observations: np.ndarray,
        eligible_mask: np.ndarray,
        *,
        exploration_noise: float = 0.0,
    ) -> np.ndarray:
        local = torch.as_tensor(
            local_observations,
            dtype=torch.float32,
            device=self.device,
        )
        mask = torch.as_tensor(eligible_mask, dtype=torch.bool, device=self.device)
        if local.shape != (
            self.config.agents,
            self.config.local_observation_dim,
        ) or mask.shape != (self.config.agents,):
            raise ValueError("invalid observation shapes for MATD3 action")
        with torch.no_grad():
            actions = self.actor(local, mask)
            if exploration_noise > 0:
                actions = actions + torch.randn_like(actions) * exploration_noise
            actions = actions.clamp(0.0, 1.0)
            actions = torch.where(mask, actions, torch.zeros_like(actions))
        return actions.cpu().numpy().astype(np.float32)

    def update(self, batch: dict[str, np.ndarray]) -> dict[str, float | bool | int]:
        names = (
            "local_observations",
            "global_observations",
            "eligible_mask",
            "actions",
            "rewards",
            "next_local_observations",
            "next_global_observations",
            "next_eligible_mask",
            "terminated",
        )
        missing = [name for name in names if name not in batch]
        if missing:
            raise ValueError(f"MATD3 batch missing fields: {missing}")

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
        mask = torch.as_tensor(
            batch["eligible_mask"], dtype=torch.bool, device=self.device
        )
        actions = torch.as_tensor(
            batch["actions"], dtype=torch.float32, device=self.device
        )
        rewards = torch.as_tensor(
            batch["rewards"], dtype=torch.float32, device=self.device
        )
        next_local = torch.as_tensor(
            batch["next_local_observations"],
            dtype=torch.float32,
            device=self.device,
        )
        next_global = torch.as_tensor(
            batch["next_global_observations"],
            dtype=torch.float32,
            device=self.device,
        )
        next_mask = torch.as_tensor(
            batch["next_eligible_mask"],
            dtype=torch.bool,
            device=self.device,
        )
        terminated = torch.as_tensor(
            batch["terminated"],
            dtype=torch.float32,
            device=self.device,
        )
        expected_local = (
            local.shape[0],
            self.config.agents,
            self.config.local_observation_dim,
        )
        if local.shape != expected_local or next_local.shape != expected_local:
            raise ValueError("local observations do not match MATD3 configuration")
        if mask.shape != local.shape[:2] or next_mask.shape != local.shape[:2]:
            raise ValueError("eligibility masks do not match the agent axes")
        if actions.shape != local.shape[:2]:
            raise ValueError("joint actions do not match the agent axes")
        if (
            global_obs.shape
            != (
                local.shape[0],
                self.config.global_observation_dim,
            )
            or next_global.shape != global_obs.shape
        ):
            raise ValueError("global observations do not match MATD3 configuration")
        numeric_tensors = (
            local,
            global_obs,
            actions,
            rewards,
            next_local,
            next_global,
            terminated,
        )
        if not all(bool(torch.isfinite(value).all()) for value in numeric_tensors):
            raise ValueError("MATD3 batch contains non-finite values")
        actions = torch.where(mask, actions.clamp(0.0, 1.0), torch.zeros_like(actions))

        with torch.no_grad():
            target_actions = self.actor_target(next_local, next_mask)
            smoothing = torch.randn_like(target_actions) * self.config.target_noise
            smoothing = smoothing.clamp(
                -self.config.target_noise_clip,
                self.config.target_noise_clip,
            )
            target_actions = (target_actions + smoothing).clamp(0.0, 1.0)
            target_actions = torch.where(
                next_mask,
                target_actions,
                torch.zeros_like(target_actions),
            )
            target_q1, target_q2 = self.critic_target(
                next_local,
                next_global,
                target_actions,
            )
            target_q = rewards + self.config.gamma * (
                1.0 - terminated
            ) * clipped_double_q_target(
                target_q1,
                target_q2,
            )

        current_q1, current_q2 = self.critic(local, global_obs, actions)
        critic_loss = torch.nn.functional.mse_loss(
            current_q1,
            target_q,
        ) + torch.nn.functional.mse_loss(current_q2, target_q)
        self.critic_optimizer.zero_grad(set_to_none=True)
        critic_loss.backward()
        self.critic_optimizer.step()

        self._updates += 1
        actor_updated = self._updates % self.config.policy_delay == 0
        actor_loss_value = float("nan")
        if actor_updated:
            policy_actions = self.actor(local, mask)
            actor_loss = -self.critic.first(local, global_obs, policy_actions).mean()
            self.actor_optimizer.zero_grad(set_to_none=True)
            actor_loss.backward()
            self.actor_optimizer.step()
            actor_loss_value = float(actor_loss.detach().cpu())
            self._polyak_update(self.actor, self.actor_target)
            self._polyak_update(self.critic, self.critic_target)

        return {
            "critic_loss": float(critic_loss.detach().cpu()),
            "actor_loss": actor_loss_value,
            "actor_updated": actor_updated,
            "update": self._updates,
            "target_q_mean": float(target_q.mean().detach().cpu()),
        }

    def _polyak_update(self, source, target) -> None:
        with torch.no_grad():
            for source_parameter, target_parameter in zip(
                source.parameters(),
                target.parameters(),
                strict=True,
            ):
                target_parameter.mul_(1.0 - self.config.tau)
                target_parameter.add_(source_parameter, alpha=self.config.tau)

    def manifest(self) -> dict[str, Any]:
        return {
            "algorithm": "MATD3",
            "version": "v2.21",
            "role": "SEPARATE_OFF_POLICY_BENCHMARK",
            "centralized_twin_critics": True,
            "delayed_actor_updates": True,
            "target_policy_smoothing": True,
            "shares_mappo_replay_or_updates": False,
            "configuration": asdict(self.config),
            "deployment_mode": DEPLOYMENT_MODE,
            "automatic_live_promotion": False,
            "execution_authority": EXECUTION_AUTHORITY,
            "broker_calls": 0,
            "order_calls": 0,
        }
