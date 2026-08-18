from __future__ import annotations

import hashlib
import json
import math
import subprocess
import tempfile
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np
import yaml

from .checkpoint_v2_21 import (
    save_research_checkpoint_v221,
    sha256_path_v221,
    verify_research_checkpoint_v221,
)
from .contracts_v2_21 import (
    DEPLOYMENT_MODE,
    EXECUTION_AUTHORITY,
    MAPPOConfigV221,
    MATD3ConfigV221,
    PortfolioEnvironmentConfigV221,
    PromotionPolicyV221,
)
from .dataset_v2_21 import (
    fit_feature_scaler_v221,
    load_portfolio_dataset_v221,
    slice_portfolio_episode_v221,
    transform_portfolio_episode_v221,
)
from .mappo_v2_21 import MAPPOTrainerV221
from .matd3_v2_21 import MATD3BenchmarkV221, MATD3ReplayBufferV221
from .portfolio_environment_v2_21 import CausalMultiAssetPortfolioEnvV221
from .research_automation_v2_21 import (
    RLTrialSpecV221,
    collect_and_update_mappo_v221,
    collect_matd3_experience_v221,
    run_trial_matrix_v221,
)
from .validation_v2_21 import (
    ImmutableSeedLedgerV221,
    RLPromotionEvidenceV221,
    SeedLedgerEntryV221,
    SeedEvaluationV221,
    build_walk_forward_plan_v221,
    evaluate_rl_promotion_v221,
)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    )


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode()).hexdigest()


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    temporary.replace(path)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_text(path, json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _tuple_int(
    value: Any,
    *,
    field: str,
    require_unique: bool = True,
    minimum: int = 0,
) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be a sequence")
    result = tuple(int(item) for item in value)
    if not result or min(result) < minimum:
        raise ValueError(f"{field} contains an invalid integer")
    if require_unique and len(set(result)) != len(result):
        raise ValueError(f"{field} must contain unique integers")
    return result


@dataclass(frozen=True)
class RLMARLPipelineConfigV221:
    data_root: Path
    output_root: Path
    symbols: tuple[str, ...]
    timeframe: str
    benchmark_symbol: str | None
    algorithms: tuple[str, ...]
    seeds: tuple[int, ...]
    train_size: int
    validation_size: int
    test_size: int
    purge: int
    embargo: int
    training_updates: int
    maximum_training_steps: int
    matd3_replay_capacity: int
    matd3_batch_size: int
    matd3_gradient_steps: int
    actor_hidden_dims: tuple[int, ...]
    critic_hidden_dims: tuple[int, ...]
    device: str
    required_regimes: tuple[str, ...]
    minimum_regime_observations: int
    environment: PortfolioEnvironmentConfigV221
    promotion: PromotionPolicyV221
    verify_source_hashes: bool = True

    def __post_init__(self) -> None:
        if not self.symbols or len(set(self.symbols)) != len(self.symbols):
            raise ValueError("symbols must be non-empty and unique")
        if any(value not in {"MAPPO", "MATD3"} for value in self.algorithms):
            raise ValueError("algorithms may only contain MAPPO and MATD3")
        if not self.algorithms or len(set(self.algorithms)) != len(self.algorithms):
            raise ValueError("algorithms must be non-empty and unique")
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("seeds must be non-empty and unique")
        sizes = (
            self.train_size,
            self.validation_size,
            self.test_size,
            self.training_updates,
            self.maximum_training_steps,
            self.matd3_replay_capacity,
            self.matd3_batch_size,
            self.matd3_gradient_steps,
        )
        if min(sizes) < 1 or min(self.purge, self.embargo) < 0:
            raise ValueError("pipeline sizes must be positive and gaps non-negative")
        if self.matd3_batch_size > self.matd3_replay_capacity:
            raise ValueError("MATD3 batch size exceeds replay capacity")
        if not self.actor_hidden_dims or not self.critic_hidden_dims:
            raise ValueError("hidden layer dimensions are required")
        if not self.required_regimes or len(set(self.required_regimes)) != len(
            self.required_regimes
        ):
            raise ValueError("required regimes must be non-empty and unique")
        if self.minimum_regime_observations < 1:
            raise ValueError("minimum_regime_observations must be positive")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["data_root"] = str(self.data_root)
        value["output_root"] = str(self.output_root)
        return value

    @property
    def config_hash(self) -> str:
        value = self.to_dict()
        value.pop("data_root", None)
        value.pop("output_root", None)
        return _canonical_hash(value)


def load_rl_marl_pipeline_config_v221(
    path: str | Path,
    *,
    project_root: str | Path | None = None,
) -> RLMARLPipelineConfigV221:
    config_path = Path(path).resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("RL/MARL pipeline config must be a mapping")
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else config_path.parent.parent.resolve()
    )
    dataset = dict(raw.get("dataset") or {})
    walk = dict(raw.get("walk_forward") or {})
    training = dict(raw.get("training") or {})
    validation = dict(raw.get("validation") or {})
    environment = dict(raw.get("environment") or {})
    promotion = dict(raw.get("promotion") or {})
    if "required_seeds" in promotion:
        promotion["required_seeds"] = _tuple_int(
            promotion["required_seeds"],
            field="promotion.required_seeds",
        )
    data_root = Path(dataset.get("data_root", "data"))
    output_root = Path(raw.get("output_root", "artifacts/rl_marl/v2_21"))
    if not data_root.is_absolute():
        data_root = root / data_root
    if not output_root.is_absolute():
        output_root = root / output_root
    algorithms = tuple(str(value).upper() for value in training.get("algorithms", ("MAPPO", "MATD3")))
    symbols = tuple(str(value).strip().upper() for value in dataset.get("symbols", ()))
    return RLMARLPipelineConfigV221(
        data_root=data_root,
        output_root=output_root,
        symbols=symbols,
        timeframe=str(dataset.get("timeframe", "1h")),
        benchmark_symbol=(
            None
            if dataset.get("benchmark_symbol") in (None, "")
            else str(dataset["benchmark_symbol"]).upper()
        ),
        algorithms=algorithms,
        seeds=_tuple_int(training.get("seeds", tuple(range(10))), field="seeds"),
        train_size=int(walk.get("train_size", 4000)),
        validation_size=int(walk.get("validation_size", 1000)),
        test_size=int(walk.get("test_size", 1000)),
        purge=int(walk.get("purge", 24)),
        embargo=int(walk.get("embargo", 24)),
        training_updates=int(training.get("training_updates", 5)),
        maximum_training_steps=int(training.get("maximum_training_steps", 1024)),
        matd3_replay_capacity=int(training.get("matd3_replay_capacity", 100_000)),
        matd3_batch_size=int(training.get("matd3_batch_size", 256)),
        matd3_gradient_steps=int(training.get("matd3_gradient_steps", 32)),
        actor_hidden_dims=_tuple_int(
            training.get("actor_hidden_dims", (128, 128)),
            field="actor_hidden_dims",
            require_unique=False,
            minimum=1,
        ),
        critic_hidden_dims=_tuple_int(
            training.get("critic_hidden_dims", (256, 256)),
            field="critic_hidden_dims",
            require_unique=False,
            minimum=1,
        ),
        device=str(training.get("device", "cpu")),
        required_regimes=tuple(
            str(value).strip().upper()
            for value in validation.get(
                "required_regimes",
                (
                    "BULL_LOW_VOL",
                    "BULL_HIGH_VOL",
                    "BEAR_LOW_VOL",
                    "BEAR_HIGH_VOL",
                ),
            )
        ),
        minimum_regime_observations=int(
            validation.get("minimum_regime_observations", 20)
        ),
        environment=PortfolioEnvironmentConfigV221(**environment),
        promotion=PromotionPolicyV221(**promotion),
        verify_source_hashes=bool(dataset.get("verify_source_hashes", True)),
    )


