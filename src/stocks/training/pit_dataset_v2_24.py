from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

SCHEMA = "pit_historical_training_contract_v2_24"
AUTHORITY_NONE = "NONE"


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def dataframe_sha256(frame: pd.DataFrame) -> str:
    normalized = frame.copy()
    normalized = normalized.reindex(sorted(normalized.columns), axis=1)
    payload = pd.util.hash_pandas_object(normalized, index=True).values.tobytes()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class PITHistoricalSplitV224:
    fold: int
    train_start: int
    train_stop: int
    validation_start: int
    validation_stop: int
    test_start: int
    test_stop: int
    purge: int
    embargo: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def build_purged_walk_forward_splits_v224(
    observations: int,
    *,
    train_size: int,
    validation_size: int,
    test_size: int,
    purge: int,
    embargo: int,
    step_size: int | None = None,
) -> tuple[PITHistoricalSplitV224, ...]:
    values = (observations, train_size, validation_size, test_size)
    if min(values) < 1 or min(purge, embargo) < 0:
        raise ValueError("invalid PIT walk-forward sizes")
    step = int(step_size or test_size)
    if step < 1:
        raise ValueError("step_size must be positive")
    folds: list[PITHistoricalSplitV224] = []
    train_start = 0
    fold = 0
    while True:
        train_stop = train_start + train_size
        validation_start = train_stop + purge
        validation_stop = validation_start + validation_size
        test_start = validation_stop + embargo
        test_stop = test_start + test_size
        if test_stop > observations:
            break
        folds.append(
            PITHistoricalSplitV224(
                fold=fold,
                train_start=train_start,
                train_stop=train_stop,
                validation_start=validation_start,
                validation_stop=validation_stop,
                test_start=test_start,
                test_stop=test_stop,
                purge=purge,
                embargo=embargo,
            )
        )
        train_start += step
        fold += 1
    if not folds:
        raise ValueError("dataset is too short for the requested PIT walk-forward plan")
    return tuple(folds)


def _utc(series: pd.Series, name: str) -> pd.Series:
    result = pd.to_datetime(series, utc=True, errors="coerce")
    if result.isna().any():
        raise ValueError(f"{name} contains invalid timestamps")
    return result


def pit_asof_join_v224(
    decisions: pd.DataFrame,
    features: pd.DataFrame,
    *,
    decision_time: str = "decision_time",
    feature_available_at: str = "available_at",
    feature_event_time: str = "event_time",
    entity: str = "symbol",
    value_columns: Sequence[str] | None = None,
    prefix: str = "feature",
) -> pd.DataFrame:
    """Backward as-of join that only exposes information available by decision time."""
    if decision_time not in decisions or feature_available_at not in features:
        raise ValueError("decision/availability timestamp columns are required")
    left = decisions.copy()
    right = features.copy()
    left[decision_time] = _utc(left[decision_time], decision_time)
    right[feature_available_at] = _utc(right[feature_available_at], feature_available_at)
    if feature_event_time in right:
        right[feature_event_time] = _utc(right[feature_event_time], feature_event_time)
        if (right[feature_event_time] > right[feature_available_at]).any():
            raise ValueError("feature event_time cannot be after available_at")

    by = entity if entity in left.columns and entity in right.columns else None
    left["_pit_original_order"] = np.arange(len(left))
    if by:
        left[by] = left[by].astype(str).str.upper().str.strip()
        right[by] = right[by].astype(str).str.upper().str.strip()
    else:
        left = left.sort_values(decision_time)
        right = right.sort_values(feature_available_at)

    values = list(value_columns or [
        column for column in right.columns
        if column not in {feature_available_at, feature_event_time, entity}
    ])
    selected = ([by] if by else []) + [feature_available_at]
    if feature_event_time in right:
        selected.append(feature_event_time)
    selected.extend(values)
    selected = list(dict.fromkeys(selected))
    right = right[selected].rename(
        columns={
            feature_available_at: f"{prefix}_available_at",
            feature_event_time: f"{prefix}_event_time",
            **{column: f"{prefix}_{column}" for column in values},
        }
    )
    if by:
        pieces: list[pd.DataFrame] = []
        for key, left_group in left.groupby(by, sort=False):
            right_group = right.loc[right[by].eq(key)].copy()
            left_group = left_group.sort_values(decision_time)
            right_group = right_group.sort_values(f"{prefix}_available_at")
            if right_group.empty:
                result = left_group.copy()
                for column in right.columns:
                    if column != by and column not in result.columns:
                        result[column] = pd.NA
            else:
                result = pd.merge_asof(
                    left_group,
                    right_group.drop(columns=[by]),
                    left_on=decision_time,
                    right_on=f"{prefix}_available_at",
                    direction="backward",
                    allow_exact_matches=True,
                )
            pieces.append(result)
        joined = pd.concat(pieces, ignore_index=True) if pieces else left.iloc[0:0].copy()
    else:
        joined = pd.merge_asof(
            left,
            right,
            left_on=decision_time,
            right_on=f"{prefix}_available_at",
            direction="backward",
            allow_exact_matches=True,
        )
    known = joined[f"{prefix}_available_at"].notna()
    if (joined.loc[known, f"{prefix}_available_at"] > joined.loc[known, decision_time]).any():
        raise AssertionError("PIT as-of join exposed future information")
    return joined.sort_values("_pit_original_order").drop(columns=["_pit_original_order"]).reset_index(drop=True)


