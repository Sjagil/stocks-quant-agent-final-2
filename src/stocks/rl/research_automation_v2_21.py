from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any

from .contracts_v2_21 import DEPLOYMENT_MODE, EXECUTION_AUTHORITY
from .mappo_v2_21 import (
    MAPPORolloutBufferV221,
    MAPPORolloutTransitionV221,
    MAPPOTrainerV221,
)
from .matd3_v2_21 import (
    MATD3BenchmarkV221,
    MATD3ReplayBufferV221,
    MATD3TransitionV221,
)
from .portfolio_environment_v2_21 import CausalMultiAssetPortfolioEnvV221
from .validation_v2_21 import ImmutableSeedLedgerV221

SUPPORTED_ALGORITHMS = ("MAPPO", "MATD3")


@dataclass(frozen=True)
class RLTrialSpecV221:
    algorithm: str
    seed: int
    fold: int
    deployment_mode: str = DEPLOYMENT_MODE
    execution_authority: str = EXECUTION_AUTHORITY

    def __post_init__(self) -> None:
        if self.algorithm not in SUPPORTED_ALGORITHMS:
            raise ValueError(f"unsupported v2.21 algorithm: {self.algorithm}")
        if self.seed < 0 or self.fold < 0:
            raise ValueError("seed and fold must be non-negative")
        if self.deployment_mode != DEPLOYMENT_MODE:
            raise ValueError("v2.21 trials are shadow-only")
        if self.execution_authority != EXECUTION_AUTHORITY:
            raise ValueError("v2.21 trials cannot receive execution authority")


def build_trial_matrix_v221(
    folds: Iterable[int],
    *,
    seeds: Iterable[int] = range(10),
    algorithms: Iterable[str] = SUPPORTED_ALGORITHMS,
) -> tuple[RLTrialSpecV221, ...]:
    fold_values = tuple(int(value) for value in folds)
    seed_values = tuple(int(value) for value in seeds)
    algorithm_values = tuple(str(value).upper() for value in algorithms)
    if not fold_values or len(set(fold_values)) != len(fold_values):
        raise ValueError("folds must be non-empty and unique")
    if len(seed_values) != 10 or len(set(seed_values)) != 10:
        raise ValueError("the final trial matrix requires exactly ten unique seeds")
    if not algorithm_values or len(set(algorithm_values)) != len(algorithm_values):
        raise ValueError("algorithms must be non-empty and unique")
    return tuple(
        RLTrialSpecV221(algorithm=algorithm, seed=seed, fold=fold)
        for algorithm in algorithm_values
        for fold in fold_values
        for seed in seed_values
    )


def collect_and_update_mappo_v221(
    env: CausalMultiAssetPortfolioEnvV221,
    trainer: MAPPOTrainerV221,
    *,
    seed: int,
    maximum_steps: int | None = None,
) -> dict[str, float | int | bool]:
    """Collect one fresh on-policy rollout and immediately run PPO updates."""

    observation = env.reset(seed=seed)
    rollout = MAPPORolloutBufferV221()
    step_limit = env.episode.steps if maximum_steps is None else int(maximum_steps)
    if step_limit < 1:
        raise ValueError("maximum_steps must be positive")
    final_result = None
    for index in range(min(step_limit, env.episode.steps)):
        local = observation.decentralized_actor_state()
        global_state = observation.centralized_critic_state(
            initial_equity=env.config.initial_equity
        )
        action = trainer.act(
            local,
            global_state,
            observation.tradable_mask,
        )
        result = env.step(action.actions)
        cutoff = index + 1 >= step_limit and not (result.terminated or result.truncated)
        rollout.add(
            MAPPORolloutTransitionV221(
                local_observations=local,
                global_observation=global_state,
                eligible_mask=observation.tradable_mask,
                actions=action.actions,
                log_probabilities=action.log_probabilities,
                rewards=result.agent_rewards,
                value=action.value,
                terminated=result.terminated,
                truncated=result.truncated or cutoff,
            )
        )
        observation = result.observation
        final_result = result
        if result.terminated or result.truncated or cutoff:
            break
    if final_result is None:
        raise RuntimeError("MAPPO collector produced no transition")

    if final_result.terminated:
        last_value = 0.0
    else:
        bootstrap = trainer.act(
            observation.decentralized_actor_state(),
            observation.centralized_critic_state(
                initial_equity=env.config.initial_equity
            ),
            observation.tradable_mask,
            deterministic=True,
        )
        last_value = bootstrap.value
    batch = rollout.training_batch(
        last_value=last_value,
        gamma=trainer.config.gamma,
        gae_lambda=trainer.config.gae_lambda,
    )
    metrics = trainer.update(batch)
    metrics.update(
        {
            "rollout_steps": len(rollout),
            "final_equity": final_result.observation.equity,
            "execution_authority": EXECUTION_AUTHORITY,
            "broker_calls": 0,
            "order_calls": 0,
        }
    )
    return metrics


