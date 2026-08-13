from __future__ import annotations

import json
import math
from pathlib import Path

from _common import (
    artifact_ref,
    base_health,
    repo_catalog,
    require_path,
    run_worker,
)


CAPABILITIES = (
    "health",
    "catalog",
    "fit_predict_lgbm",
)


def _health(
    request: dict,
) -> dict:
    return base_health(
        request,
        distributions=(
            "pyqlib",
        ),
        imports=(
            "qlib",
            "lightgbm",
            "numpy",
            "pandas",
        ),
        capabilities=(
            CAPABILITIES
        ),
    )


def _catalog(
    request: dict,
) -> dict:
    repo = (
        request.get(
            "context"
        )
        or {}
    ).get(
        "repo_path"
    )

    return {
        "state": "OK",
        "data": {
            "top_level_modules": [],
            "repo_catalog": (
                repo_catalog(
                    repo,
                    (
                        "workflow_config_*Alpha158*.yaml",
                        "workflow_config_*Alpha360*.yaml",
                        "*model*.py",
                        "*risk*.py",
                    ),
                )
            ),
            "purpose": (
                "Independent Qlib ML "
                "prediction challenger."
            ),
        },
    }


class FrameDataset:
    def __init__(
        self,
        frame,
        *,
        feature_columns,
        periods,
        purge_bars: int,
    ):
        self.frame = frame
        self.feature_columns = list(
            feature_columns
        )
        self.periods = periods
        self.purge_bars = int(
            purge_bars
        )
        self.segments = {
            name: value
            for name, value
            in periods.items()
        }

    def _segment(
        self,
        name: str,
    ):
        import pandas as pd

        start, end = (
            self.periods[
                name
            ]
        )

        start = pd.Timestamp(
            start
        )

        end = pd.Timestamp(
            end
        )

        if start.tzinfo is None:
            start = start.tz_localize(
                "UTC"
            )
        else:
            start = start.tz_convert(
                "UTC"
            )

        if end.tzinfo is None:
            end = end.tz_localize(
                "UTC"
            )
        else:
            end = end.tz_convert(
                "UTC"
            )

        result = self.frame.loc[
            (
                self.frame.index
                >= start
            )
            &
            (
                self.frame.index
                <= end
            )
        ].copy()

        if (
            name
            in {
                "train",
                "valid",
            }
            and self.purge_bars > 0
        ):
            if (
                len(result)
                <= self.purge_bars
            ):
                raise ValueError(
                    f"{name}: not enough "
                    "rows after purge"
                )

            result = result.iloc[
                :-self.purge_bars
            ]

        return result

    def prepare(
        self,
        segment,
        col_set=None,
        data_key=None,
    ):
        del data_key

        import pandas as pd

        if not isinstance(
            segment,
            str,
        ):
            raise ValueError(
                "worker dataset expects "
                "named segments"
            )

        frame = self._segment(
            segment
        )

        if col_set == "feature":
            return frame[
                self.feature_columns
            ].copy()

        if col_set == [
            "feature",
            "label",
        ]:
            features = frame[
                self.feature_columns
            ].copy()

            features.columns = (
                pd.MultiIndex.from_tuples(
                    [
                        (
                            "feature",
                            column,
                        )
                        for column
                        in features.columns
                    ]
                )
            )

            label = frame[
                [
                    "label"
                ]
            ].copy()

            label.columns = (
                pd.MultiIndex.from_tuples(
                    [
                        (
                            "label",
                            "label",
                        )
                    ]
                )
            )

            return pd.concat(
                [
                    features,
                    label,
                ],
                axis=1,
            )

        raise ValueError(
            f"unsupported col_set: "
            f"{col_set!r}"
        )


def _finite_or_none(
    value,
):
    try:
        result = float(
            value
        )
    except Exception:
        return None

    return (
        result
        if math.isfinite(
            result
        )
        else None
    )


