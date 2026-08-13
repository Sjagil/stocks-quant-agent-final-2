from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from _common import artifact_ref


def _finite_or_none(
    value,
):
    try:
        result = float(
            value
        )
    except Exception:
        return None

    if not math.isfinite(
        result
    ):
        return None

    return result


def _utc_timestamp(
    value,
) -> pd.Timestamp:
    result = pd.Timestamp(
        value
    )

    if result.tzinfo is None:
        return result.tz_localize(
            "UTC"
        )

    return result.tz_convert(
        "UTC"
    )


def _segment(
    frame: pd.DataFrame,
    periods: dict,
    name: str,
) -> pd.DataFrame:
    start, end = (
        periods[
            name
        ]
    )

    start = _utc_timestamp(
        start
    )

    end = _utc_timestamp(
        end
    )

    result = frame.loc[
        (
            frame[
                "datetime"
            ]
            >= start
        )
        & (
            frame[
                "datetime"
            ]
            <= end
        )
    ].copy()

    if result.empty:
        raise ValueError(
            f"{name}: empty panel segment"
        )

    return result


def _pairwise_accuracy(
    prediction: np.ndarray,
    label: np.ndarray,
) -> float | None:
    if len(
        prediction
    ) < 2:
        return None

    i, j = np.triu_indices(
        len(
            prediction
        ),
        k=1,
    )

    pred_delta = (
        prediction[i]
        - prediction[j]
    )

    label_delta = (
        label[i]
        - label[j]
    )

    valid = (
        label_delta != 0.0
    )

    if not valid.any():
        return None

    correct = (
        np.sign(
            pred_delta[
                valid
            ]
        )
        == np.sign(
            label_delta[
                valid
            ]
        )
    )

    return float(
        correct.mean()
    )


