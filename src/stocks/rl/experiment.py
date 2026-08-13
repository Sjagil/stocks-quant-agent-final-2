from __future__ import annotations

import json
import statistics
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import pandas as pd

from stocks.data.canonical import (
    canonicalize_ohlcv,
)

from .config import (
    EnvironmentConfig,
    RewardConfig,
    TrainingConfig,
)

from .environment import (
    LongOnlySwingEnv,
)

from .evaluator import (
    evaluate_policy,
)

from .features import (
    build_rl_features,
)

from .metrics import (
    summarize_returns,
)

from .splits import (
    WalkForwardSplit,
    purged_walk_forward_splits,
)

from .trainer import (
    load_policy,
    train_policy,
)


DEFAULT_SEEDS = (
    11,
    29,
    47,
)


def build_experiment_splits(
    n_samples: int,
    *,
    window_size: int,
    max_folds: int = 3,
) -> list[WalkForwardSplit]:
    if n_samples < 800:
        raise ValueError(
            "at least 800 fully-observed rows "
            "are required for RL walk-forward research"
        )

    train_size = max(
        4 * window_size,
        int(n_samples * 0.50),
    )

    validation_size = max(
        2 * window_size,
        int(n_samples * 0.15),
    )

    test_size = max(
        2 * window_size,
        int(n_samples * 0.15),
    )

    purge = window_size
    embargo = window_size

    splits = purged_walk_forward_splits(
        n_samples,
        train_size=train_size,
        validation_size=validation_size,
        test_size=test_size,
        purge=purge,
        embargo=embargo,
        step_size=test_size,
    )

    if not splits:
        raise ValueError(
            "dataset is too small after "
            "purge/embargo requirements"
        )

    return splits[:max_folds]


