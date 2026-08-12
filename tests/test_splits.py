from stocks.rl.splits import purged_walk_forward_splits


def test_purged_walk_forward_has_gaps():
    splits = purged_walk_forward_splits(
        1000,
        train_size=400,
        validation_size=100,
        test_size=100,
        purge=10,
        embargo=10,
    )
    assert splits
    first = splits[0]
    assert first.validation_start - first.train_end == 10
    assert first.test_start - first.validation_end == 10
