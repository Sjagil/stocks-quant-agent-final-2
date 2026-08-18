from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pytest

from stocks.rl.contracts_v2_21 import (
    DEPLOYMENT_MODE,
    EXECUTION_AUTHORITY,
    MAPPOConfigV221,
    MATD3ConfigV221,
    PortfolioEnvironmentConfigV221,
    PortfolioEpisodeV221,
    PromotionPolicyV221,
)
from stocks.rl.mappo_v2_21 import (
    CentralizedValueCriticV221,
    MAPPORolloutBufferV221,
    MAPPORolloutTransitionV221,
    MAPPOTrainerV221,
    generalized_advantage_estimate,
)
from stocks.rl.matd3_v2_21 import (
    MATD3BenchmarkV221,
    MATD3ReplayBufferV221,
    MATD3TransitionV221,
    clipped_double_q_target,
)
from stocks.rl.portfolio_environment_v2_21 import (
    CausalMultiAssetPortfolioEnvV221,
    one_way_turnover,
    project_long_only_weights,
)
from stocks.rl.research_automation_v2_21 import (
    build_trial_matrix_v221,
    collect_and_update_mappo_v221,
    collect_matd3_experience_v221,
    run_trial_matrix_v221,
)
from stocks.rl.validation_v2_21 import (
    ImmutableSeedLedgerV221,
    RLPromotionEvidenceV221,
    SeedEvaluationV221,
    build_walk_forward_plan_v221,
    evaluate_rl_promotion_v221,
)

ROOT = Path(__file__).resolve().parents[1]


def episode(
    *,
    asset_returns: np.ndarray | None = None,
    steps: int = 4,
    assets: int = 3,
) -> PortfolioEpisodeV221:
    returns = (
        np.asarray(asset_returns, dtype=np.float64)
        if asset_returns is not None
        else np.full((steps, assets), 0.01, dtype=np.float64)
    )
    time_count, asset_count = returns.shape
    timestamps = np.arange(time_count + 1, dtype=np.int64) + 10
    return PortfolioEpisodeV221(
        local_observations=np.zeros((time_count + 1, asset_count, 4), dtype=np.float32),
        global_observations=np.zeros((time_count + 1, 2), dtype=np.float32),
        asset_returns=returns,
        benchmark_returns=np.zeros(time_count, dtype=np.float64),
        tradable_mask=np.ones((time_count + 1, asset_count), dtype=bool),
        timestamps=timestamps,
        feature_cutoffs=timestamps.copy(),
    )


def test_episode_rejects_lookahead_feature_cutoffs():
    with pytest.raises(ValueError, match="lookahead"):
        PortfolioEpisodeV221(
            local_observations=np.zeros((3, 1, 1)),
            global_observations=np.zeros((3, 1)),
            asset_returns=np.zeros((2, 1)),
            benchmark_returns=np.zeros(2),
            tradable_mask=np.ones((3, 1), dtype=bool),
            timestamps=np.asarray([10, 20, 30]),
            feature_cutoffs=np.asarray([11, 20, 30]),
        )


def test_long_only_projection_applies_mask_asset_cap_and_gross_cap():
    projected = project_long_only_weights(
        np.asarray([-1.0, 0.9, 0.8, 0.7]),
        np.asarray([True, True, False, True]),
        max_asset_weight=0.4,
        max_gross_exposure=0.6,
    )
    assert np.all(projected >= 0)
    assert projected[2] == 0
    assert projected.max() <= 0.4
    assert projected.sum() == pytest.approx(0.6)


def test_turnover_includes_cash_leg_and_counts_one_way():
    assert one_way_turnover(
        np.asarray([0.0, 0.0]), np.asarray([0.3, 0.2])
    ) == pytest.approx(0.5)
    assert one_way_turnover(
        np.asarray([0.3, 0.2]), np.asarray([0.2, 0.3])
    ) == pytest.approx(0.1)


