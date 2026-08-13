from stocks.rl.config import (
    TrainingConfig,
    load_rl_yaml,
)


def test_sac_buffer_is_bounded() -> None:
    cfg = TrainingConfig()

    assert cfg.sac_buffer_size > 0
    assert cfg.sac_buffer_size <= 100_000
    assert cfg.sac_learning_starts >= 100
    assert cfg.sac_learning_starts < cfg.sac_buffer_size


def test_repository_sac_profile_is_bounded() -> None:
    _, _, training, _ = load_rl_yaml(
        "config/rl.yaml"
    )

    assert training.sac_buffer_size == 25_000
    assert training.sac_learning_starts == 1_000
    assert training.sac_train_freq == 1
    assert training.sac_gradient_steps == 1


def test_ppo_defaults_are_unchanged() -> None:
    cfg = TrainingConfig()

    assert cfg.n_steps == 2048
    assert cfg.batch_size == 256
    assert cfg.gamma == 0.995
    assert cfg.gae_lambda == 0.95
    assert cfg.clip_range == 0.10
