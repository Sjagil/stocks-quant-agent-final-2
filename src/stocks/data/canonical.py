from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

CANONICAL_SCHEMA_VERSION = "1.0"
OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")
PRICE_COLUMNS = ("open", "high", "low", "close")
OPTIONAL_COLUMNS = ("vwap", "trades")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class CanonicalMetadata:
    symbol: str
    timeframe: str
    source: str
    exchange: str | None = None
    asset_type: str | None = None
    currency: str | None = None
    timezone: str = "UTC"
    adjustment: str = "raw"
    schema_version: str = CANONICAL_SCHEMA_VERSION
    retrieved_at: str = field(default_factory=utc_now_iso)
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if not self.timeframe.strip():
            raise ValueError("timeframe is required")
        if not self.source.strip():
            raise ValueError("source is required")
        if self.timezone != "UTC":
            raise ValueError("canonical market data timezone must be UTC")
        if self.schema_version != CANONICAL_SCHEMA_VERSION:
            raise ValueError(f"unsupported canonical schema: {self.schema_version}")


@dataclass(frozen=True)
class QualityReport:
    rows: int
    start: str | None
    end: str | None
    duplicate_timestamps: int
    non_monotonic: bool
    missing_required_values: int
    non_finite_values: int
    non_positive_prices: int
    negative_volume: int
    invalid_high: int
    invalid_low: int
    zero_volume_rows: int
    max_abs_close_return: float | None
    passed: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SplitEvent:
    effective_at: pd.Timestamp
    factor: float
    source_payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        timestamp = pd.Timestamp(self.effective_at)
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        object.__setattr__(self, "effective_at", timestamp)
        if not np.isfinite(self.factor) or self.factor <= 0:
            raise ValueError("split factor must be finite and positive")


def _to_utc_index(index: pd.Index) -> pd.DatetimeIndex:
    result = pd.to_datetime(index, utc=True, errors="coerce")
    if result.isna().any():
        raise ValueError("timestamp index contains unparseable values")
    return pd.DatetimeIndex(result, name="timestamp")