def test_environment_reconciles_equity_weights_and_cost_once():
    config = PortfolioEnvironmentConfigV221(
        max_asset_weight=0.5,
        max_gross_exposure=0.9,
        transaction_cost_bps=5,
        slippage_bps=5,
    )
    env = CausalMultiAssetPortfolioEnvV221(
        episode(asset_returns=np.asarray([[0.10, 0.0], [0.0, 0.0]])),
        config=config,
    )
    env.reset(seed=7)
    result = env.step(np.asarray([0.5, 0.4]))

    expected_turnover = 0.9
    expected_cost = expected_turnover * 0.001
    expected_net_return = 0.5 * 0.10 - expected_cost
    assert result.info["turnover"] == pytest.approx(expected_turnover)
    assert result.info["transaction_cost"] == pytest.approx(expected_cost)
    assert result.info["net_return"] == pytest.approx(expected_net_return)
    assert result.info["equity"] == pytest.approx(
        config.initial_equity * (1 + expected_net_return)
    )
    assert (
        result.observation.portfolio_weights.sum() + result.observation.cash_weight
    ) == pytest.approx(1.0)


def test_observation_exposes_dynamic_actor_and_critic_context():
    env = CausalMultiAssetPortfolioEnvV221(episode(steps=2, assets=2))
    observation = env.reset(seed=3)
    actor_state = observation.decentralized_actor_state()
    critic_state = observation.centralized_critic_state(
        initial_equity=env.config.initial_equity
    )
    assert actor_state.shape == (2, 8)
    assert critic_state.shape == (6,)
    assert np.all(actor_state[:, -4] == 0)
    assert np.all(actor_state[:, -3] == 1)


def test_higher_costs_strictly_reduce_equity():
    data = episode(asset_returns=np.zeros((2, 2)))
    low = CausalMultiAssetPortfolioEnvV221(
        data,
        config=PortfolioEnvironmentConfigV221(
            transaction_cost_bps=1,
            slippage_bps=1,
        ),
    )
    high = CausalMultiAssetPortfolioEnvV221(
        data,
        config=PortfolioEnvironmentConfigV221(
            transaction_cost_bps=10,
            slippage_bps=10,
        ),
    )
    low_result = low.step(np.asarray([0.3, 0.3]))
    high_result = high.step(np.asarray([0.3, 0.3]))
    assert high_result.observation.equity < low_result.observation.equity


def test_reward_is_not_clipped_and_metadata_is_non_authoritative():
    env = CausalMultiAssetPortfolioEnvV221(
        episode(asset_returns=np.asarray([[0.5], [0.0]])),
        config=PortfolioEnvironmentConfigV221(
            max_asset_weight=0.9,
            return_normalizer=0.01,
        ),
    )
    result = env.step(np.asarray([0.9]))
    assert result.team_reward > 10.0
    assert result.info["deployment_mode"] == "SHADOW_ONLY"
    assert result.info["execution_authority"] == "NONE"
    assert result.info["broker_calls"] == 0
    assert result.info["order_calls"] == 0


def test_drawdown_hard_limit_terminates_episode():
    env = CausalMultiAssetPortfolioEnvV221(
        episode(asset_returns=np.asarray([[-0.5], [0.0]])),
        config=PortfolioEnvironmentConfigV221(
            max_asset_weight=0.9,
            drawdown_hard_limit=0.10,
        ),
    )
    result = env.step(np.asarray([0.9]))
    assert result.terminated is True
    assert result.truncated is False
    assert result.info["hard_drawdown_stop"] is True
    with pytest.raises(RuntimeError, match="finished"):
        env.step(np.asarray([0.0]))


def test_gae_bootstraps_truncation_but_not_true_termination():
    common = {
        "rewards": np.asarray([[0.0]]),
        "values": np.asarray([[1.0]]),
        "next_values": np.asarray([[2.0]]),
        "gamma": 0.9,
        "gae_lambda": 0.95,
    }
    truncated = generalized_advantage_estimate(
        **common,
        terminated=np.asarray([False]),
        truncated=np.asarray([True]),
    )
    terminated = generalized_advantage_estimate(
        **common,
        terminated=np.asarray([True]),
        truncated=np.asarray([False]),
    )
    assert truncated[0, 0] == pytest.approx(0.8)
    assert terminated[0, 0] == pytest.approx(-1.0)


