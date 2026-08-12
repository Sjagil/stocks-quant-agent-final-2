from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .config import EnvironmentConfig, RewardConfig
from .rewards import calculate_reward

try:  # Optional research dependency.
    import gymnasium as gym
    from gymnasium import spaces
except Exception:  # pragma: no cover
    gym = None
    spaces = None


if gym is not None:
    class LongOnlySwingEnv(gym.Env):
        """Causal single-asset swing environment with continuous long-only sizing.

        Observation at t contains the last `window_size` feature rows plus current
        portfolio state. Action is target exposure in [0, 1] for the t -> t+1 bar.
        """

        metadata = {"render_modes": []}

        def __init__(
            self,
            features: pd.DataFrame,
            close: pd.Series,
            *,
            env_cfg: EnvironmentConfig | None = None,
            reward_cfg: RewardConfig | None = None,
        ) -> None:
            super().__init__()
            self.env_cfg = env_cfg or EnvironmentConfig()
            self.reward_cfg = reward_cfg or RewardConfig()

            joined = features.copy()
            joined["__close__"] = close.astype(float)
            joined = joined.replace([np.inf, -np.inf], np.nan).dropna()
            if len(joined) <= self.env_cfg.window_size + 2:
                raise ValueError("not enough fully-observed rows for the configured window")

            self.feature_names = [c for c in joined.columns if c != "__close__"]
            self.features = joined[self.feature_names].astype(np.float32)
            self.close = joined["__close__"].astype(float)

            obs_size = self.env_cfg.window_size * len(self.feature_names) + 3
            self.observation_space = spaces.Box(-np.inf, np.inf, shape=(obs_size,), dtype=np.float32)
            self.action_space = spaces.Box(
                low=np.array([0.0], dtype=np.float32),
                high=np.array([self.env_cfg.max_position], dtype=np.float32),
                dtype=np.float32,
            )
            self._start = self.env_cfg.window_size - 1
            self._last = len(self.features) - 2
            self.reset()

        def _observation(self) -> np.ndarray:
            start = self._step - self.env_cfg.window_size + 1
            window = self.features.iloc[start : self._step + 1].to_numpy(dtype=np.float32).reshape(-1)
            drawdown = 1.0 - self._equity / max(self._peak_equity, 1e-12)
            state = np.array([self._position, 1.0 - self._position, drawdown], dtype=np.float32)
            return np.concatenate([window, state]).astype(np.float32)

        def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
            super().reset(seed=seed)
            self._step = self._start
            self._position = 0.0
            self._equity = float(self.env_cfg.initial_equity)
            self._peak_equity = self._equity
            self._trades = 0
            return self._observation(), self._info()

        def _info(self) -> dict[str, float | int]:
            return {
                "equity": float(self._equity),
                "position": float(self._position),
                "peak_equity": float(self._peak_equity),
                "trades": int(self._trades),
            }

        def step(self, action):
            target = float(np.clip(np.asarray(action).reshape(-1)[0], 0.0, self.env_cfg.max_position))
            old_position = self._position
            if abs(target - old_position) < self.env_cfg.min_trade_delta:
                target = old_position
            else:
                self._trades += 1

            p0 = float(self.close.iloc[self._step])
            p1 = float(self.close.iloc[self._step + 1])
            asset_return = p1 / p0 - 1.0
            gross_return = target * asset_return

            previous_equity = self._equity
            turnover = abs(target - old_position)
            one_way_cost = (self.reward_cfg.transaction_cost_bps + self.reward_cfg.slippage_bps) / 10_000.0
            net_simple_return = gross_return - turnover * one_way_cost
            equity_after = previous_equity * max(1e-9, 1.0 + net_simple_return)

            breakdown = calculate_reward(
                gross_return=gross_return,
                old_position=old_position,
                new_position=target,
                previous_equity=previous_equity,
                new_equity_before_penalties=equity_after,
                peak_equity=self._peak_equity,
                cfg=self.reward_cfg,
            )

            self._position = target
            self._equity = equity_after
            self._peak_equity = max(self._peak_equity, self._equity)
            self._step += 1

            terminated = self._equity <= self.env_cfg.initial_equity * 0.25
            truncated = self._step >= self._last
            info = self._info() | {
                "asset_return": float(asset_return),
                "gross_return": float(gross_return),
                "reward_cost": breakdown.cost,
                "reward_downside_penalty": breakdown.downside_penalty,
                "reward_drawdown_penalty": breakdown.drawdown_penalty,
                "reward_turnover_penalty": breakdown.turnover_penalty,
            }
            return self._observation(), breakdown.reward, terminated, truncated, info
else:
    class LongOnlySwingEnv:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ImportError("gymnasium is required for LongOnlySwingEnv; install the 'rl' extra")