def collect_matd3_experience_v221(
    env: CausalMultiAssetPortfolioEnvV221,
    benchmark: MATD3BenchmarkV221,
    replay: MATD3ReplayBufferV221,
    *,
    seed: int,
    exploration_noise: float = 0.10,
    maximum_steps: int | None = None,
) -> dict[str, float | int | str]:
    """Collect benchmark experience without invoking any MAPPO component."""

    observation = env.reset(seed=seed)
    step_limit = env.episode.steps if maximum_steps is None else int(maximum_steps)
    if step_limit < 1 or exploration_noise < 0:
        raise ValueError("invalid MATD3 collection settings")
    collected = 0
    final_equity = observation.equity
    for _ in range(min(step_limit, env.episode.steps)):
        local = observation.decentralized_actor_state()
        global_state = observation.centralized_critic_state(
            initial_equity=env.config.initial_equity
        )
        actions = benchmark.select_actions(
            local,
            observation.tradable_mask,
            exploration_noise=exploration_noise,
        )
        result = env.step(actions)
        next_observation = result.observation
        replay.add(
            MATD3TransitionV221(
                local_observations=local,
                global_observation=global_state,
                eligible_mask=observation.tradable_mask,
                actions=actions,
                reward=result.team_reward,
                next_local_observations=(next_observation.decentralized_actor_state()),
                next_global_observation=(
                    next_observation.centralized_critic_state(
                        initial_equity=env.config.initial_equity
                    )
                ),
                next_eligible_mask=next_observation.tradable_mask,
                terminated=result.terminated,
            )
        )
        collected += 1
        final_equity = next_observation.equity
        observation = next_observation
        if result.terminated or result.truncated:
            break
    return {
        "collected_transitions": collected,
        "replay_size": len(replay),
        "final_equity": final_equity,
        "execution_authority": EXECUTION_AUTHORITY,
        "broker_calls": 0,
        "order_calls": 0,
    }


def run_trial_matrix_v221(
    trials: Iterable[RLTrialSpecV221],
    evaluator: Callable[[RLTrialSpecV221], Mapping[str, Any]],
    *,
    config_hash: str,
) -> tuple[tuple[dict[str, Any], ...], ImmutableSeedLedgerV221]:
    """Run an injected evaluator and record every result in a hash chain."""

    normalized_config_hash = config_hash.lower()
    if len(normalized_config_hash) != 64 or any(
        character not in "0123456789abcdef" for character in normalized_config_hash
    ):
        raise ValueError("config_hash must be SHA-256")
    ledger = ImmutableSeedLedgerV221()
    results: list[dict[str, Any]] = []
    for trial in trials:
        raw = dict(evaluator(trial))
        if raw.get("execution_authority", EXECUTION_AUTHORITY) != EXECUTION_AUTHORITY:
            raise ValueError("trial evaluator attempted to grant execution authority")
        if int(raw.get("broker_calls", 0)) != 0 or int(raw.get("order_calls", 0)) != 0:
            raise ValueError("trial evaluator reported external order activity")
        result = {
            **asdict(trial),
            **raw,
            "automatic_live_promotion": False,
            "execution_authority": EXECUTION_AUTHORITY,
            "broker_calls": 0,
            "order_calls": 0,
        }
        canonical = json.dumps(
            result,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        artifact_hash = hashlib.sha256(canonical.encode()).hexdigest()
        ledger.append(
            {
                "algorithm": trial.algorithm,
                "seed": trial.seed,
                "fold": trial.fold,
                "config_hash": normalized_config_hash,
                "artifact_hash": artifact_hash,
            }
        )
        results.append({**result, "artifact_hash": artifact_hash})
    if not ledger.validate():
        raise RuntimeError("trial ledger failed its own integrity check")
    return tuple(results), ledger