def test_mappo_rollout_builds_agent_advantages_and_clears():
    buffer = MAPPORolloutBufferV221()
    for truncated in (False, True):
        buffer.add(
            MAPPORolloutTransitionV221(
                local_observations=np.zeros((2, 3)),
                global_observation=np.zeros(2),
                eligible_mask=np.ones(2, dtype=bool),
                actions=np.full(2, 0.5),
                log_probabilities=np.zeros(2),
                rewards=np.full(2, 0.1),
                value=0.0,
                terminated=False,
                truncated=truncated,
            )
        )
    batch = buffer.training_batch(last_value=0.2, gamma=0.99, gae_lambda=0.95)
    assert batch["advantages"].shape == (2, 2)
    assert batch["returns"].shape == (2, 2)
    buffer.clear()
    assert len(buffer) == 0


def test_mappo_actor_mask_critic_and_update_are_finite():
    pytest.importorskip("torch")
    config = MAPPOConfigV221(
        local_observation_dim=3,
        global_observation_dim=2,
        actor_hidden_dims=(16, 16),
        critic_hidden_dims=(32, 32),
        update_epochs=2,
        target_kl=10.0,
    )
    trainer = MAPPOTrainerV221(config, seed=11)
    action = trainer.act(
        np.zeros((3, 3), dtype=np.float32),
        np.zeros(2, dtype=np.float32),
        np.asarray([True, False, True]),
        deterministic=True,
    )
    assert action.actions.shape == (3,)
    assert np.all((action.actions >= 0) & (action.actions <= 1))
    assert action.actions[1] == 0
    assert action.log_probabilities[1] == 0
    assert np.isfinite(action.value)

    time_count, agent_count = 5, 3
    rng = np.random.default_rng(4)
    batch = {
        "local_observations": rng.normal(size=(time_count, agent_count, 3)).astype(
            np.float32
        ),
        "global_observations": rng.normal(size=(time_count, 2)).astype(np.float32),
        "eligible_mask": np.ones((time_count, agent_count), dtype=bool),
        "actions": np.clip(
            rng.uniform(size=(time_count, agent_count)),
            1e-4,
            1 - 1e-4,
        ).astype(np.float32),
        "old_log_probabilities": np.zeros((time_count, agent_count), dtype=np.float32),
        "advantages": rng.normal(size=(time_count, agent_count)).astype(np.float32),
        "returns": rng.normal(size=(time_count, agent_count)).astype(np.float32),
        "old_values": np.zeros(time_count, dtype=np.float32),
    }
    metrics = trainer.update(batch)
    for field in ("policy_loss", "value_loss", "entropy", "approximate_kl"):
        assert np.isfinite(metrics[field])
    assert metrics["policy_samples"] == time_count * agent_count
    assert trainer.manifest()["centralized_value_critic"] is True
    assert trainer.manifest()["execution_authority"] == "NONE"


def test_mappo_critic_interface_has_no_action_input():
    parameters = inspect.signature(CentralizedValueCriticV221.forward).parameters
    assert set(parameters) == {
        "self",
        "local_observations",
        "global_observations",
        "eligible_mask",
    }


def matd3_transition(value: float) -> MATD3TransitionV221:
    return MATD3TransitionV221(
        local_observations=np.full((2, 3), value, dtype=np.float32),
        global_observation=np.full(2, value, dtype=np.float32),
        eligible_mask=np.ones(2, dtype=bool),
        actions=np.full(2, 0.4, dtype=np.float32),
        reward=value,
        next_local_observations=np.full((2, 3), value + 0.1, dtype=np.float32),
        next_global_observation=np.full(2, value + 0.1, dtype=np.float32),
        next_eligible_mask=np.ones(2, dtype=bool),
        terminated=False,
    )


def test_matd3_replay_is_bounded_and_returns_joint_batches():
    buffer = MATD3ReplayBufferV221(2, seed=1)
    for value in (0.1, 0.2, 0.3):
        buffer.add(matd3_transition(value))
    assert len(buffer) == 2
    batch = buffer.sample(2)
    assert batch["local_observations"].shape == (2, 2, 3)
    assert batch["actions"].shape == (2, 2)