def _git_commit(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "UNKNOWN"


def _evaluation(
    episode,
    environment: PortfolioEnvironmentConfigV221,
    action_fn,
) -> dict[str, Any]:
    env = CausalMultiAssetPortfolioEnvV221(episode, config=environment)
    observation = env.reset(seed=0)
    returns: list[float] = []
    baseline: list[float] = []
    max_concentration = 0.0
    violations = 0
    final = None
    while True:
        actions = action_fn(observation)
        result = env.step(actions)
        target = np.asarray(result.info["target_weights"], dtype=float)
        returns.append(float(result.info["net_return"]))
        baseline.append(float(result.info["benchmark_return"]))
        max_concentration = max(max_concentration, float(target.max(initial=0.0)))
        if (
            np.any(target < -1e-12)
            or target.sum() > environment.max_gross_exposure + 1e-9
            or target.max(initial=0.0) > environment.max_asset_weight + 1e-9
        ):
            violations += 1
        observation = result.observation
        final = result
        if result.terminated or result.truncated:
            break
    assert final is not None
    curve = np.cumprod(1.0 + np.asarray(returns, dtype=float))
    peaks = np.maximum.accumulate(np.concatenate([[1.0], curve]))[1:]
    drawdown = 1.0 - curve / peaks
    return {
        "steps": len(returns),
        "strategy_return": float(curve[-1] - 1.0),
        "baseline_return": float(np.prod(1.0 + np.asarray(baseline)) - 1.0),
        "maximum_drawdown": float(drawdown.max(initial=0.0)),
        "maximum_concentration": max_concentration,
        "constraint_violations": violations,
        "final_equity": float(final.observation.equity),
    }


def _stress_environment(
    config: PortfolioEnvironmentConfigV221,
    multiplier: float,
) -> PortfolioEnvironmentConfigV221:
    return replace(
        config,
        transaction_cost_bps=config.transaction_cost_bps * multiplier,
        slippage_bps=config.slippage_bps * multiplier,
    )


def _regime_counts(
    benchmark_returns: np.ndarray,
    *,
    window: int = 20,
) -> dict[str, int]:
    values = np.asarray(benchmark_returns, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("benchmark returns are required for regime coverage")
    means = np.empty_like(values)
    volatility = np.empty_like(values)
    for index in range(len(values)):
        sample = values[max(0, index - window + 1) : index + 1]
        means[index] = sample.mean()
        volatility[index] = sample.std(ddof=0)
    threshold = float(np.median(volatility))
    counts = {
        "BULL_LOW_VOL": 0,
        "BULL_HIGH_VOL": 0,
        "BEAR_LOW_VOL": 0,
        "BEAR_HIGH_VOL": 0,
    }
    for mean, vol in zip(means, volatility, strict=True):
        direction = "BULL" if mean >= 0 else "BEAR"
        level = "HIGH_VOL" if vol >= threshold else "LOW_VOL"
        counts[f"{direction}_{level}"] += 1
    return counts


def _train_trial(
    trial: RLTrialSpecV221,
    *,
    split,
    full_episode,
    pipeline: RLMARLPipelineConfigV221,
    dataset_hash: str,
    code_commit: str,
    run_root: Path,
) -> dict[str, Any]:
    raw_train = slice_portfolio_episode_v221(
        full_episode,
        split.train_start,
        split.train_end,
    )
    raw_test = slice_portfolio_episode_v221(
        full_episode,
        split.test_start,
        split.test_end,
    )
    raw_validation = slice_portfolio_episode_v221(
        full_episode,
        split.validation_start,
        split.validation_end,
    )
    scaler = fit_feature_scaler_v221(raw_train)
    train = transform_portfolio_episode_v221(raw_train, scaler)
    test = transform_portfolio_episode_v221(raw_test, scaler)
    validation = transform_portfolio_episode_v221(raw_validation, scaler)
    actor_dim = train.local_observations.shape[-1] + 4
    critic_dim = train.global_observations.shape[-1] + 4
    training_metrics: list[dict[str, Any]] = []

    if trial.algorithm == "MAPPO":
        model = MAPPOTrainerV221(
            MAPPOConfigV221(
                local_observation_dim=actor_dim,
                global_observation_dim=critic_dim,
                actor_hidden_dims=pipeline.actor_hidden_dims,
                critic_hidden_dims=pipeline.critic_hidden_dims,
            ),
            seed=trial.seed,
            device=pipeline.device,
        )
        for _ in range(pipeline.training_updates):
            env = CausalMultiAssetPortfolioEnvV221(train, config=pipeline.environment)
            training_metrics.append(
                collect_and_update_mappo_v221(
                    env,
                    model,
                    seed=trial.seed,
                    maximum_steps=min(pipeline.maximum_training_steps, train.steps),
                )
            )

        def action_fn(observation):
            return model.act(
                observation.decentralized_actor_state(),
                observation.centralized_critic_state(
                    initial_equity=pipeline.environment.initial_equity
                ),
                observation.tradable_mask,
                deterministic=True,
            ).actions

    else:
        model = MATD3BenchmarkV221(
            MATD3ConfigV221(
                agents=train.assets,
                local_observation_dim=actor_dim,
                global_observation_dim=critic_dim,
                hidden_dims=pipeline.critic_hidden_dims,
            ),
            seed=trial.seed,
            device=pipeline.device,
        )
        replay = MATD3ReplayBufferV221(
            pipeline.matd3_replay_capacity,
            seed=trial.seed,
        )
        for _ in range(pipeline.training_updates):
            env = CausalMultiAssetPortfolioEnvV221(train, config=pipeline.environment)
            training_metrics.append(
                collect_matd3_experience_v221(
                    env,
                    model,
                    replay,
                    seed=trial.seed,
                    maximum_steps=min(pipeline.maximum_training_steps, train.steps),
                )
            )
            for _ in range(pipeline.matd3_gradient_steps):
                if len(replay) < pipeline.matd3_batch_size:
                    break
                training_metrics.append(model.update(replay.sample(pipeline.matd3_batch_size)))

        def action_fn(observation):
            return model.select_actions(
                observation.decentralized_actor_state(),
                observation.tradable_mask,
                exploration_noise=0.0,
            )

    validation_result = _evaluation(validation, pipeline.environment, action_fn)
    standard = _evaluation(test, pipeline.environment, action_fn)
    cost_stress = _evaluation(test, _stress_environment(pipeline.environment, 1.5), action_fn)
    severe_stress = _evaluation(test, _stress_environment(pipeline.environment, 2.0), action_fn)
    checkpoint_dir = run_root / "checkpoints" / trial.algorithm.lower() / f"seed-{trial.seed}" / f"fold-{trial.fold}"
    checkpoint = save_research_checkpoint_v221(
        model,
        checkpoint_dir,
        algorithm=trial.algorithm,
        seed=trial.seed,
        fold=trial.fold,
        dataset_hash=dataset_hash,
        config_hash=pipeline.config_hash,
        code_commit=code_commit,
        extra={"scaler": scaler.to_dict()},
    )
    checkpoint_manifest = verify_research_checkpoint_v221(checkpoint)
    return {
        **standard,
        "fold_net_return": standard["strategy_return"],
        "cost_stress_return": cost_stress["strategy_return"],
        "severe_stress_return": severe_stress["strategy_return"],
        "validation_return": validation_result["strategy_return"],
        "training_updates": len(training_metrics),
        "training_last_metrics": {
            key: value
            for key, value in (training_metrics[-1] if training_metrics else {}).items()
            if not isinstance(value, (float, np.floating)) or np.isfinite(value)
        },
        "checkpoint_manifest": str(checkpoint.relative_to(run_root)),
        "checkpoint_weights_sha256": checkpoint_manifest["weights_sha256"],
        "checkpoint_tensor_sha256": checkpoint_manifest["tensor_sha256"],
        "scaler": scaler.to_dict(),
        "regime_counts": _regime_counts(raw_test.benchmark_returns),
        "reproducible": False,
        "deployment_mode": DEPLOYMENT_MODE,
        "execution_authority": EXECUTION_AUTHORITY,
        "broker_calls": 0,
        "order_calls": 0,
    }


def _deflated_sharpe_probability(returns: Sequence[float], trials: int) -> float:
    values = np.asarray(returns, dtype=float)
    if len(values) < 3 or values.std(ddof=1) <= 1e-12:
        return 0.0
    mean = float(values.mean())
    std = float(values.std(ddof=1))
    sharpe = mean / std
    centered = (values - mean) / std
    skew = float(np.mean(centered**3))
    kurtosis = float(np.mean(centered**4))
    sharpe_error = math.sqrt(
        max(1.0 - skew * sharpe + (kurtosis - 1.0) * sharpe**2 / 4.0, 1e-12)
        / (len(values) - 1)
    )
    count = max(int(trials), 2)
    normal = NormalDist()
    euler_gamma = 0.5772156649015329
    expected_max = sharpe_error * (
        (1.0 - euler_gamma) * normal.inv_cdf(1.0 - 1.0 / count)
        + euler_gamma * normal.inv_cdf(1.0 - 1.0 / (count * math.e))
    )
    return float(normal.cdf((sharpe - expected_max) / sharpe_error))


def _expectancy_lower_bps(returns: Sequence[float]) -> float:
    values = np.asarray(returns, dtype=float)
    if len(values) < 2:
        return float("-inf")
    lower = values.mean() - 1.96 * values.std(ddof=1) / math.sqrt(len(values))
    return float(lower * 10_000.0)


def _promotion_summary(
    results: Sequence[Mapping[str, Any]],
    pipeline: RLMARLPipelineConfigV221,
    *,
    dataset_hash: str,
    code_commit: str,
    smoke: bool,
    algorithms: Sequence[str],
) -> dict[str, Any]:
    decisions: dict[str, Any] = {}
    for algorithm in algorithms:
        rows = [row for row in results if row["algorithm"] == algorithm]
        by_seed: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
        for row in rows:
            by_seed[int(row["seed"])].append(row)
        if smoke or tuple(sorted(by_seed)) != tuple(sorted(pipeline.promotion.required_seeds)):
            decisions[algorithm] = {
                "algorithm": algorithm,
                "research_ready": False,
                "status": "RESEARCH_REJECTED",
                "blockers": ["EXACT_TEN_SEEDS_REQUIRED" if not smoke else "SMOKE_RUN_NOT_PROMOTION_CAPABLE"],
                "execution_authority": EXECUTION_AUTHORITY,
                "broker_calls": 0,
                "order_calls": 0,
            }
            continue
        seed_rows: list[SeedEvaluationV221] = []
        all_returns: list[float] = []
        regime_counts = {name: 0 for name in pipeline.required_regimes}
        for row in rows:
            observed = dict(row.get("regime_counts") or {})
            for name in regime_counts:
                regime_counts[name] += int(observed.get(name, 0))
        for seed in pipeline.promotion.required_seeds:
            values = sorted(by_seed[seed], key=lambda value: int(value["fold"]))
            fold_returns = tuple(float(value["fold_net_return"]) for value in values)
            all_returns.extend(fold_returns)
            seed_rows.append(
                SeedEvaluationV221(
                    seed=seed,
                    fold_net_returns=fold_returns,
                    strategy_return=float(np.prod([1.0 + value for value in fold_returns]) - 1.0),
                    baseline_return=float(np.prod([1.0 + float(value["baseline_return"]) for value in values]) - 1.0),
                    cost_stress_return=float(np.prod([1.0 + float(value["cost_stress_return"]) for value in values]) - 1.0),
                    severe_stress_return=float(np.prod([1.0 + float(value["severe_stress_return"]) for value in values]) - 1.0),
                    maximum_drawdown=max(float(value["maximum_drawdown"]) for value in values),
                    maximum_concentration=max(float(value["maximum_concentration"]) for value in values),
                    reproducible=all(bool(value["reproducible"]) for value in values),
                    constraint_violations=sum(int(value["constraint_violations"]) for value in values),
                )
            )
        evidence = RLPromotionEvidenceV221(
            algorithm=algorithm,
            seeds=tuple(seed_rows),
            deflated_sharpe_probability=_deflated_sharpe_probability(
                all_returns,
                len(results),
            ),
            expectancy_ci_lower_bps=_expectancy_lower_bps(all_returns),
            regime_coverage_complete=all(
                regime_counts[name] >= pipeline.minimum_regime_observations
                for name in pipeline.required_regimes
            ),
            environment_contract_hash=_canonical_hash(
                {"environment": asdict(pipeline.environment), "dataset_hash": dataset_hash}
            ),
            code_commit=code_commit,
        )
        decision = evaluate_rl_promotion_v221(evidence, policy=pipeline.promotion)
        value = decision.to_dict()
        value["regime_counts"] = regime_counts
        decisions[algorithm] = value
    return decisions


def run_rl_marl_pipeline_v221(
    pipeline: RLMARLPipelineConfigV221,
    *,
    smoke: bool = False,
    maximum_folds: int | None = None,
    algorithms: Sequence[str] | None = None,
    seeds: Sequence[int] | None = None,
    verify_reproducibility: bool = False,
    project_root: str | Path | None = None,
) -> Path:
    root = Path(project_root or Path.cwd()).resolve()
    selected_algorithms = tuple(
        str(value).upper() for value in (algorithms or pipeline.algorithms)
    )
    selected_seeds = tuple(int(value) for value in (seeds or pipeline.seeds))
    if smoke:
        selected_algorithms = selected_algorithms[:1]
        selected_seeds = selected_seeds[:1]
        maximum_folds = 1 if maximum_folds is None else maximum_folds
    if not smoke and len(selected_seeds) != 10:
        raise ValueError("non-smoke pipeline runs require exactly ten seeds")
    if any(value not in pipeline.algorithms for value in selected_algorithms):
        raise ValueError("requested algorithm is not enabled by config")

    dataset = load_portfolio_dataset_v221(
        pipeline.data_root,
        symbols=pipeline.symbols,
        timeframe=pipeline.timeframe,
        benchmark_symbol=pipeline.benchmark_symbol,
        verify_hash=pipeline.verify_source_hashes,
    )
    folds = build_walk_forward_plan_v221(
        dataset.episode.steps,
        train_size=pipeline.train_size,
        validation_size=pipeline.validation_size,
        test_size=pipeline.test_size,
        purge=pipeline.purge,
        embargo=pipeline.embargo,
    )
    if maximum_folds is not None:
        if maximum_folds < 1:
            raise ValueError("maximum_folds must be positive")
        folds = folds[:maximum_folds]
    run_root = pipeline.output_root / f"{pipeline.config_hash[:12]}-{dataset.dataset_hash[:12]}"
    run_root.mkdir(parents=True, exist_ok=True)
    code_commit = _git_commit(root)
    trials = tuple(
        RLTrialSpecV221(algorithm=algorithm, seed=seed, fold=fold)
        for algorithm in selected_algorithms
        for fold in range(len(folds))
        for seed in selected_seeds
    )

    def evaluator(trial: RLTrialSpecV221) -> Mapping[str, Any]:
        primary = _train_trial(
            trial,
            split=folds[trial.fold],
            full_episode=dataset.episode,
            pipeline=pipeline,
            dataset_hash=dataset.dataset_hash,
            code_commit=code_commit,
            run_root=run_root,
        )
        if not verify_reproducibility:
            return primary
        repeated = _train_trial(
            trial,
            split=folds[trial.fold],
            full_episode=dataset.episode,
            pipeline=pipeline,
            dataset_hash=dataset.dataset_hash,
            code_commit=code_commit,
            run_root=run_root / "reproducibility",
        )
        comparable = (
            "strategy_return",
            "baseline_return",
            "cost_stress_return",
            "severe_stress_return",
            "maximum_drawdown",
            "maximum_concentration",
            "constraint_violations",
            "checkpoint_tensor_sha256",
        )
        primary["reproducible"] = all(primary[key] == repeated[key] for key in comparable)
        primary["reproducibility_hash"] = _canonical_hash(
            {key: repeated[key] for key in comparable}
        )
        return primary

    results, ledger = run_trial_matrix_v221(
        trials,
        evaluator,
        config_hash=pipeline.config_hash,
    )
    trial_path = run_root / "trials.jsonl"
    ledger_path = run_root / "ledger.jsonl"
    config_path = run_root / "config.snapshot.json"
    dataset_path = run_root / "dataset.manifest.json"
    _atomic_text(trial_path, "".join(_canonical_json(row) + "\n" for row in results))
    _atomic_text(ledger_path, ledger.to_jsonl())
    _atomic_json(config_path, pipeline.to_dict())
    _atomic_json(dataset_path, dataset.manifest())
    decisions = _promotion_summary(
        results,
        pipeline,
        dataset_hash=dataset.dataset_hash,
        code_commit=code_commit,
        smoke=smoke,
        algorithms=selected_algorithms,
    )
    summary = {
        "schema_version": "v2.21.1",
        "status": "PIPELINE_COMPLETE",
        "smoke": smoke,
        "algorithms": list(selected_algorithms),
        "seeds": list(selected_seeds),
        "folds": len(folds),
        "trials": len(results),
        "reproducibility_verified": bool(verify_reproducibility),
        "dataset_hash": dataset.dataset_hash,
        "config_hash": pipeline.config_hash,
        "code_commit": code_commit,
        "promotion": decisions,
        "artifacts": {
            "trials.jsonl": sha256_path_v221(trial_path),
            "ledger.jsonl": sha256_path_v221(ledger_path),
            "config.snapshot.json": sha256_path_v221(config_path),
            "dataset.manifest.json": sha256_path_v221(dataset_path),
        },
        "deployment_mode": DEPLOYMENT_MODE,
        "automatic_live_promotion": False,
        "execution_authority": EXECUTION_AUTHORITY,
        "broker_calls": 0,
        "order_calls": 0,
    }
    _atomic_json(run_root / "summary.json", summary)
    return run_root


def audit_rl_marl_pipeline_v221(run_root: str | Path) -> dict[str, Any]:
    root = Path(run_root)
    summary_path = root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    blockers: list[str] = []
    if summary.get("schema_version") != "v2.21.1":
        blockers.append("UNSUPPORTED_SUMMARY_SCHEMA")
    if summary.get("execution_authority") != EXECUTION_AUTHORITY:
        blockers.append("EXECUTION_AUTHORITY_PRESENT")
    if int(summary.get("broker_calls", -1)) != 0 or int(summary.get("order_calls", -1)) != 0:
        blockers.append("EXTERNAL_ORDER_ACTIVITY")
    for relative, expected in dict(summary.get("artifacts") or {}).items():
        path = root / relative
        if not path.is_file():
            blockers.append(f"MISSING_ARTIFACT:{relative}")
        elif sha256_path_v221(path) != expected:
            blockers.append(f"ARTIFACT_HASH_MISMATCH:{relative}")
    trial_path = root / "trials.jsonl"
    trials = [
        json.loads(line)
        for line in trial_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if trial_path.is_file() else []
    if len(trials) != int(summary.get("trials", -1)):
        blockers.append("TRIAL_COUNT_MISMATCH")
    for trial in trials:
        if trial.get("execution_authority") != EXECUTION_AUTHORITY:
            blockers.append("TRIAL_EXECUTION_AUTHORITY_PRESENT")
        expected_artifact_hash = str(trial.get("artifact_hash", ""))
        unsigned = {key: value for key, value in trial.items() if key != "artifact_hash"}
        if _canonical_hash(unsigned) != expected_artifact_hash:
            blockers.append("TRIAL_ARTIFACT_HASH_MISMATCH")
        manifest = root / str(trial.get("checkpoint_manifest", ""))
        try:
            checkpoint = verify_research_checkpoint_v221(manifest)
            if checkpoint["weights_sha256"] != trial.get("checkpoint_weights_sha256"):
                blockers.append("CHECKPOINT_HASH_BINDING_MISMATCH")
            if checkpoint["tensor_sha256"] != trial.get("checkpoint_tensor_sha256"):
                blockers.append("CHECKPOINT_TENSOR_BINDING_MISMATCH")
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            blockers.append(f"INVALID_CHECKPOINT:{type(exc).__name__}")
    ledger_path = root / "ledger.jsonl"
    try:
        entries = tuple(
            SeedLedgerEntryV221(**json.loads(line))
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        ledger = ImmutableSeedLedgerV221.from_entries(entries)
        if len(ledger.entries) != len(trials):
            blockers.append("LEDGER_TRIAL_COUNT_MISMATCH")
    except (FileNotFoundError, TypeError, ValueError, json.JSONDecodeError):
        blockers.append("INVALID_SEED_LEDGER")
    unique = list(dict.fromkeys(blockers))
    audit = {
        "schema_version": "v2.21.1",
        "valid": not unique,
        "blockers": unique,
        "trials": len(trials),
        "automatic_live_promotion": False,
        "execution_authority": EXECUTION_AUTHORITY,
        "broker_calls": 0,
        "order_calls": 0,
    }
    _atomic_json(root / "audit.json", audit)
    return audit
