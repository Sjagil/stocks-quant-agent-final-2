from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np


def _torch():
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        from torch.distributions import Beta
    except Exception as exc:  # pragma: no cover
        raise ImportError("torch is required for MAPPO research training") from exc
    return torch, nn, F, Beta


class MAPPOTrainerV240:
    """Small shared-actor/centralized-critic MAPPO research trainer.

    Dataset contract:
      local_obs [T,A,F], global_obs [T,G], actions [T,A] in [0,1],
      rewards [T,A], eligible_mask [T,A].
    It is research-only and produces no execution action by itself.
    """

    def __init__(self, local_dim: int, global_dim: int, *, hidden: int = 128, seed: int = 47):
        torch, nn, _, _ = _torch()
        torch.manual_seed(int(seed))

        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.actor = nn.Sequential(nn.Linear(local_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh())
                self.alpha = nn.Linear(hidden, 1)
                self.beta = nn.Linear(hidden, 1)
                self.critic = nn.Sequential(nn.Linear(global_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 1))

            def actor_params(self, x):
                h = self.actor(x)
                return torch.nn.functional.softplus(self.alpha(h)) + 1.01, torch.nn.functional.softplus(self.beta(h)) + 1.01

            def value(self, g):
                return self.critic(g).squeeze(-1)

        self.torch = torch
        self.nn = nn
        self.net = Net()

    def load(self, path: str | Path) -> bool:
        p = Path(path)
        if not p.is_file():
            return False
        payload = self.torch.load(p, map_location="cpu")
        self.net.load_state_dict(payload["state_dict"])
        return True

    def save(self, path: str | Path, metadata: dict) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + ".tmp")
        self.torch.save({"state_dict": self.net.state_dict(), "metadata": metadata}, tmp)
        os.replace(tmp, p)
        return p

    def train(self, dataset: dict[str, np.ndarray], *, updates: int, learning_rate: float, gamma: float, clip_ratio: float, value_coef: float, entropy_coef: float, max_grad_norm: float) -> dict:
        torch, _, _, Beta = _torch()
        local = torch.as_tensor(dataset["local_obs"], dtype=torch.float32)
        glob = torch.as_tensor(dataset["global_obs"], dtype=torch.float32)
        actions = torch.as_tensor(dataset["actions"], dtype=torch.float32).clamp(1e-4, 1 - 1e-4)
        rewards = torch.as_tensor(dataset["rewards"], dtype=torch.float32)
        mask = torch.as_tensor(dataset["eligible_mask"], dtype=torch.bool)
        if local.ndim != 3 or glob.ndim != 2 or actions.shape != local.shape[:2] or rewards.shape != actions.shape or mask.shape != actions.shape:
            raise ValueError("invalid MAPPO dataset shapes")
        T, A, _ = local.shape
        if glob.shape[0] != T:
            raise ValueError("global observations must align with time")

        with torch.no_grad():
            a0, b0 = self.net.actor_params(local)
            old_dist = Beta(a0.squeeze(-1), b0.squeeze(-1))
            old_logp = old_dist.log_prob(actions)
            values0 = self.net.value(glob)
            global_reward = torch.where(mask, rewards, torch.zeros_like(rewards)).sum(1) / mask.sum(1).clamp(min=1)
            returns = torch.zeros_like(global_reward)
            running = torch.tensor(0.0)
            for t in range(T - 1, -1, -1):
                running = global_reward[t] + float(gamma) * running
                returns[t] = running
            advantage_t = returns - values0
            advantages = advantage_t[:, None].expand(T, A)
            valid_adv = advantages[mask]
            if valid_adv.numel() > 1:
                advantages = (advantages - valid_adv.mean()) / (valid_adv.std(unbiased=False) + 1e-8)

        optimizer = torch.optim.Adam(self.net.parameters(), lr=float(learning_rate))
        last = {}
        for _ in range(int(updates)):
            alpha, beta = self.net.actor_params(local)
            dist = Beta(alpha.squeeze(-1), beta.squeeze(-1))
            logp = dist.log_prob(actions)
            ratio = torch.exp(logp - old_logp)
            clipped = torch.clamp(ratio, 1.0 - float(clip_ratio), 1.0 + float(clip_ratio))
            surrogate = torch.minimum(ratio * advantages, clipped * advantages)
            policy_loss = -surrogate[mask].mean()
            values = self.net.value(glob)
            value_loss = ((values - returns) ** 2).mean()
            entropy = dist.entropy()[mask].mean()
            loss = policy_loss + float(value_coef) * value_loss - float(entropy_coef) * entropy
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.net.parameters(), float(max_grad_norm))
            optimizer.step()
            last = {
                "loss": float(loss.detach()),
                "policy_loss": float(policy_loss.detach()),
                "value_loss": float(value_loss.detach()),
                "entropy": float(entropy.detach()),
            }
        return {**last, "samples": int(T), "agents": int(A), "updates": int(updates), "execution_authority": "NONE"}


def load_mappo_npz_v240(path: str | Path, *, minimum_samples: int = 512) -> dict[str, np.ndarray]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    with np.load(p, allow_pickle=False) as z:
        required = {"local_obs", "global_obs", "actions", "rewards", "eligible_mask"}
        missing = required - set(z.files)
        if missing:
            raise ValueError(f"MAPPO dataset missing arrays: {sorted(missing)}")
        data = {k: np.asarray(z[k]) for k in required}
    if len(data["local_obs"]) < int(minimum_samples):
        raise ValueError("insufficient MAPPO samples")
    return data


def train_mappo_file_v240(dataset_path: str | Path, checkpoint_path: str | Path, config: dict) -> dict:
    data = load_mappo_npz_v240(dataset_path, minimum_samples=int(config.get("minimum_samples", 512)))
    trainer = MAPPOTrainerV240(data["local_obs"].shape[-1], data["global_obs"].shape[-1], seed=int(config.get("seed", 47)))
    warm = trainer.load(checkpoint_path)
    result = trainer.train(
        data,
        updates=int(config.get("updates_per_cycle", 8)),
        learning_rate=float(config.get("learning_rate", 3e-4)),
        gamma=float(config.get("gamma", 0.995)),
        clip_ratio=float(config.get("clip_ratio", 0.2)),
        value_coef=float(config.get("value_coefficient", 0.5)),
        entropy_coef=float(config.get("entropy_coefficient", 0.01)),
        max_grad_norm=float(config.get("max_grad_norm", 0.5)),
    )
    metadata = {**result, "warm_started": warm, "dataset": str(dataset_path), "execution_authority": "NONE"}
    trainer.save(checkpoint_path, metadata)
    return {**metadata, "checkpoint_path": str(checkpoint_path)}


__all__ = ["MAPPOTrainerV240", "load_mappo_npz_v240", "train_mappo_file_v240"]