def test_matd3_uses_clipped_double_q_and_delayed_actor_updates():
    torch = pytest.importorskip("torch")
    assert torch.equal(
        clipped_double_q_target(torch.tensor([1.0, 4.0]), torch.tensor([2.0, 3.0])),
        torch.tensor([1.0, 3.0]),
    )
    config = MATD3ConfigV221(
        agents=2,
        local_observation_dim=3,
        global_observation_dim=2,
        hidden_dims=(16, 16),
        policy_delay=2,
    )
    benchmark = MATD3BenchmarkV221(config, seed=2)
    buffer = MATD3ReplayBufferV221(8, seed=2)
    for value in (0.1, 0.2, 0.3, 0.4):
        buffer.add(matd3_transition(value))
    batch = buffer.sample(4)
    first = benchmark.update(batch)
    second = benchmark.update(batch)
    assert first["actor_updated"] is False
    assert second["actor_updated"] is True
    assert np.isfinite(first["critic_loss"])
    assert np.isfinite(second["actor_loss"])
    actions = benchmark.select_actions(np.zeros((2, 3)), np.asarray([True, False]))
    assert actions.shape == (2,)
    assert actions[1] == 0
    manifest = benchmark.manifest()
    assert manifest["role"] == "SEPARATE_OFF_POLICY_BENCHMARK"
    assert manifest["shares_mappo_replay_or_updates"] is False


def test_collectors_connect_algorithms_to_same_causal_environment_contract():
    pytest.importorskip("torch")
    mappo_env = CausalMultiAssetPortfolioEnvV221(episode(steps=3, assets=2))
    mappo = MAPPOTrainerV221(
        MAPPOConfigV221(
            local_observation_dim=8,
            global_observation_dim=6,
            actor_hidden_dims=(16,),
            critic_hidden_dims=(16,),
            update_epochs=1,
            target_kl=10.0,
        ),
        seed=5,
    )
    mappo_result = collect_and_update_mappo_v221(
        mappo_env,
        mappo,
        seed=5,
    )
    assert mappo_result["rollout_steps"] == 3
    assert mappo_result["execution_authority"] == "NONE"

    matd3_env = CausalMultiAssetPortfolioEnvV221(episode(steps=3, assets=2))
    matd3 = MATD3BenchmarkV221(
        MATD3ConfigV221(
            agents=2,
            local_observation_dim=8,
            global_observation_dim=6,
            hidden_dims=(16,),
        ),
        seed=5,
    )
    replay = MATD3ReplayBufferV221(8, seed=5)
    matd3_result = collect_matd3_experience_v221(
        matd3_env,
        matd3,
        replay,
        seed=5,
        exploration_noise=0.0,
    )
    assert matd3_result["collected_transitions"] == 3
    assert matd3_result["replay_size"] == 3
    assert matd3_result["execution_authority"] == "NONE"


def passing_evidence() -> RLPromotionEvidenceV221:
    rows = tuple(
        SeedEvaluationV221(
            seed=seed,
            fold_net_returns=(0.02, 0.01, -0.001, 0.03),
            strategy_return=0.12,
            baseline_return=0.06,
            cost_stress_return=0.04,
            severe_stress_return=0.02,
            maximum_drawdown=0.08,
            maximum_concentration=0.25,
            reproducible=True,
        )
        for seed in range(10)
    )
    return RLPromotionEvidenceV221(
        algorithm="MAPPO",
        seeds=rows,
        deflated_sharpe_probability=0.97,
        expectancy_ci_lower_bps=1.5,
        regime_coverage_complete=True,
        environment_contract_hash="a" * 64,
        code_commit="deadbeef",
    )


def test_promotion_gate_requires_full_evidence_but_remains_shadow_only():
    decision = evaluate_rl_promotion_v221(passing_evidence())
    assert decision.research_ready is True
    assert decision.seed_count == 10
    assert decision.seed_wins == 10
    assert decision.positive_fold_ratio == pytest.approx(0.75)
    assert decision.status == "SHADOW_RESEARCH_READY"
    assert decision.deployment_mode == DEPLOYMENT_MODE
    assert decision.automatic_live_promotion is False
    assert decision.execution_authority == EXECUTION_AUTHORITY
    assert decision.broker_calls == 0
    assert decision.order_calls == 0


