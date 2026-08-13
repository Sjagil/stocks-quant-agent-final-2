from stocks.rl.experiment import (
    build_experiment_splits,
)


def test_rl_splits_have_full_window_purge_and_embargo() -> None:
    splits = build_experiment_splits(
        10_000,
        window_size=64,
        max_folds=3,
    )

    assert len(splits) >= 2

    for split in splits:
        assert (
            split.validation_start
            -
            split.train_end
            >= 64
        )

        assert (
            split.test_start
            -
            split.validation_end
            >= 64
        )

        assert (
            split.train_end
            <= split.validation_start
            <= split.validation_end
            <= split.test_start
            <= split.test_end
        )
