from __future__ import annotations

import numpy as np
import pytest

from stocks.research.purged_walkforward_v2_30 import (
    PurgedWalkForwardConfig,
    assert_no_label_overlap,
    purged_walkforward_splits,
)


def test_purged_splits_have_no_label_overlap():
    cfg = PurgedWalkForwardConfig(
        minimum_train_size=100,
        test_size=20,
        step_size=20,
        purge_bars=10,
    )
    splits = purged_walkforward_splits(250, config=cfg)
    assert len(splits) > 2
    for train, test in splits:
        assert_no_label_overlap(train, test, label_horizon_bars=10)
        assert train.max() + 10 < test.min()


def test_overlap_assertion_fails_without_enough_purge():
    with pytest.raises(AssertionError):
        assert_no_label_overlap(
            np.arange(0, 100),
            np.arange(105, 120),
            label_horizon_bars=10,
        )