def build_forward_return_labels_v224(
    frame: pd.DataFrame,
    *,
    horizon_bars: int,
    decision_time: str = "decision_time",
    price: str = "close",
    entity: str = "symbol",
    label_name: str = "forward_return",
) -> pd.DataFrame:
    if horizon_bars < 1:
        raise ValueError("horizon_bars must be positive")
    result = frame.copy()
    result[decision_time] = _utc(result[decision_time], decision_time)
    order = [entity, decision_time] if entity in result.columns else [decision_time]
    result = result.sort_values(order).reset_index(drop=True)
    if entity in result.columns:
        grouped = result.groupby(entity, sort=False, group_keys=False)
        future_price = grouped[price].shift(-horizon_bars)
        label_available = grouped[decision_time].shift(-horizon_bars)
    else:
        future_price = result[price].shift(-horizon_bars)
        label_available = result[decision_time].shift(-horizon_bars)
    result[label_name] = pd.to_numeric(future_price, errors="coerce") / pd.to_numeric(
        result[price], errors="coerce"
    ) - 1.0
    result[f"{label_name}_available_at"] = label_available
    return result


def audit_pit_training_frame_v224(
    frame: pd.DataFrame,
    *,
    decision_time: str = "decision_time",
    label_columns: Sequence[str] = (),
) -> dict[str, Any]:
    errors: list[str] = []
    if decision_time not in frame:
        errors.append("DECISION_TIME_MISSING")
        decision = pd.Series(dtype="datetime64[ns, UTC]")
    else:
        try:
            decision = _utc(frame[decision_time], decision_time)
        except ValueError:
            errors.append("DECISION_TIME_INVALID")
            decision = pd.Series(dtype="datetime64[ns, UTC]")

    excluded_availability = set(label_columns) | {
        f"{column}_available_at" for column in label_columns
    }
    availability_columns = [
        column for column in frame.columns
        if column.endswith("_available_at") and column not in excluded_availability
    ]
    future_feature_rows = 0
    if len(decision) == len(frame):
        for column in availability_columns:
            available = pd.to_datetime(frame[column], utc=True, errors="coerce")
            known = available.notna()
            future = known & (available > decision)
            future_feature_rows += int(future.sum())
    if future_feature_rows:
        errors.append("FUTURE_FEATURE_AVAILABILITY")

    duplicates = int(frame.duplicated().sum())
    if duplicates:
        errors.append("DUPLICATE_TRAINING_ROWS")
    return {
        "schema": SCHEMA,
        "valid": not errors,
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "availability_columns": availability_columns,
        "future_feature_rows": future_feature_rows,
        "duplicate_rows": duplicates,
        "dataset_sha256": dataframe_sha256(frame),
        "errors": errors,
        "point_in_time": True,
        "execution_authority": AUTHORITY_NONE,
        "broker_calls": 0,
        "order_calls": 0,
    }


