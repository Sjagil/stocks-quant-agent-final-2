from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .environments import prepare_features

try:
    from pettingzoo import ParallelEnv
    from gymnasium import spaces
except Exception:  # pragma: no cover
    ParallelEnv = object
    spaces = None


@dataclass(frozen=True)
class CoordinatedAction:
    timing_action: str
    sizing_target: float
    risk_action: str
    resulting_exposure: float


def coordinate_roles(
    *,
    current_exposure: float,
    timing_action: str,
    sizing_target: float,
    risk_action: str,
) -> CoordinatedAction:
    current = float(np.clip(current_exposure, 0.0, 1.0))
    sizing = float(np.clip(sizing_target, 0.0, 1.0))

    if timing_action == "EXIT_TO_CASH":
        target = 0.0
    elif timing_action == "ENTER_LONG":
        target = sizing
    elif timing_action == "HOLD":
        target = current
    else:
        raise ValueError(f"unsupported timing action: {timing_action}")

    risk_factors = {
        "KEEP": 1.0,
        "CUT_25": 0.75,
        "CUT_50": 0.50,
        "FLAT": 0.0,
    }
    if risk_action not in risk_factors:
        raise ValueError(f"unsupported risk action: {risk_action}")

    if current <= 1e-12 and timing_action != "ENTER_LONG":
        target = 0.0

    # Risk can only reduce what timing+sizing proposed.
    target = min(target, target * risk_factors[risk_action])
    target = float(np.clip(target, 0.0, 1.0))

    return CoordinatedAction(
        timing_action=timing_action,
        sizing_target=sizing,
        risk_action=risk_action,
        resulting_exposure=target,
    )


if spaces is not None:
    class SpecialistParallelTradingEnv(ParallelEnv):
        """Cooperative PettingZoo environment for specialist learners.

        This is intentionally an independent-learner MARL research environment,
        not a claim of centralized-critic/MADDPG training.
        """

        metadata = {"name": "specialist_parallel_trading_v2_12"}
        possible_agents = ["timing", "sizing", "risk"]

        def __init__(self, frame: pd.DataFrame, *, window_size: int = 64):
            self.window_size = int(window_size)
            self.features, self.close = prepare_features(
                frame,
                rolling_window=max(64, self.window_size),
            )
            if len(self.features) <= self.window_size + 2:
                raise ValueError("not enough rows for MARL environment")

            self.agents = self.possible_agents[:]
            obs_size = self.window_size * self.features.shape[1] + 3
            shared_obs = spaces.Box(
                -np.inf,
                np.inf,
                shape=(obs_size,),
                dtype=np.float32,
            )
            self.observation_spaces = {
                agent: shared_obs
                for agent in self.possible_agents
            }
            self.action_spaces = {
                "timing": spaces.Discrete(3),
                "sizing": spaces.Box(
                    low=np.array([0.0], dtype=np.float32),
                    high=np.array([1.0], dtype=np.float32),
                    dtype=np.float32,
                ),
                "risk": spaces.Discrete(4),
            }
            self._start = self.window_size - 1
            self._last = len(self.features) - 2
            self.reset()

        def observation_space(self, agent):
            return self.observation_spaces[agent]

        def action_space(self, agent):
            return self.action_spaces[agent]

        def _obs(self):
            start = self._step - self.window_size + 1
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
            shared = np.concatenate([window, state]).astype(np.float32)
            return {
                agent: shared.copy()
                for agent in self.agents
            }

        def reset(self, seed=None, options=None):
            del options
            if seed is not None:
                np.random.seed(int(seed))
            self.agents = self.possible_agents[:]
            self._step = self._start
            self._position = 0.0
            self._equity = 1.0
            self._peak = 1.0
            observations = self._obs()
            infos = {
                agent: {"execution_authority": "NONE"}
                for agent in self.agents
            }
            return observations, infos

        def step(self, actions):
            timing_map = {
                0: "HOLD",
                1: "ENTER_LONG",
                2: "EXIT_TO_CASH",
            }
            risk_map = {
                0: "KEEP",
                1: "CUT_25",
                2: "CUT_50",
                3: "FLAT",
            }
            sizing_raw = float(
                np.asarray(actions["sizing"]).reshape(-1)[0]
            )
            coordinated = coordinate_roles(
                current_exposure=self._position,
                timing_action=timing_map[int(actions["timing"])],
                sizing_target=sizing_raw,
                risk_action=risk_map[int(actions["risk"])],
            )

            old = self._position
            target = coordinated.resulting_exposure
            p0 = float(self.close.iloc[self._step])
            p1 = float(self.close.iloc[self._step + 1])
            asset_return = p1 / p0 - 1.0
            turnover = abs(target - old)
            reward = target * asset_return - turnover * 0.0008

            self._position = target
            self._equity *= max(1e-9, 1.0 + reward)
            self._peak = max(self._peak, self._equity)
            self._step += 1

            done = self._step >= self._last
            observations = self._obs()
            rewards = {
                agent: float(reward)
                for agent in self.agents
            }
            terminations = {
                agent: False
                for agent in self.agents
            }
            truncations = {
                agent: bool(done)
                for agent in self.agents
            }
            infos = {
                agent: {
                    "position": float(self._position),
                    "shared_reward": True,
                    "execution_authority": "NONE",
                }
                for agent in self.agents
            }
            if done:
                self.agents = []

            return (
                observations,
                rewards,
                terminations,
                truncations,
                infos,
            )
else:
    class SpecialistParallelTradingEnv:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ImportError("pettingzoo and gymnasium are required")