def test_promotion_gate_fails_closed_on_missing_seeds_and_bad_stress():
    source = passing_evidence()
    bad_seed = SeedEvaluationV221(
        seed=0,
        fold_net_returns=(-0.1, -0.1),
        strategy_return=-0.2,
        baseline_return=0.0,
        cost_stress_return=-0.2,
        severe_stress_return=-0.3,
        maximum_drawdown=0.3,
        maximum_concentration=0.8,
        reproducible=False,
        constraint_violations=1,
    )
    evidence = RLPromotionEvidenceV221(
        algorithm=source.algorithm,
        seeds=(bad_seed,),
        deflated_sharpe_probability=0.2,
        expectancy_ci_lower_bps=-5.0,
        regime_coverage_complete=False,
        environment_contract_hash=source.environment_contract_hash,
        code_commit=source.code_commit,
    )
    decision = evaluate_rl_promotion_v221(evidence)
    assert decision.research_ready is False
    assert "EXACT_TEN_SEEDS_REQUIRED" in decision.blockers
    assert "HARD_CONSTRAINT_VIOLATION" in decision.blockers
    assert decision.execution_authority == "NONE"


def test_promotion_policy_rejects_any_seed_count_other_than_ten():
    with pytest.raises(ValueError, match="exactly ten"):
        PromotionPolicyV221(required_seeds=(1, 2, 3))


def test_walk_forward_plan_preserves_purge_and_embargo():
    plan = build_walk_forward_plan_v221(
        150,
        train_size=50,
        validation_size=15,
        test_size=10,
        purge=3,
        embargo=4,
    )
    assert len(plan) > 1
    for fold in plan:
        assert fold.validation_start - fold.train_end == 3
        assert fold.test_start - fold.validation_end == 4


def test_seed_ledger_is_hash_chained_and_tamper_evident():
    ledger = ImmutableSeedLedgerV221()
    first = ledger.append(
        {
            "algorithm": "MAPPO",
            "seed": 0,
            "fold": 0,
            "config_hash": "a" * 64,
            "artifact_hash": "b" * 64,
        }
    )
    second = ledger.append(
        {
            "algorithm": "MAPPO",
            "seed": 1,
            "fold": 0,
            "config_hash": "a" * 64,
            "artifact_hash": "c" * 64,
        }
    )
    assert second.previous_hash == first.entry_hash
    assert ledger.validate() is True
    assert len(ledger.to_jsonl().splitlines()) == 2
    ledger.entries[0].record["seed"] = 99
    assert ledger.validate() is False


def test_trial_matrix_runs_ten_seeds_per_fold_and_hashes_results():
    trials = build_trial_matrix_v221(
        folds=(0, 1),
        algorithms=("MAPPO", "MATD3"),
    )
    assert len(trials) == 40
    results, ledger = run_trial_matrix_v221(
        trials,
        lambda trial: {"score": trial.seed + trial.fold},
        config_hash="d" * 64,
    )
    assert len(results) == len(trials)
    assert len(ledger.entries) == len(trials)
    assert ledger.validate() is True
    assert all(len(row["artifact_hash"]) == 64 for row in results)
    assert all(row["execution_authority"] == "NONE" for row in results)


def test_trial_matrix_rejects_authority_or_order_activity():
    trials = build_trial_matrix_v221(folds=(0,), algorithms=("MAPPO",))
    with pytest.raises(ValueError, match="execution authority"):
        run_trial_matrix_v221(
            trials[:1],
            lambda _: {"execution_authority": "LIVE"},
            config_hash="d" * 64,
        )
    with pytest.raises(ValueError, match="order activity"):
        run_trial_matrix_v221(
            trials[:1],
            lambda _: {"order_calls": 1},
            config_hash="d" * 64,
        )


def test_v221_runtime_has_no_broker_or_order_integration():
    files = (
        ROOT / "src/stocks/rl/portfolio_environment_v2_21.py",
        ROOT / "src/stocks/rl/mappo_v2_21.py",
        ROOT / "src/stocks/rl/matd3_v2_21.py",
        ROOT / "src/stocks/rl/validation_v2_21.py",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "submit_order" not in text
        assert "place_order" not in text
        assert 'execution_authority": "NONE' in text or "EXECUTION_AUTHORITY" in text
