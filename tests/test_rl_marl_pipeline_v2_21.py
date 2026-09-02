from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stocks.rl.checkpoint_v2_21 import (
    save_research_checkpoint_v221,
    verify_research_checkpoint_v221,
)
from stocks.rl.contracts_v2_21 import PortfolioEnvironmentConfigV221, PromotionPolicyV221
from stocks.rl.dataset_v2_21 import (
    build_portfolio_episode_from_frames_v221,
    fit_feature_scaler_v221,
    slice_portfolio_episode_v221,
    transform_portfolio_episode_v221,
)
from stocks.rl.pipeline_v2_21 import (
    RLMARLPipelineConfigV221,
    audit_rl_marl_pipeline_v221,
    load_rl_marl_pipeline_config_v221,
    run_rl_marl_pipeline_v221,
)

ROOT = Path(__file__).resolve().parents[1]


def market_frame(seed: int, rows: int = 96) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    index = pd.date_range("2024-01-02 14:30", periods=rows, freq="h", tz="UTC")
    close = 100.0 * np.cumprod(1.0 + rng.normal(0.0002, 0.003, rows))
    return pd.DataFrame(
        {
            "open": close * (1.0 + rng.normal(0.0, 0.0003, rows)),
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": rng.integers(100_000, 200_000, rows).astype(float),
        },
        index=index.rename("timestamp"),
    )


def bundle():
    return build_portfolio_episode_from_frames_v221(
        {"AAA": market_frame(1), "BBB": market_frame(2)},
        timeframe="1h",
        benchmark_symbol="AAA",
    )


def test_dataset_builder_is_aligned_causal_and_finite():
    result = bundle()
    episode = result.episode
    assert result.symbols == ("AAA", "BBB")
    assert episode.assets == 2
    assert episode.local_observations.shape[2] == 6
    assert episode.global_observations.shape[1] == 4
    assert episode.local_observations.shape[0] == episode.steps + 1
    assert np.all(episode.feature_cutoffs <= episode.timestamps)
    assert np.isfinite(episode.asset_returns).all()
    assert result.manifest()["forward_filled_bars"] is False
    assert result.manifest()["execution_authority"] == "NONE"


def test_future_price_change_does_not_change_past_features():
    first = market_frame(3)
    second = market_frame(4)
    original = build_portfolio_episode_from_frames_v221(
        {"AAA": first, "BBB": second}, timeframe="1h"
    ).episode
    changed = first.copy()
    changed.iloc[-1, changed.columns.get_loc("close")] *= 1.5
    changed.iloc[-1, changed.columns.get_loc("high")] = changed.iloc[-1]["close"] * 1.01
    modified = build_portfolio_episode_from_frames_v221(
        {"AAA": changed, "BBB": second}, timeframe="1h"
    ).episode
    np.testing.assert_allclose(
        original.local_observations[:-1],
        modified.local_observations[:-1],
    )


def test_dataset_intersection_does_not_forward_fill_missing_bar():
    first = market_frame(5)
    second = market_frame(6).drop(market_frame(6).index[30])
    result = build_portfolio_episode_from_frames_v221(
        {"AAA": first, "BBB": second}, timeframe="1h"
    )
    missing = first.index[30].to_datetime64()
    assert missing not in set(result.episode.timestamps)


def test_scaler_is_fit_on_training_slice_only():
    episode = bundle().episode
    train = slice_portfolio_episode_v221(episode, 0, 30)
    test = slice_portfolio_episode_v221(episode, 40, 50)
    scaler = fit_feature_scaler_v221(train)
    transformed = transform_portfolio_episode_v221(test, scaler)
    local_train = transform_portfolio_episode_v221(train, scaler).local_observations
    assert np.abs(local_train.mean(axis=(0, 1))).max() < 1e-5
    assert transformed.steps == test.steps
    assert scaler.fitted_observations == 31


class FakeTensor:
    def __init__(self, value):
        self.value = np.asarray(value, dtype=np.float32)

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.value


class FakeModule:
    def state_dict(self):
        return {"weight": FakeTensor([[1.0, 2.0]]), "bias": FakeTensor([0.5])}


class FakeMAPPO:
    actor = FakeModule()
    critic = FakeModule()

    @staticmethod
    def manifest():
        return {
            "algorithm": "MAPPO",
            "execution_authority": "NONE",
            "broker_calls": 0,
            "order_calls": 0,
        }


