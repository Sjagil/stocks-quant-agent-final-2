from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_TRADE_COLUMNS = (
    "hypothesis_id",
    "strategy",
    "symbol",
    "entry_time",
    "exit_time",
    "gross_return",
    "forced",
)
TRADE_KEY_COLUMNS = (
    "hypothesis_id",
    "symbol",
    "entry_time",
    "exit_time",
)


def _empty_trade_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(REQUIRED_TRADE_COLUMNS))


def _normalize_trade_frame(
    frame: pd.DataFrame,
    *,
    source: str,
) -> pd.DataFrame:
    missing = sorted(set(REQUIRED_TRADE_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"{source}: canonical trade columns missing: {missing}")

    work = frame.copy()
    work["hypothesis_id"] = work["hypothesis_id"].astype(str)
    work["strategy"] = work["strategy"].astype(str)
    work["symbol"] = work["symbol"].astype(str).str.upper()
    for column in ("entry_time", "exit_time"):
        work[column] = pd.to_datetime(work[column], utc=True, errors="coerce")
        if work[column].isna().any():
            raise ValueError(f"{source}: invalid {column}")

    if work.duplicated(list(TRADE_KEY_COLUMNS)).any():
        raise ValueError(f"{source}: duplicate canonical trade keys")

    return work.sort_values(list(TRADE_KEY_COLUMNS)).reset_index(drop=True)


def materialize_survivor_trades(
    trade_cache: Mapping[str, pd.DataFrame],
    survivors: pd.DataFrame,
) -> pd.DataFrame:
    if survivors.empty:
        return _empty_trade_frame()
    if "hypothesis_id" not in survivors.columns:
        raise ValueError("survivors: hypothesis_id missing")

    survivor_ids = tuple(
        sorted(set(survivors["hypothesis_id"].astype(str)))
    )
    parts: list[pd.DataFrame] = []
    missing_ids: list[str] = []
    for hypothesis_id in survivor_ids:
        frame = trade_cache.get(hypothesis_id)
        if frame is None or frame.empty:
            missing_ids.append(hypothesis_id)
            continue
        parts.append(
            _normalize_trade_frame(
                frame,
                source=f"indicator survivor {hypothesis_id}",
            )
        )

    if missing_ids:
        raise ValueError(
            "survivors without canonical trades: "
            + ",".join(missing_ids)
        )

    result = pd.concat(parts, ignore_index=True)
    observed = set(result["hypothesis_id"].astype(str))
    unexpected = sorted(observed - set(survivor_ids))
    if unexpected:
        raise ValueError(
            "indicator trade cache contains unexpected hypothesis ids: "
            + ",".join(unexpected)
        )
    return _normalize_trade_frame(
        result,
        source="indicator survivor trade artifact",
    )


def load_canonical_trade_artifacts(
    *,
    primary_candidates: Sequence[Path],
    supplemental: Sequence[Path] = (),
) -> pd.DataFrame:
    sources: list[tuple[Path, pd.DataFrame]] = []
    for path in primary_candidates:
        if not path.is_file():
            continue
        frame = pd.read_parquet(path)
        if frame.empty:
            continue
        sources.append((path, frame))
        break

    for path in supplemental:
        if not path.is_file():
            continue
        frame = pd.read_parquet(path)
        if not frame.empty:
            sources.append((path, frame))

    if not sources:
        raise FileNotFoundError(
            "No canonical survivor trade artifact found. Run the 1h "
            "strategy factory and indicator discovery first."
        )

    parts: list[pd.DataFrame] = []
    claimed: dict[str, Path] = {}
    for path, frame in sources:
        normalized = _normalize_trade_frame(frame, source=str(path))
        hypothesis_ids = set(normalized["hypothesis_id"].astype(str))
        overlap = sorted(hypothesis_ids & set(claimed))
        if overlap:
            owners = ", ".join(
                f"{item}:{claimed[item]}" for item in overlap
            )
            raise ValueError(
                f"canonical hypothesis supplied by multiple artifacts: "
                f"{owners}; duplicate source={path}"
            )
        for hypothesis_id in hypothesis_ids:
            claimed[hypothesis_id] = path
        normalized["canonical_trade_source"] = str(path)
        parts.append(normalized)

    return _normalize_trade_frame(
        pd.concat(parts, ignore_index=True),
        source="combined canonical trade artifacts",
    )


def configured_validation_coverage(
    summary: pd.DataFrame,
    strategies: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    expected = tuple(str(item["hypothesis_id"]) for item in strategies)
    if len(expected) != len(set(expected)):
        raise ValueError("configured strategy hypothesis ids are not unique")

    required = {"hypothesis_id", "status"}
    missing_columns = sorted(required - set(summary.columns))
    if missing_columns:
        raise ValueError(
            f"strategy summary columns missing: {missing_columns}"
        )

    work = summary.copy()
    work["hypothesis_id"] = work["hypothesis_id"].astype(str)
    configured = work.loc[work["hypothesis_id"].isin(expected)]
    if configured["hypothesis_id"].duplicated().any():
        raise ValueError("strategy summary contains duplicate hypotheses")

    status_by_id = dict(
        zip(configured["hypothesis_id"], configured["status"], strict=True)
    )
    missing = sorted(set(expected) - set(status_by_id))
    not_validated = sorted(
        hypothesis_id
        for hypothesis_id, status in status_by_id.items()
        if str(status) != "CROSS_ENGINE_VALIDATED"
    )
    validated_ids = sorted(
        hypothesis_id
        for hypothesis_id, status in status_by_id.items()
        if str(status) == "CROSS_ENGINE_VALIDATED"
    )
    return {
        "validated": not missing and not not_validated,
        "expected": len(expected),
        "validated_count": len(validated_ids),
        "validated_hypothesis_ids": validated_ids,
        "missing_hypothesis_ids": missing,
        "not_validated_hypothesis_ids": not_validated,
    }
