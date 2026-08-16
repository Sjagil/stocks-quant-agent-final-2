from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from stocks.rl.config import EnvironmentConfig, RewardConfig
from stocks.rl.features import build_rl_features
from stocks.rl.rewards import calculate_reward

try:
    import gymnasium as gym
    from gymnasium import spaces
except Exception:  # pragma: no cover
    gym = None
    spaces = None


def prepare_features(
    frame: pd.DataFrame,
    *,
    rolling_window: int = 64,
) -> tuple[pd.DataFrame, pd.Series]:
    features = build_rl_features(
        frame,
        rolling_window=rolling_window,
    )
    joined = features.copy()
    joined["__close__"] = frame["close"].astype(float)
    joined = (
        joined
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    if joined.empty:
        raise ValueError("no fully observed feature rows")
    return (
        joined.drop(columns=["__close__"]).astype(np.float32),
        joined["__close__"].astype(float),
    )


def latest_market_observation(
    frame: pd.DataFrame,
    *,
    window_size: int,
    position: float,
    drawdown: float,
) -> np.ndarray:
    features, _ = prepare_features(
        frame,
        rolling_window=max(64, window_size),
    )
    if len(features) < window_size:
        raise ValueError("not enough rows for latest agent observation")

    window = (
        features.iloc[-window_size:]
        .to_numpy(dtype=np.float32)
        .reshape(-1)
    )
    state = np.array(
        [
            float(np.clip(position, 0.0, 1.0)),
            float(1.0 - np.clip(position, 0.0, 1.0)),
            float(max(0.0, drawdown)),
        ],
        dtype=np.float32,
    )
    return np.concatenate([window, state]).astype(np.float32)


if gym is not None:
    class _EpisodeMixin:
        def _configure_episode(
            self,
            *,
            random_start: bool,
            episode_length: int | None,
        ) -> None:
            self.random_start = bool(random_start)
            self.episode_length = (
                int(episode_length)
                if episode_length is not None
                else None
            )
            if self.episode_length is not None and self.episode_length < 8:
                raise ValueError("episode_length must be >= 8")

        def _choose_episode_bounds(self) -> tuple[int, int]:
            base_start = self.env_cfg.window_size - 1
            absolute_last = len(self.features) - 2

            if self.episode_length is None:
                return base_start, absolute_last

            max_start = max(
                base_start,
                absolute_last - self.episode_length + 1,
            )

            if self.random_start and max_start > base_start:
                start = int(
                    self.np_random.integers(
                        base_start,
                        max_start + 1,
                    )
                )
            else:
                start = base_start

            last = min(
                absolute_last,
                start + self.episode_length - 1,
            )
            return start, last


    class DiscreteLongOnlyTimingEnv(_EpisodeMixin, gym.Env):
        """DQN timing environment: HOLD / ENTER_LONG / EXIT_TO_CASH."""

        metadata = {"render_modes": []}
        HOLD = 0
        ENTER_LONG = 1
        EXIT_TO_CASH = 2

        def __init__(
            self,
            frame: pd.DataFrame,
            *,
            env_cfg: EnvironmentConfig | None = None,
            reward_cfg: RewardConfig | None = None,
            random_start: bool = False,
            episode_length: int | None = None,
        ) -> None:
            super().__init__()
            self.env_cfg = env_cfg or EnvironmentConfig()
            self.reward_cfg = reward_cfg or RewardConfig()
            self.features, self.close = prepare_features(
                frame,
                rolling_window=max(64, self.env_cfg.window_size),
            )
            if len(self.features) <= self.env_cfg.window_size + 2:
                raise ValueError("not enough rows for timing environment")

            self._configure_episode(
                random_start=random_start,
                episode_length=episode_length,
            )

            obs_size = (
                self.env_cfg.window_size * self.features.shape[1] + 3
            )
            self.observation_space = spaces.Box(
                -np.inf,
                np.inf,
                shape=(obs_size,),
                dtype=np.float32,
            )
            self.action_space = spaces.Discrete(3)
            self.reset()

        def _obs(self) -> np.ndarray:
            start = self._step - self.env_cfg.window_size + 1
            window = (
                self.features.iloc[start : self._step + 1]
                .to_numpy(dtype=np.float32)
                .reshape(-1)
            )
            drawdown = 1.0 - self._equity / max(self._peak, 1e-12)
            state = np.array(
                [self._position, 1.0 - self._position, drawdown],
                dtype=np.float32,
            )
            return np.concatenate([window, state]).astype(np.float32)

        def _info(self) -> dict[str, float | int]:
            return {
                "equity": float(self._equity),
                "position": float(self._position),
                "trades": int(self._trades),
                "episode_start": int(self._episode_start),
                "episode_last": int(self._episode_last),
            }

        def reset(
            self,
            *,
            seed: int | None = None,
            options: dict[str, Any] | None = None,
        ):
            del options
            super().reset(seed=seed)
            self._episode_start, self._episode_last = (
                self._choose_episode_bounds()
            )
            self._step = self._episode_start
            self._position = 0.0
            self._equity = float(self.env_cfg.initial_equity)
            self._peak = self._equity
            self._trades = 0
            return self._obs(), self._info()

        def step(self, action):
            action = int(np.asarray(action).reshape(-1)[0])
            old = self._position

            if action == self.ENTER_LONG:
                target = 1.0
            elif action == self.EXIT_TO_CASH:
                target = 0.0
            elif action == self.HOLD:
                target = old
            else:
                raise ValueError(f"invalid timing action: {action}")

            if target != old:
                self._trades += 1

            p0 = float(self.close.iloc[self._step])
            p1 = float(self.close.iloc[self._step + 1])
            asset_return = p1 / p0 - 1.0
            gross_return = target * asset_return
            turnover = abs(target - old)
            cost = (
                self.reward_cfg.transaction_cost_bps
                + self.reward_cfg.slippage_bps
            ) / 10_000.0

            previous = self._equity
            next_equity = previous * max(
                1e-9,
                1.0 + gross_return - turnover * cost,
            )

            breakdown = calculate_reward(
                gross_return=gross_return,
                old_position=old,
                new_position=target,
                previous_equity=previous,
                new_equity_before_penalties=next_equity,
                peak_equity=self._peak,
                cfg=self.reward_cfg,
            )

            self._position = target
            self._equity = next_equity
            self._peak = max(self._peak, self._equity)
            self._step += 1

            terminated = (
                self._equity
                <= self.env_cfg.initial_equity * 0.25
            )
            truncated = self._step >= self._episode_last

            return (
                self._obs(),
                float(breakdown.reward),
                bool(terminated),
                bool(truncated),
                self._info(),
            )


    class ContinuousLongOnlySizingEnv(_EpisodeMixin, gym.Env):
        """SAC exposure environment with target exposure constrained to [0, 1]."""

        metadata = {"render_modes": []}

        def __init__(
            self,
            frame: pd.DataFrame,
            *,
            env_cfg: EnvironmentConfig | None = None,
            reward_cfg: RewardConfig | None = None,
            random_start: bool = False,
            episode_length: int | None = None,
        ) -> None:
            super().__init__()
            self.env_cfg = env_cfg or EnvironmentConfig()
            self.reward_cfg = reward_cfg or RewardConfig()
            self.features, self.close = prepare_features(
                frame,
                rolling_window=max(64, self.env_cfg.window_size),
            )
            if len(self.features) <= self.env_cfg.window_size + 2:
                raise ValueError("not enough rows for sizing environment")

            self._configure_episode(
                random_start=random_start,
                episode_length=episode_length,
            )

            obs_size = (
                self.env_cfg.window_size * self.features.shape[1] + 3
            )
            self.observation_space = spaces.Box(
                -np.inf,
                np.inf,
                shape=(obs_size,),
                dtype=np.float32,
            )
            self.action_space = spaces.Box(
                low=np.array([0.0], dtype=np.float32),
                high=np.array([self.env_cfg.max_position], dtype=np.float32),
                dtype=np.float32,
            )
            self.reset()

        def _obs(self) -> np.ndarray:
            start = self._step - self.env_cfg.window_size + 1
            window = (
                self.features.iloc[start : self._step + 1]
                .to_numpy(dtype=np.float32)
                .reshape(-1)
            )
            drawdown = 1.0 - self._equity / max(self._peak, 1e-12)
            state = np.array(
                [self._position, 1.0 - self._position, drawdown],
                dtype=np.float32,
            )
            return np.concatenate([window, state]).astype(np.float32)

        def _info(self) -> dict[str, float | int]:
            return {
                "equity": float(self._equity),
                "position": float(self._position),
                "trades": int(self._trades),
                "episode_start": int(self._episode_start),
                "episode_last": int(self._episode_last),
            }

        def reset(
            self,
            *,
            seed: int | None = None,
            options: dict[str, Any] | None = None,
        ):
            del options
            super().reset(seed=seed)
            self._episode_start, self._episode_last = (
                self._choose_episode_bounds()
            )
            self._step = self._episode_start
            self._position = 0.0
            self._equity = float(self.env_cfg.initial_equity)
            self._peak = self._equity
            self._trades = 0
            return self._obs(), self._info()

        def step(self, action):
            target = float(
                np.clip(
                    np.asarray(action).reshape(-1)[0],
                    0.0,
                    self.env_cfg.max_position,
                )
            )
            old = float(self._position)

            if abs(target - old) < self.env_cfg.min_trade_delta:
                target = old
            else:
                self._trades += 1

            p0 = float(self.close.iloc[self._step])
            p1 = float(self.close.iloc[self._step + 1])
            asset_return = p1 / p0 - 1.0
            gross_return = target * asset_return
            turnover = abs(target - old)
            cost = (
                self.reward_cfg.transaction_cost_bps
                + self.reward_cfg.slippage_bps
            ) / 10_000.0

            previous = self._equity
            next_equity = previous * max(
                1e-9,
                1.0 + gross_return - turnover * cost,
            )

            breakdown = calculate_reward(
                gross_return=gross_return,
                old_position=old,
                new_position=target,
                previous_equity=previous,
                new_equity_before_penalties=next_equity,
                peak_equity=self._peak,
                cfg=self.reward_cfg,
            )

            self._position = target
            self._equity = next_equity
            self._peak = max(self._peak, self._equity)
            self._step += 1

            terminated = (
                self._equity
                <= self.env_cfg.initial_equity * 0.25
            )
            truncated = self._step >= self._episode_last

            return (
                self._obs(),
                float(breakdown.reward),
                bool(terminated),
                bool(truncated),
                self._info(),
            )


    class RiskReductionEnv(_EpisodeMixin, gym.Env):
        """Risk agent which can keep or reduce an already-open long only."""

        metadata = {"render_modes": []}
        KEEP = 0
        CUT_25 = 1
        CUT_50 = 2
        FLAT = 3

        def __init__(
            self,
            frame: pd.DataFrame,
            *,
            env_cfg: EnvironmentConfig | None = None,
            reward_cfg: RewardConfig | None = None,
            random_start: bool = False,
            episode_length: int | None = None,
        ) -> None:
            super().__init__()
            self.env_cfg = env_cfg or EnvironmentConfig()
            self.reward_cfg = reward_cfg or RewardConfig()
            self.features, self.close = prepare_features(
                frame,
                rolling_window=max(64, self.env_cfg.window_size),
            )
            if len(self.features) <= self.env_cfg.window_size + 2:
                raise ValueError("not enough rows for risk environment")

            self._configure_episode(
                random_start=random_start,
                episode_length=episode_length,
            )

            obs_size = (
                self.env_cfg.window_size * self.features.shape[1] + 3
            )
            self.observation_space = spaces.Box(
                -np.inf,
                np.inf,
                shape=(obs_size,),
                dtype=np.float32,
            )
            self.action_space = spaces.Discrete(4)
            self.reset()

        def action_masks(self) -> np.ndarray:
            if self._position <= 1e-9:
                return np.array(
                    [True, False, False, False],
                    dtype=bool,
                )
            return np.array(
                [True, True, True, True],
                dtype=bool,
            )

        def _obs(self) -> np.ndarray:
            start = self._step - self.env_cfg.window_size + 1
            window = (
                self.features.iloc[start : self._step + 1]
                .to_numpy(dtype=np.float32)
                .reshape(-1)
            )
            drawdown = 1.0 - self._equity / max(self._peak, 1e-12)
            state = np.array(
                [self._position, 1.0 - self._position, drawdown],
                dtype=np.float32,
            )
            return np.concatenate([window, state]).astype(np.float32)

        def _info(self) -> dict[str, float | int]:
            return {
                "position": float(self._position),
                "equity": float(self._equity),
                "trades": int(self._trades),
                "episode_start": int(self._episode_start),
                "episode_last": int(self._episode_last),
            }

        def reset(
            self,
            *,
            seed: int | None = None,
            options: dict[str, Any] | None = None,
        ):
            del options
            super().reset(seed=seed)
            self._episode_start, self._episode_last = (
                self._choose_episode_bounds()
            )
            self._step = self._episode_start
            self._position = 1.0
            self._equity = float(self.env_cfg.initial_equity)
            self._peak = self._equity
            self._trades = 0
            return self._obs(), self._info()

        def step(self, action):
            action = int(np.asarray(action).reshape(-1)[0])
            if not self.action_masks()[action]:
                raise ValueError("masked risk action attempted")

            old = float(self._position)
            factors = {
                self.KEEP: 1.0,
                self.CUT_25: 0.75,
                self.CUT_50: 0.50,
                self.FLAT: 0.0,
            }
            target = min(old, old * factors[action])

            if target != old:
                self._trades += 1

            p0 = float(self.close.iloc[self._step])
            p1 = float(self.close.iloc[self._step + 1])
            asset_return = p1 / p0 - 1.0
            gross_return = target * asset_return
            turnover = abs(target - old)
            cost = (
                self.reward_cfg.transaction_cost_bps
                + self.reward_cfg.slippage_bps
            ) / 10_000.0

            previous = self._equity
            next_equity = previous * max(
                1e-9,
                1.0 + gross_return - turnover * cost,
            )

            breakdown = calculate_reward(
                gross_return=gross_return,
                old_position=old,
                new_position=target,
                previous_equity=previous,
                new_equity_before_penalties=next_equity,
                peak_equity=self._peak,
                cfg=self.reward_cfg,
            )

            self._position = target
            self._equity = next_equity
            self._peak = max(self._peak, self._equity)
            self._step += 1

            ruined = (
                self._equity
                <= self.env_cfg.initial_equity * 0.25
            )
            # Once flat, the risk-management episode is complete. This avoids
            # thousands of useless all-cash transitions during training.
            flattened = self._position <= 1e-9
            terminated = bool(ruined or flattened)
            truncated = self._step >= self._episode_last

            return (
                self._obs(),
                float(breakdown.reward),
                terminated,
                bool(truncated),
                self._info(),
            )
else:
    class DiscreteLongOnlyTimingEnv:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ImportError("gymnasium is required")

    class ContinuousLongOnlySizingEnv:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ImportError("gymnasium is required")

    class RiskReductionEnv:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ImportError("gymnasium is required")