def _evaluate_panel(
    aligned: pd.DataFrame,
    *,
    min_cross_section: int,
) -> tuple[
    dict,
    pd.DataFrame,
]:
    rows = []

    top1_history = []
    top2_history = []

    for decision_time, group in (
        aligned.groupby(
            "datetime",
            sort=True,
        )
    ):
        group = (
            group.dropna(
                subset=[
                    "prediction",
                    "label",
                ]
            )
            .sort_values(
                "prediction"
            )
        )

        if (
            group[
                "symbol"
            ]
            .nunique()
            < min_cross_section
        ):
            continue

        prediction = (
            group[
                "prediction"
            ]
            .to_numpy(
                dtype=float
            )
        )

        label = (
            group[
                "label"
            ]
            .to_numpy(
                dtype=float
            )
        )

        rank_ic = (
            group[
                "prediction"
            ]
            .corr(
                group[
                    "label"
                ],
                method="spearman",
            )
        )

        pearson = (
            group[
                "prediction"
            ]
            .corr(
                group[
                    "label"
                ]
            )
        )

        bottom1 = group.iloc[
            0
        ]

        top1 = group.iloc[
            -1
        ]

        bottom2 = (
            group.head(
                2
            )[
                "label"
            ]
            .mean()
        )

        top2 = (
            group.tail(
                2
            )[
                "label"
            ]
            .mean()
        )

        top1_symbol = str(
            top1[
                "symbol"
            ]
        )

        top2_symbols = tuple(
            sorted(
                group.tail(
                    2
                )[
                    "symbol"
                ]
                .astype(str)
                .tolist()
            )
        )

        top1_history.append(
            top1_symbol
        )

        top2_history.append(
            top2_symbols
        )

        row = {
            "datetime": (
                decision_time
            ),
            "cross_section_size": int(
                len(
                    group
                )
            ),
            "rank_ic": (
                _finite_or_none(
                    rank_ic
                )
            ),
            "pearson_ic": (
                _finite_or_none(
                    pearson
                )
            ),
            "pairwise_rank_accuracy": (
                _pairwise_accuracy(
                    prediction,
                    label,
                )
            ),
            "top1_symbol": (
                top1_symbol
            ),
            "bottom1_symbol": str(
                bottom1[
                    "symbol"
                ]
            ),
            "top1_label": float(
                top1[
                    "label"
                ]
            ),
            "bottom1_label": float(
                bottom1[
                    "label"
                ]
            ),
            "top1_bottom1_label_spread": float(
                top1[
                    "label"
                ]
                - bottom1[
                    "label"
                ]
            ),
            "top2_bottom2_label_spread": float(
                top2
                - bottom2
            ),
            "top2_symbols": (
                "|".join(
                    top2_symbols
                )
            ),
        }

        for column in (
            "raw_return",
            "benchmark_return",
            "excess_return",
        ):
            if column in group:
                row[
                    f"top1_{column}"
                ] = float(
                    top1[
                        column
                    ]
                )

        rows.append(
            row
        )

    group_metrics = pd.DataFrame(
        rows
    )

    if group_metrics.empty:
        raise ValueError(
            "no evaluable panel groups"
        )

    rank_ic = pd.to_numeric(
        group_metrics[
            "rank_ic"
        ],
        errors="coerce",
    ).dropna()

    pearson = pd.to_numeric(
        group_metrics[
            "pearson_ic"
        ],
        errors="coerce",
    ).dropna()

    pairwise = pd.to_numeric(
        group_metrics[
            "pairwise_rank_accuracy"
        ],
        errors="coerce",
    ).dropna()

    spread1 = pd.to_numeric(
        group_metrics[
            "top1_bottom1_label_spread"
        ],
        errors="coerce",
    ).dropna()

    spread2 = pd.to_numeric(
        group_metrics[
            "top2_bottom2_label_spread"
        ],
        errors="coerce",
    ).dropna()

    top1_turnover = (
        float(
            np.mean(
                [
                    current
                    != previous
                    for previous, current
                    in zip(
                        top1_history[
                            :-1
                        ],
                        top1_history[
                            1:
                        ],
                    )
                ]
            )
        )
        if len(
            top1_history
        ) > 1
        else 0.0
    )

    top2_turnovers = []

    for previous, current in zip(
        top2_history[
            :-1
        ],
        top2_history[
            1:
        ],
    ):
        previous_set = set(
            previous
        )

        current_set = set(
            current
        )

        retained = len(
            previous_set
            & current_set
        )

        denominator = max(
            len(
                previous_set
            ),
            1,
        )

        top2_turnovers.append(
            1.0
            - retained
            / denominator
        )

    top2_turnover = (
        float(
            np.mean(
                top2_turnovers
            )
        )
        if top2_turnovers
        else 0.0
    )

    metrics = {
        "test_time_groups": int(
            len(
                group_metrics
            )
        ),
        "mean_cross_section_size": float(
            group_metrics[
                "cross_section_size"
            ].mean()
        ),
        "mean_rank_ic": (
            float(
                rank_ic.mean()
            )
            if not rank_ic.empty
            else None
        ),
        "median_rank_ic": (
            float(
                rank_ic.median()
            )
            if not rank_ic.empty
            else None
        ),
        "positive_rank_ic_ratio": (
            float(
                (
                    rank_ic
                    > 0.0
                ).mean()
            )
            if not rank_ic.empty
            else None
        ),
        "mean_pearson_ic": (
            float(
                pearson.mean()
            )
            if not pearson.empty
            else None
        ),
        "mean_pairwise_rank_accuracy": (
            float(
                pairwise.mean()
            )
            if not pairwise.empty
            else None
        ),
        "mean_top1_bottom1_label_spread": (
            float(
                spread1.mean()
            )
            if not spread1.empty
            else None
        ),
        "median_top1_bottom1_label_spread": (
            float(
                spread1.median()
            )
            if not spread1.empty
            else None
        ),
        "mean_top2_bottom2_label_spread": (
            float(
                spread2.mean()
            )
            if not spread2.empty
            else None
        ),
        "top1_positive_label_rate": float(
            (
                group_metrics[
                    "top1_label"
                ]
                > 0.0
            ).mean()
        ),
        "top1_turnover_proxy": (
            top1_turnover
        ),
        "top2_turnover_proxy": (
            top2_turnover
        ),
    }

    if (
        "top1_excess_return"
        in group_metrics
    ):
        metrics[
            "mean_top1_excess_return"
        ] = float(
            group_metrics[
                "top1_excess_return"
            ].mean()
        )

    if (
        "top1_raw_return"
        in group_metrics
    ):
        metrics[
            "mean_top1_raw_return"
        ] = float(
            group_metrics[
                "top1_raw_return"
            ].mean()
        )

    return (
        metrics,
        group_metrics,
    )