def audit_rl_episode_v221_pit(bundle: Any) -> dict[str, Any]:
    episode = bundle.episode
    timestamps = np.asarray(episode.timestamps)
    cutoffs = np.asarray(episode.feature_cutoffs)
    errors: list[str] = []
    if timestamps.ndim != 1 or cutoffs.ndim != 1 or len(timestamps) != len(cutoffs):
        errors.append("RL_TIMESTAMP_SHAPE_INVALID")
    else:
        if np.any(cutoffs > timestamps):
            errors.append("RL_FEATURE_CUTOFF_AFTER_DECISION")
        if len(timestamps) > 1 and np.any(timestamps[1:] <= timestamps[:-1]):
            errors.append("RL_TIMESTAMPS_NOT_STRICTLY_INCREASING")
    manifest = bundle.manifest()
    if manifest.get("point_in_time") is not True:
        errors.append("RL_MANIFEST_NOT_POINT_IN_TIME")
    if manifest.get("feature_cutoff_at_or_before_decision") is not True:
        errors.append("RL_FEATURE_CUTOFF_CONTRACT_MISSING")
    if manifest.get("forward_filled_bars") is not False:
        errors.append("RL_FORWARD_FILL_NOT_DISABLED")
    if str(manifest.get("execution_authority") or "").upper() != AUTHORITY_NONE:
        errors.append("RL_DATASET_EXECUTION_AUTHORITY_PRESENT")
    return {
        "schema": SCHEMA,
        "mode": "RL_V2_21_COMPATIBILITY_AUDIT",
        "valid": not errors,
        "dataset_hash": bundle.dataset_hash,
        "symbols": list(bundle.symbols),
        "timeframe": bundle.timeframe,
        "observations": int(episode.steps + 1),
        "errors": errors,
        "point_in_time": True,
        "execution_authority": AUTHORITY_NONE,
        "broker_calls": 0,
        "order_calls": 0,
    }



def write_pit_training_splits_v224(
    frame: pd.DataFrame,
    splits: Sequence[PITHistoricalSplitV224],
    output_root: str | Path,
    *,
    metadata: Mapping[str, Any] | None = None,
    label_columns: Sequence[str] = (),
) -> Path:
    """Write immutable CSV train/validation/test folds for any offline AI/agent trainer."""
    audit = audit_pit_training_frame_v224(frame, label_columns=label_columns)
    if not audit["valid"]:
        raise ValueError("PIT training frame failed audit: " + "|".join(audit["errors"]))
    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=True)
    fold_manifest: list[dict[str, Any]] = []
    for split in splits:
        fold_root = output / f"fold-{split.fold:02d}"
        fold_root.mkdir(parents=True, exist_ok=True)
        slices = {
            "train": frame.iloc[split.train_start:split.train_stop].copy(),
            "validation": frame.iloc[split.validation_start:split.validation_stop].copy(),
            "test": frame.iloc[split.test_start:split.test_stop].copy(),
        }
        hashes: dict[str, str] = {}
        for name, value in slices.items():
            path = fold_root / f"{name}.csv"
            value.to_csv(path, index=False)
            hashes[name] = dataframe_sha256(value)
        fold_manifest.append({**split.to_dict(), "hashes": hashes})
    manifest = {
        "schema": SCHEMA,
        "dataset_sha256": audit["dataset_sha256"],
        "folds": fold_manifest,
        "metadata": dict(metadata or {}),
        "point_in_time": True,
        "purged_walk_forward": True,
        "preprocessing_fit_scope": "TRAIN_ONLY",
        "suitable_consumers": ["SUPERVISED_ML", "OFFLINE_AGENT", "RL_RESEARCH"],
        "automatic_live_promotion": False,
        "execution_authority": AUTHORITY_NONE,
        "broker_calls": 0,
        "order_calls": 0,
    }
    manifest["manifest_sha256"] = _canonical_hash(manifest)
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return output

def write_training_manifest_v224(
    path: str | Path,
    *,
    frame: pd.DataFrame,
    splits: Sequence[PITHistoricalSplitV224],
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    audit = audit_pit_training_frame_v224(frame)
    if not audit["valid"]:
        raise ValueError("PIT training frame failed audit: " + "|".join(audit["errors"]))
    payload = {
        "schema": SCHEMA,
        "dataset_sha256": audit["dataset_sha256"],
        "rows": len(frame),
        "columns": list(frame.columns),
        "splits": [split.to_dict() for split in splits],
        "metadata": dict(metadata or {}),
        "point_in_time": True,
        "purged_walk_forward": True,
        "train_only_preprocessing_required": True,
        "automatic_live_promotion": False,
        "execution_authority": AUTHORITY_NONE,
        "broker_calls": 0,
        "order_calls": 0,
    }
    payload["manifest_sha256"] = _canonical_hash(payload)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return destination


__all__ = [
    "PITHistoricalSplitV224",
    "pit_asof_join_v224",
    "build_forward_return_labels_v224",
    "build_purged_walk_forward_splits_v224",
    "audit_pit_training_frame_v224",
    "audit_rl_episode_v221_pit",
    "write_training_manifest_v224",
    "write_pit_training_splits_v224",
]