def test_checkpoint_is_pickle_free_hashed_and_tamper_evident(tmp_path):
    manifest_path = save_research_checkpoint_v221(
        FakeMAPPO(),
        tmp_path,
        algorithm="MAPPO",
        seed=1,
        fold=2,
        dataset_hash="a" * 64,
        config_hash="b" * 64,
        code_commit="1234567",
    )
    manifest = verify_research_checkpoint_v221(manifest_path)
    assert manifest["execution_authority"] == "NONE"
    assert manifest["tensor_count"] == 4
    weights = tmp_path / "weights.npz"
    weights.write_bytes(weights.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_research_checkpoint_v221(manifest_path)


def test_repository_config_loads_exact_ten_seed_shadow_contract():
    config = load_rl_marl_pipeline_config_v221(
        ROOT / "config/rl_marl_pipeline_v2_21.yaml",
        project_root=ROOT,
    )
    assert config.algorithms == ("MAPPO", "MATD3")
    assert config.seeds == tuple(range(10))
    assert config.promotion.required_seeds == tuple(range(10))
    assert config.environment.max_gross_exposure < 1.0
    assert len(config.config_hash) == 64


def test_non_smoke_run_rejects_incomplete_seed_matrix(tmp_path):
    config = RLMARLPipelineConfigV221(
        data_root=tmp_path,
        output_root=tmp_path / "out",
        symbols=("AAA", "BBB"),
        timeframe="1h",
        benchmark_symbol="AAA",
        algorithms=("MAPPO",),
        seeds=(0,),
        train_size=20,
        validation_size=8,
        test_size=8,
        purge=2,
        embargo=2,
        training_updates=1,
        maximum_training_steps=8,
        matd3_replay_capacity=32,
        matd3_batch_size=8,
        matd3_gradient_steps=1,
        actor_hidden_dims=(8,),
        critic_hidden_dims=(8,),
        device="cpu",
        required_regimes=(
            "BULL_LOW_VOL",
            "BULL_HIGH_VOL",
            "BEAR_LOW_VOL",
            "BEAR_HIGH_VOL",
        ),
        minimum_regime_observations=1,
        environment=PortfolioEnvironmentConfigV221(),
        promotion=PromotionPolicyV221(),
    )
    with pytest.raises(ValueError, match="exactly ten seeds"):
        run_rl_marl_pipeline_v221(config, project_root=ROOT)


def test_smoke_pipeline_runs_end_to_end_when_torch_is_available(tmp_path):
    pytest.importorskip("torch")
    pytest.importorskip("pyarrow")
    processed = tmp_path / "data/processed"
    processed.mkdir(parents=True)
    market_frame(7).to_parquet(processed / "AAA_1h.parquet")
    market_frame(8).to_parquet(processed / "BBB_1h.parquet")
    config = RLMARLPipelineConfigV221(
        data_root=tmp_path / "data",
        output_root=tmp_path / "artifacts",
        symbols=("AAA", "BBB"),
        timeframe="1h",
        benchmark_symbol="AAA",
        algorithms=("MAPPO",),
        seeds=tuple(range(10)),
        train_size=20,
        validation_size=8,
        test_size=8,
        purge=2,
        embargo=2,
        training_updates=1,
        maximum_training_steps=8,
        matd3_replay_capacity=32,
        matd3_batch_size=8,
        matd3_gradient_steps=1,
        actor_hidden_dims=(8,),
        critic_hidden_dims=(8,),
        device="cpu",
        required_regimes=(
            "BULL_LOW_VOL",
            "BULL_HIGH_VOL",
            "BEAR_LOW_VOL",
            "BEAR_HIGH_VOL",
        ),
        minimum_regime_observations=1,
        environment=PortfolioEnvironmentConfigV221(
            max_asset_weight=0.4,
            max_gross_exposure=0.8,
        ),
        promotion=PromotionPolicyV221(),
    )
    run_root = run_rl_marl_pipeline_v221(
        config,
        smoke=True,
        project_root=ROOT,
    )
    audit = audit_rl_marl_pipeline_v221(run_root)
    summary = json.loads((run_root / "summary.json").read_text(encoding="utf-8"))
    assert audit["valid"] is True
    assert audit["trials"] == 1
    assert summary["status"] == "PIPELINE_COMPLETE"
    assert summary["promotion"]["MAPPO"]["research_ready"] is False
    assert summary["execution_authority"] == "NONE"