def _prepare_dataset(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    market = canonicalize_ohlcv(
        frame
    )

    features = build_rl_features(
        market
    )

    joined = features.join(
        market["close"]
        .astype(float)
        .rename("__close__")
    )

    joined = (
        joined
        .replace(
            [float("inf"), float("-inf")],
            float("nan"),
        )
        .dropna()
    )

    feature_frame = joined.drop(
        columns=["__close__"]
    )

    close = joined[
        "__close__"
    ].astype(float)

    return (
        feature_frame,
        close,
    )


def _make_env(
    features: pd.DataFrame,
    close: pd.Series,
    start: int,
    end: int,
    *,
    environment: EnvironmentConfig,
    reward: RewardConfig,
) -> LongOnlySwingEnv:
    return LongOnlySwingEnv(
        features.iloc[start:end].copy(),
        close.iloc[start:end].copy(),
        env_cfg=environment,
        reward_cfg=reward,
    )


def _buy_hold_baseline(
    close: pd.Series,
    *,
    window_size: int,
    reward: RewardConfig,
) -> dict:
    usable = close.iloc[
        max(window_size - 1, 0):
    ].copy()

    returns = (
        usable
        .pct_change(
            fill_method=None
        )
        .dropna()
    )

    if not returns.empty:
        one_way_cost = (
            reward.transaction_cost_bps
            +
            reward.slippage_bps
        ) / 10_000.0

        returns.iloc[0] -= (
            one_way_cost
        )

    return summarize_returns(
        returns
    ).to_dict()


def _cash_baseline(
    close: pd.Series,
    *,
    window_size: int,
) -> dict:
    usable = close.iloc[
        max(window_size, 1):
    ]

    returns = pd.Series(
        0.0,
        index=usable.index,
        dtype=float,
    )

    return summarize_returns(
        returns
    ).to_dict()


def _median_validation_seed(
    rows: list[dict],
) -> dict:
    if not rows:
        raise ValueError(
            "no seed evaluations available"
        )

    ranked = sorted(
        rows,
        key=lambda row: (
            float(
                row["validation"][
                    "sharpe"
                ]
            ),
            int(
                row["seed"]
            ),
        ),
    )

    return ranked[
        len(ranked) // 2
    ]


def run_walk_forward_experiment(
    frame: pd.DataFrame,
    *,
    symbol: str,
    timeframe: str,
    output_root: str | Path,
    seeds: Sequence[int] = DEFAULT_SEEDS,
    max_folds: int = 2,
    environment: EnvironmentConfig | None = None,
    reward: RewardConfig | None = None,
    training: TrainingConfig | None = None,
) -> dict:
    environment = (
        environment
        or EnvironmentConfig()
    )

    reward = (
        reward
        or RewardConfig()
    )

    training = (
        training
        or TrainingConfig()
    )

    if len(seeds) < 3:
        raise ValueError(
            "use at least three independent RL seeds"
        )

    features, close = (
        _prepare_dataset(
            frame
        )
    )

    splits = build_experiment_splits(
        len(features),
        window_size=environment.window_size,
        max_folds=max_folds,
    )

    root = (
        Path(output_root)
        / training.algorithm.upper()
        / symbol.upper()
        / timeframe
    )

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    fold_results: list[dict] = []

    for fold_number, split in enumerate(
        splits,
        start=1,
    ):
        seed_results: list[dict] = []

        fold_dir = (
            root
            / f"fold_{fold_number:02d}"
        )

        fold_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        for seed in seeds:
            train_env = _make_env(
                features,
                close,
                split.train_start,
                split.train_end,
                environment=environment,
                reward=reward,
            )

            seed_cfg = replace(
                training,
                seed=int(seed),
            )

            model_path = (
                fold_dir
                / f"seed_{seed}.zip"
            )

            train_policy(
                train_env,
                model_path,
                seed_cfg,
                verbose=0,
            )

            validation_env = _make_env(
                features,
                close,
                split.validation_start,
                split.validation_end,
                environment=environment,
                reward=reward,
            )

            model = load_policy(
                model_path,
                algorithm=seed_cfg.algorithm,
                env=validation_env,
            )

            validation = (
                evaluate_policy(
                    model,
                    validation_env,
                )
            )

            seed_results.append(
                {
                    "seed": int(seed),
                    "model_path": str(
                        model_path
                    ),
                    "validation": asdict(
                        validation
                    ),
                }
            )

            del model
            del train_env
            del validation_env

        selected = (
            _median_validation_seed(
                seed_results
            )
        )

        test_env = _make_env(
            features,
            close,
            split.test_start,
            split.test_end,
            environment=environment,
            reward=reward,
        )

        selected_model = (
            load_policy(
                selected[
                    "model_path"
                ],
                algorithm=training.algorithm,
                env=test_env,
            )
        )

        test_result = (
            evaluate_policy(
                selected_model,
                test_env,
            )
        )

        test_close = close.iloc[
            split.test_start:
            split.test_end
        ]

        fold_results.append(
            {
                "fold": fold_number,
                "split": asdict(
                    split
                ),
                "seeds": seed_results,
                "selected_seed": int(
                    selected["seed"]
                ),
                "selection_policy": (
                    "median_validation_sharpe"
                ),
                "selected_test": asdict(
                    test_result
                ),
                "buy_hold_test": (
                    _buy_hold_baseline(
                        test_close,
                        window_size=environment.window_size,
                        reward=reward,
                    )
                ),
                "cash_test": (
                    _cash_baseline(
                        test_close,
                        window_size=environment.window_size,
                    )
                ),
                "test_used_for_seed_selection": False,
            }
        )

        del selected_model
        del test_env

    test_sharpes = [
        float(
            row[
                "selected_test"
            ][
                "sharpe"
            ]
        )
        for row in fold_results
    ]

    test_returns = [
        float(
            row[
                "selected_test"
            ][
                "total_return"
            ]
        )
        for row in fold_results
    ]

    test_drawdowns = [
        float(
            row[
                "selected_test"
            ][
                "max_drawdown"
            ]
        )
        for row in fold_results
    ]

    payload = {
        "schema": (
            "rl_walk_forward_experiment_v2"
        ),
        "created_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "algorithm": (
            training.algorithm.upper()
        ),
        "seeds": [
            int(seed)
            for seed in seeds
        ],
        "fully_observed_rows": len(
            features
        ),
        "feature_count": (
            features.shape[1]
        ),
        "fold_count": len(
            fold_results
        ),
        "folds": fold_results,
        "summary": {
            "median_test_sharpe": (
                statistics.median(
                    test_sharpes
                )
            ),
            "median_test_return": (
                statistics.median(
                    test_returns
                )
            ),
            "worst_test_drawdown": (
                max(
                    test_drawdowns
                )
            ),
        },
        "research_status": (
            "EVALUATED_CHALLENGER"
        ),
        "money_control": False,
        "direct_broker_calls": 0,
        "execution_authority": "NONE",
    }

    manifest = (
        root
        / "experiment.json"
    )

    manifest.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    payload[
        "artifact"
    ] = str(
        manifest
    )

    return payload