def fit_predict_panel_lgbm(
    request: dict,
    artifact_dir: Path,
) -> dict:
    import lightgbm as lgb

    payload = dict(
        request.get(
            "payload"
        )
        or {}
    )

    input_path = Path(
        str(
            payload.get(
                "input_parquet"
            )
            or ""
        )
    )

    if not input_path.is_file():
        raise FileNotFoundError(
            input_path
        )

    feature_columns = [
        str(
            column
        )
        for column in (
            payload.get(
                "feature_columns"
            )
            or []
        )
    ]

    if not feature_columns:
        raise ValueError(
            "feature_columns is required "
            "for panel fitting"
        )

    if (
        len(
            feature_columns
        )
        != len(
            set(
                feature_columns
            )
        )
    ):
        raise ValueError(
            "duplicate feature columns"
        )

    periods = dict(
        payload.get(
            "periods"
        )
        or {}
    )

    for name in (
        "train",
        "valid",
        "test",
    ):
        value = periods.get(
            name
        )

        if (
            not isinstance(
                value,
                (
                    list,
                    tuple,
                ),
            )
            or len(
                value
            )
            != 2
        ):
            raise ValueError(
                f"periods.{name} "
                "must be [start, end]"
            )

    frame = pd.read_parquet(
        input_path
    )

    required = {
        "datetime",
        "symbol",
        "label",
        *feature_columns,
    }

    missing = (
        required
        - set(
            frame.columns
        )
    )

    if missing:
        raise ValueError(
            "panel parquet missing "
            f"{sorted(missing)}"
        )

    frame[
        "datetime"
    ] = pd.to_datetime(
        frame[
            "datetime"
        ],
        utc=True,
        errors="coerce",
    )

    frame[
        "symbol"
    ] = (
        frame[
            "symbol"
        ]
        .astype(str)
        .str.upper()
    )

    for column in (
        feature_columns
        + [
            "label",
        ]
    ):
        frame[
            column
        ] = pd.to_numeric(
            frame[
                column
            ],
            errors="coerce",
        )

    frame[
        feature_columns
        + [
            "label",
        ]
    ] = (
        frame[
            feature_columns
            + [
                "label",
            ]
        ]
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
    )

    frame = frame.dropna(
        subset=[
            "datetime",
            "symbol",
            "label",
        ]
    )

    if frame.duplicated(
        subset=[
            "datetime",
            "symbol",
        ]
    ).any():
        raise ValueError(
            "duplicate panel datetime/symbol"
        )

    preserve_missingness = bool(
        payload.get(
            "preserve_feature_missingness",
            True,
        )
    )

    if not preserve_missingness:
        frame = frame.dropna(
            subset=feature_columns
        )

    min_cross_section = int(
        payload.get(
            "min_cross_section",
            4,
        )
    )

    counts = (
        frame.groupby(
            "datetime"
        )[
            "symbol"
        ]
        .transform(
            "nunique"
        )
    )

    frame = frame.loc[
        counts
        >= min_cross_section
    ].copy()

    frame = frame.sort_values(
        [
            "datetime",
            "symbol",
        ]
    ).reset_index(
        drop=True
    )

    train = _segment(
        frame,
        periods,
        "train",
    )

    valid = _segment(
        frame,
        periods,
        "valid",
    )

    test = _segment(
        frame,
        periods,
        "test",
    )

    train_set = lgb.Dataset(
        train[
            feature_columns
        ],
        label=train[
            "label"
        ],
        feature_name=(
            feature_columns
        ),
        free_raw_data=False,
    )

    valid_set = lgb.Dataset(
        valid[
            feature_columns
        ],
        label=valid[
            "label"
        ],
        feature_name=(
            feature_columns
        ),
        reference=train_set,
        free_raw_data=False,
    )

    params = {
        "objective": "regression",
        "metric": "l2",
        "learning_rate": float(
            payload.get(
                "learning_rate",
                0.025,
            )
        ),
        "num_leaves": int(
            payload.get(
                "num_leaves",
                31,
            )
        ),
        "feature_fraction": float(
            payload.get(
                "feature_fraction",
                0.90,
            )
        ),
        "bagging_fraction": float(
            payload.get(
                "bagging_fraction",
                0.90,
            )
        ),
        "bagging_freq": 1,
        "seed": int(
            payload.get(
                "seed",
                42,
            )
        ),
        "feature_fraction_seed": int(
            payload.get(
                "seed",
                42,
            )
        ),
        "bagging_seed": int(
            payload.get(
                "seed",
                42,
            )
        ),
        "data_random_seed": int(
            payload.get(
                "seed",
                42,
            )
        ),
        "num_threads": int(
            payload.get(
                "num_threads",
                4,
            )
        ),
        "verbosity": -1,
    }

    evals_result = {}

    model = lgb.train(
        params,
        train_set,
        num_boost_round=int(
            payload.get(
                "num_boost_round",
                800,
            )
        ),
        valid_sets=[
            train_set,
            valid_set,
        ],
        valid_names=[
            "train",
            "valid",
        ],
        callbacks=[
            lgb.early_stopping(
                int(
                    payload.get(
                        "early_stopping_rounds",
                        40,
                    )
                )
            ),
            lgb.log_evaluation(
                period=0
            ),
            lgb.record_evaluation(
                evals_result
            ),
        ],
    )

    prediction = model.predict(
        test[
            feature_columns
        ],
        num_iteration=(
            model.best_iteration
        ),
    )

    metadata_columns = [
        column
        for column in (
            "raw_return",
            "benchmark_return",
            "excess_return",
            "cross_section_size",
        )
        if column in test
    ]

    aligned = test[
        [
            "datetime",
            "symbol",
            "label",
            *metadata_columns,
        ]
    ].copy()

    aligned[
        "prediction"
    ] = prediction

    panel_metrics, group_metrics = (
        _evaluate_panel(
            aligned,
            min_cross_section=(
                min_cross_section
            ),
        )
    )

    feature_missing_fraction = float(
        frame[
            feature_columns
        ]
        .isna()
        .mean()
        .mean()
    )

    prediction_path = (
        artifact_dir
        / "qlib_panel_predictions.parquet"
    )

    aligned.to_parquet(
        prediction_path,
        index=False,
    )

    group_path = (
        artifact_dir
        / "qlib_panel_group_metrics.parquet"
    )

    group_metrics.to_parquet(
        group_path,
        index=False,
    )

    model_path = (
        artifact_dir
        / "qlib_panel_lgbm.txt"
    )

    model.save_model(
        str(
            model_path
        )
    )

    metrics = {
        "schema": (
            "qlib_panel_lgbm_metrics_v1"
        ),
        "engine": (
            "qlib_worker_direct_lightgbm_panel"
        ),
        "feature_count": int(
            len(
                feature_columns
            )
        ),
        "dataset_rows": int(
            len(
                frame
            )
        ),
        "train_rows": int(
            len(
                train
            )
        ),
        "valid_rows": int(
            len(
                valid
            )
        ),
        "test_rows": int(
            len(
                test
            )
        ),
        "preserve_feature_missingness": (
            preserve_missingness
        ),
        "feature_missing_fraction": (
            feature_missing_fraction
        ),
        "min_cross_section": (
            min_cross_section
        ),
        "best_iteration": int(
            model.best_iteration
            or 0
        ),
        "periods": periods,
        "target_kind": str(
            payload.get(
                "target_kind"
            )
            or "cross_sectional_relative_return"
        ),
        "label_semantics": str(
            payload.get(
                "label_semantics"
            )
            or ""
        ),
        "feature_representation": str(
            payload.get(
                "feature_representation"
            )
            or "raw"
        ),
        **panel_metrics,
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }

    metrics_path = (
        artifact_dir
        / "qlib_panel_metrics.json"
    )

    metrics_path.write_text(
        json.dumps(
            metrics,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "state": "OK",
        "data": metrics,
        "artifacts": [
            artifact_ref(
                prediction_path,
                media_type=(
                    "application/"
                    "vnd.apache.parquet"
                ),
                rows=len(
                    aligned
                ),
            ),
            artifact_ref(
                group_path,
                media_type=(
                    "application/"
                    "vnd.apache.parquet"
                ),
                rows=len(
                    group_metrics
                ),
            ),
            artifact_ref(
                model_path,
                media_type="text/plain",
            ),
            artifact_ref(
                metrics_path,
                media_type=(
                    "application/json"
                ),
            ),
        ],
        "warnings": [
            (
                "Panel labels overlap through "
                "the holding horizon; metrics "
                "are research evidence and do "
                "not imply independent samples."
            ),
            (
                "This panel capability has "
                "execution authority NONE and "
                "cannot call the broker."
            ),
        ],
    }