def canonicalize_ohlcv(
    frame: pd.DataFrame,
    *,
    copy: bool = True,
    drop_duplicate_timestamps: bool = False,
    drop_missing_required: bool = False,
    sort: bool = True,
) -> pd.DataFrame:
    """Normalize arbitrary OHLCV into the repository's canonical UTC schema.

    The function never adjusts prices, forward-fills bars or fabricates volume.
    Corporate actions and session/calendar decisions remain explicit later steps.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    work = frame.copy() if copy else frame
    work.columns = [str(column).strip().lower().replace(" ", "_") for column in work.columns]

    if "timestamp" in work.columns:
        work = work.set_index("timestamp")
    elif "datetime" in work.columns:
        work = work.set_index("datetime")
    elif isinstance(work.index, pd.RangeIndex):
        raise ValueError("canonical OHLCV requires a timestamp/datetime column or DatetimeIndex")
    if not isinstance(work.index, pd.DatetimeIndex):
        work.index = _to_utc_index(work.index)
    else:
        work.index = _to_utc_index(work.index)

    missing = [column for column in OHLCV_COLUMNS if column not in work.columns]
    if missing:
        raise ValueError(f"missing canonical OHLCV columns: {missing}")

    selected = list(OHLCV_COLUMNS) + [column for column in OPTIONAL_COLUMNS if column in work.columns]
    work = work[selected]
    for column in selected:
        work[column] = pd.to_numeric(work[column], errors="coerce")

    if drop_duplicate_timestamps:
        work = work.loc[~work.index.duplicated(keep="last")]
    if sort:
        work = work.sort_index(kind="stable")
    if drop_missing_required:
        work = work.dropna(subset=list(OHLCV_COLUMNS))
    work.index.name = "timestamp"
    return work


def quality_report(frame: pd.DataFrame) -> QualityReport:
    work = canonicalize_ohlcv(
        frame,
        drop_duplicate_timestamps=False,
        drop_missing_required=False,
        sort=False,
    )
    duplicates = int(work.index.duplicated(keep=False).sum())
    missing_required = int(work[list(OHLCV_COLUMNS)].isna().sum().sum())
    numeric = work[list(OHLCV_COLUMNS)].to_numpy(dtype=float, copy=True)
    non_finite = int((~np.isfinite(numeric) & ~np.isnan(numeric)).sum())
    prices = work[list(PRICE_COLUMNS)]
    non_positive = int((prices <= 0).sum().sum())
    negative_volume = int((work["volume"] < 0).sum())
    invalid_high = int((work["high"] < prices[["open", "close", "low"]].max(axis=1)).sum())
    invalid_low = int((work["low"] > prices[["open", "close", "high"]].min(axis=1)).sum())
    zero_volume = int((work["volume"] == 0).sum())
    sorted_close = pd.to_numeric(work["close"], errors="coerce").sort_index(kind="stable")
    returns = sorted_close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).dropna()
    max_abs_return = float(returns.abs().max()) if not returns.empty else None
    warnings: list[str] = []
    if zero_volume:
        warnings.append(f"zero_volume_rows:{zero_volume}")
    if max_abs_return is not None and max_abs_return > 0.50:
        warnings.append(f"extreme_close_return:{max_abs_return:.6f}")
    passed = not any((duplicates, missing_required, non_finite, non_positive, negative_volume, invalid_high, invalid_low))
    return QualityReport(
        rows=len(work),
        start=work.index.min().isoformat() if len(work) else None,
        end=work.index.max().isoformat() if len(work) else None,
        duplicate_timestamps=duplicates,
        non_monotonic=not work.index.is_monotonic_increasing,
        missing_required_values=missing_required,
        non_finite_values=non_finite,
        non_positive_prices=non_positive,
        negative_volume=negative_volume,
        invalid_high=invalid_high,
        invalid_low=invalid_low,
        zero_volume_rows=zero_volume,
        max_abs_close_return=max_abs_return,
        passed=passed and work.index.is_monotonic_increasing,
        warnings=tuple(warnings),
    )


def validate_canonical(frame: pd.DataFrame, *, fail_on_extreme_return: float | None = None) -> QualityReport:
    report = quality_report(frame)
    failures: list[str] = []
    if report.rows == 0:
        failures.append("empty_dataset")
    for name in (
        "duplicate_timestamps",
        "missing_required_values",
        "non_finite_values",
        "non_positive_prices",
        "negative_volume",
        "invalid_high",
        "invalid_low",
    ):
        value = getattr(report, name)
        if value:
            failures.append(f"{name}={value}")
    if report.non_monotonic:
        failures.append("timestamps_not_monotonic")
    if fail_on_extreme_return is not None and report.max_abs_close_return is not None:
        if report.max_abs_close_return > fail_on_extreme_return:
            failures.append(f"max_abs_close_return={report.max_abs_close_return:.6f}>{fail_on_extreme_return}")
    if failures:
        raise ValueError("canonical data validation failed: " + ", ".join(failures))
    return report


def merge_canonical_frames(frames: Iterable[pd.DataFrame]) -> pd.DataFrame:
    materialized = [
        canonicalize_ohlcv(frame, drop_duplicate_timestamps=False, drop_missing_required=False)
        for frame in frames
        if frame is not None and not frame.empty
    ]
    if not materialized:
        return pd.DataFrame(columns=list(OHLCV_COLUMNS), index=pd.DatetimeIndex([], name="timestamp", tz="UTC"))
    merged = pd.concat(materialized, axis=0)
    merged = merged.loc[~merged.index.duplicated(keep="last")].sort_index(kind="stable")
    validate_canonical(merged)
    return merged


def split_factor_from_payload(record: Mapping[str, Any]) -> float:
    old_shares = record.get("old_shares")
    new_shares = record.get("new_shares")
    if old_shares is not None and new_shares is not None:
        old = float(old_shares)
        new = float(new_shares)
        if old <= 0 or new <= 0:
            raise ValueError(f"invalid split shares: {record}")
        return new / old
    raw = record.get("split") or record.get("ratio") or record.get("split_ratio")
    if raw is None:
        raise ValueError(f"split ratio missing: {record}")
    text = str(raw).strip()
    for separator in ("/", ":"):
        if separator in text:
            left, right = text.split(separator, 1)
            numerator, denominator = float(left), float(right)
            if numerator <= 0 or denominator <= 0:
                raise ValueError(f"invalid split ratio: {text}")
            return numerator / denominator
    factor = float(text)
    if factor <= 0:
        raise ValueError(f"invalid split ratio: {text}")
    return factor


def split_events_from_payload(payload: Sequence[Mapping[str, Any]]) -> tuple[SplitEvent, ...]:
    events: list[SplitEvent] = []
    for record in payload:
        date = record.get("date") or record.get("split_date")
        if not date:
            continue
        events.append(
            SplitEvent(
                effective_at=pd.Timestamp(str(date)),
                factor=split_factor_from_payload(record),
                source_payload=dict(record),
            )
        )
    return tuple(sorted(events, key=lambda event: event.effective_at))


def apply_split_adjustments(frame: pd.DataFrame, events: Sequence[SplitEvent]) -> pd.DataFrame:
    """Return split-adjusted OHLCV on the latest-share basis.

    For each event, pre-event prices are divided by new/old shares and volume is
    multiplied by the same factor. Dividends are deliberately not embedded here.
    """
    adjusted = canonicalize_ohlcv(frame)
    cumulative = pd.Series(1.0, index=adjusted.index, dtype=float)
    for event in sorted(events, key=lambda item: item.effective_at):
        mask = adjusted.index < event.effective_at
        cumulative.loc[mask] *= event.factor
    for column in PRICE_COLUMNS:
        adjusted[column] = adjusted[column].astype(float) / cumulative
    adjusted["volume"] = adjusted["volume"].astype(float) * cumulative
    if "vwap" in adjusted.columns:
        adjusted["vwap"] = adjusted["vwap"].astype(float) / cumulative
    validate_canonical(adjusted)
    return adjusted


def _metadata_path(parquet_path: Path) -> Path:
    return parquet_path.with_suffix(".metadata.json")


def write_canonical_parquet(
    frame: pd.DataFrame,
    path: str | Path,
    metadata: CanonicalMetadata,
    *,
    extra_metadata: Mapping[str, Any] | None = None,
) -> tuple[Path, Path]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    canonical = canonicalize_ohlcv(frame, drop_duplicate_timestamps=False, drop_missing_required=False)
    report = validate_canonical(canonical)
    with tempfile.NamedTemporaryFile(suffix=".parquet", dir=target.parent, delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        canonical.to_parquet(temp_path, index=True)
        temp_path.replace(target)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
    manifest = {
        **asdict(metadata),
        "rows": len(canonical),
        "start": canonical.index.min().isoformat() if len(canonical) else None,
        "end": canonical.index.max().isoformat() if len(canonical) else None,
        "columns": list(canonical.columns),
        "sha256": sha256_file(target),
        "quality": report.to_dict(),
        "extra": dict(extra_metadata or {}),
    }
    meta_path = _metadata_path(target)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=meta_path.parent, delete=False) as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")
        tmp_meta = Path(handle.name)
    tmp_meta.replace(meta_path)
    return target, meta_path


def read_canonical_parquet(
    path: str | Path,
    *,
    verify_hash: bool = False,
    verify_metadata: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any] | None]:
    target = Path(path)
    frame = canonicalize_ohlcv(
        pd.read_parquet(target),
        drop_duplicate_timestamps=False,
        drop_missing_required=False,
    )
    validate_canonical(frame)
    meta_path = _metadata_path(target)
    metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else None
    if metadata:
        if str(metadata.get("schema_version")) != CANONICAL_SCHEMA_VERSION:
            raise ValueError(f"unsupported canonical schema in {meta_path}: {metadata.get('schema_version')}")
        if verify_metadata:
            expected_rows = metadata.get("rows")
            if expected_rows is not None and int(expected_rows) != len(frame):
                raise ValueError(f"metadata row count mismatch for {target}: {expected_rows} != {len(frame)}")
            expected_columns = metadata.get("columns")
            if expected_columns is not None and list(expected_columns) != list(frame.columns):
                raise ValueError(f"metadata columns mismatch for {target}")
            if len(frame):
                if metadata.get("start") and str(metadata["start"]) != frame.index.min().isoformat():
                    raise ValueError(f"metadata start mismatch for {target}")
                if metadata.get("end") and str(metadata["end"]) != frame.index.max().isoformat():
                    raise ValueError(f"metadata end mismatch for {target}")
            if metadata.get("timezone") and str(metadata["timezone"]) != "UTC":
                raise ValueError(f"metadata timezone must be UTC for {target}")
    if verify_hash and metadata and metadata.get("sha256"):
        actual = sha256_file(target)
        if actual != metadata["sha256"]:
            raise ValueError(f"parquet hash mismatch for {target}")
    return frame, metadata