def _fit_predict_lgbm(
    request: dict,
    artifact_dir: Path,
) -> dict:
    import lightgbm as lgb
    import numpy as np
    import pandas as pd

    from qlib.contrib.model.gbdt import (
        LGBModel,
    )

    payload = dict(
        request.get(
            "payload"
        )
        or {}
    )

    input_path = require_path(
        payload,
        "input_parquet",
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
            or len(value) != 2
        ):
            raise ValueError(
                f"periods.{name} "
                "must be [start, end]"
            )

    frame = pd.read_parquet(
        input_path
    )

    timestamp_column = None

    for candidate in (
        "datetime",
        "timestamp",
        "timestamp_utc",
    ):
        if candidate in frame:
            timestamp_column = (
                candidate
            )
            break

    if timestamp_column is None:
        if isinstance(
            frame.index,
            pd.DatetimeIndex,
        ):
            frame = (
                frame.reset_index()
            )

            timestamp_column = (
                frame.columns[0]
            )
        else:
            raise ValueError(
                "Alpha158 parquet needs "
                "a datetime column"
            )

    frame[
        timestamp_column
    ] = pd.to_datetime(
        frame[
            timestamp_column
        ],
        utc=True,
        errors="coerce",
    )

    frame = (
        frame.dropna(
            subset=[
                timestamp_column
            ]
        )
        .sort_values(
            timestamp_column
        )
        .set_index(
            timestamp_column
        )
    )

    if "label" not in frame:
        raise ValueError(
            "Qlib fitting requires "
            "a label column"
        )

    excluded = {
        "label",
        "vt_symbol",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "vwap",
    }

    feature_columns = []

    for column in frame.columns:
        if column in excluded:
            continue

        converted = pd.to_numeric(
            frame[
                column
            ],
            errors="coerce",
        )

        if converted.notna().any():
            frame[
                column
            ] = converted

            feature_columns.append(
                column
            )

    frame[
        "label"
    ] = pd.to_numeric(
        frame[
            "label"
        ],
        errors="coerce",
    )

    frame = (
        frame[
            feature_columns
            + [
                "label"
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

    preserve_feature_missingness = bool(
        payload.get(
            "preserve_feature_missingness",
            False,
        )
    )

    if preserve_feature_missingness:
        frame = frame.dropna(
            subset=[
                "label",
            ]
        )
    else:
        frame = frame.dropna()

    feature_missing_fraction = float(
        frame[
            feature_columns
        ]
        .isna()
        .mean()
        .mean()
    )

    if len(
        feature_columns
    ) < 50:
        raise ValueError(
            "unexpectedly few Alpha158 "
            f"features: {len(feature_columns)}"
        )

    dataset = FrameDataset(
        frame,
        feature_columns=(
            feature_columns
        ),
        periods=periods,
        purge_bars=int(
            payload.get(
                "purge_bars",
                3,
            )
        ),
    )

    model = LGBModel(
        loss="mse",
        early_stopping_rounds=int(
            payload.get(
                "early_stopping_rounds",
                30,
            )
        ),
        num_boost_round=int(
            payload.get(
                "num_boost_round",
                500,
            )
        ),
        learning_rate=float(
            payload.get(
                "learning_rate",
                0.03,
            )
        ),
        num_leaves=int(
            payload.get(
                "num_leaves",
                31,
            )
        ),
        feature_fraction=float(
            payload.get(
                "feature_fraction",
                0.90,
            )
        ),
        bagging_fraction=float(
            payload.get(
                "bagging_fraction",
                0.90,
            )
        ),
        bagging_freq=1,
        seed=int(
            payload.get(
                "seed",
                42,
            )
        ),
        num_threads=int(
            payload.get(
                "num_threads",
                4,
            )
        ),
    )

    prepared = (
        model._prepare_data(
            dataset
        )
    )

    datasets, names = zip(
        *prepared
    )

    evals_result = {}

    model.model = lgb.train(
        model.params,
        datasets[
            0
        ],
        num_boost_round=(
            model.num_boost_round
        ),
        valid_sets=list(
            datasets
        ),
        valid_names=list(
            names
        ),
        callbacks=[
            lgb.early_stopping(
                model.early_stopping_rounds
            ),
            lgb.log_evaluation(
                period=0
            ),
            lgb.record_evaluation(
                evals_result
            ),
        ],
    )

    test = dataset._segment(
        "test"
    )

    predictions = model.predict(
        dataset,
        segment="test",
    ).rename(
        "prediction"
    )

    aligned = pd.concat(
        [
            predictions,
            test[
                "label"
            ].rename(
                "label"
            ),
        ],
        axis=1,
    ).dropna()

    if aligned.empty:
        raise ValueError(
            "no aligned Qlib test "
            "predictions"
        )

    pearson = (
        aligned[
            "prediction"
        ]
        .corr(
            aligned[
                "label"
            ]
        )
    )

    spearman = (
        aligned[
            "prediction"
        ]
        .corr(
            aligned[
                "label"
            ],
            method="spearman",
        )
    )

    mse = float(
        (
            (
                aligned[
                    "prediction"
                ]
                -
                aligned[
                    "label"
                ]
            )
            ** 2
        ).mean()
    )

    directional_accuracy = float(
        (
            np.sign(
                aligned[
                    "prediction"
                ]
            )
            ==
            np.sign(
                aligned[
                    "label"
                ]
            )
        ).mean()
    )

    labels = (
        aligned["label"]
        .astype(float)
    )

    predictions_series = (
        aligned["prediction"]
        .astype(float)
    )

    nonzero = (
        labels != 0.0
    )

    labels_nonzero = labels.loc[
        nonzero
    ]

    predictions_nonzero = (
        predictions_series.loc[
            nonzero
        ]
    )

    actual_positive = (
        labels_nonzero > 0.0
    )

    predicted_positive = (
        predictions_nonzero > 0.0
    )

    positive_rate = float(
        actual_positive.mean()
    )

    majority_class_accuracy = float(
        max(
            positive_rate,
            1.0 - positive_rate,
        )
    )

    directional_accuracy_nonzero = float(
        (
            actual_positive
            == predicted_positive
        ).mean()
    )

    positive_count = int(
        actual_positive.sum()
    )

    negative_count = int(
        (~actual_positive).sum()
    )

    if positive_count:
        positive_recall = float(
            predicted_positive.loc[
                actual_positive
            ].mean()
        )
    else:
        positive_recall = None

    if negative_count:
        negative_recall = float(
            (
                ~predicted_positive.loc[
                    ~actual_positive
                ]
            ).mean()
        )
    else:
        negative_recall = None

    if (
        positive_recall is not None
        and negative_recall is not None
    ):
        balanced_directional_accuracy = (
            0.5
            * (
                positive_recall
                + negative_recall
            )
        )
    else:
        balanced_directional_accuracy = (
            None
        )

    directional_edge_vs_majority = (
        directional_accuracy_nonzero
        - majority_class_accuracy
    )

    lower_threshold = float(
        predictions_series.quantile(
            0.20
        )
    )

    upper_threshold = float(
        predictions_series.quantile(
            0.80
        )
    )

    bottom_returns = labels.loc[
        predictions_series
        <= lower_threshold
    ]

    top_returns = labels.loc[
        predictions_series
        >= upper_threshold
    ]

    bottom_quintile_mean_return = float(
        bottom_returns.mean()
    )

    top_quintile_mean_return = float(
        top_returns.mean()
    )

    top_bottom_return_spread = float(
        top_quintile_mean_return
        - bottom_quintile_mean_return
    )

    symbol = str(
        payload.get(
            "symbol"
        )
        or ""
    ).upper()

    output = (
        aligned.reset_index()
    )

    output[
        "symbol"
    ] = symbol

    prediction_path = (
        artifact_dir
        / "qlib_predictions.parquet"
    )

    output.to_parquet(
        prediction_path,
        index=False,
    )

    model_path = (
        artifact_dir
        / "qlib_lgbm.txt"
    )

    model.model.save_model(
        str(
            model_path
        )
    )

    metrics = {
        "schema": (
            "qlib_lgbm_metrics_v1"
        ),
        "symbol": symbol,
        "feature_count": len(
            feature_columns
        ),
        "test_rows": len(
            aligned
        ),
        "preserve_feature_missingness": (
            preserve_feature_missingness
        ),
        "feature_missing_fraction": (
            feature_missing_fraction
        ),
        "dataset_rows": len(
            frame
        ),
        "pearson_ic": (
            _finite_or_none(
                pearson
            )
        ),
        "spearman_ic": (
            _finite_or_none(
                spearman
            )
        ),
        "mse": mse,
        "directional_accuracy": (
            directional_accuracy
        ),
        "directional_accuracy_nonzero": (
            directional_accuracy_nonzero
        ),
        "label_positive_rate": (
            positive_rate
        ),
        "majority_class_accuracy": (
            majority_class_accuracy
        ),
        "directional_edge_vs_majority": (
            directional_edge_vs_majority
        ),
        "positive_recall": (
            positive_recall
        ),
        "negative_recall": (
            negative_recall
        ),
        "balanced_directional_accuracy": (
            balanced_directional_accuracy
        ),
        "top_quintile_mean_return": (
            top_quintile_mean_return
        ),
        "bottom_quintile_mean_return": (
            bottom_quintile_mean_return
        ),
        "top_bottom_return_spread": (
            top_bottom_return_spread
        ),
        "periods": periods,
        "purge_bars": int(
            payload.get(
                "purge_bars",
                3,
            )
        ),
        "label_semantics": str(
            payload.get(
                "label_semantics"
            )
            or (
                "VeighNa Alpha158 upstream "
                "forward label"
            )
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }

    metrics_path = (
        artifact_dir
        / "qlib_metrics.json"
    )

    metrics_path.write_text(
        json.dumps(
            metrics,
            indent=2,
            sort_keys=True,
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
                model_path,
                media_type=(
                    "text/plain"
                ),
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
                "Qlib worker uses "
                "LGBModel data preparation "
                "and model wrapper; Qlib's "
                "MLflow recorder is bypassed "
                "because the project worker "
                "artifact protocol is canonical."
            )
        ],
    }


def handle(
    request: dict,
    artifact_dir: Path,
) -> dict:
    action = request[
        "action"
    ]

    if action == "health":
        return _health(
            request
        )

    if action == "catalog":
        return _catalog(
            request
        )

    if action == (
        "fit_predict_lgbm"
    ):
        return _fit_predict_lgbm(
            request,
            artifact_dir,
        )

    raise ValueError(
        f"unsupported qlib "
        f"action: {action}"
    )


if __name__ == "__main__":
    run_worker(
        handle
    )
