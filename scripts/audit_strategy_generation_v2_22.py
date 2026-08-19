#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_ROOT = ROOT / "artifacts/research_runtime/strategy_generation_v2_22"
MANIFEST_ARTIFACTS = (
    "blueprints.csv",
    "hypotheses.csv",
    "fold_candidates.csv",
    "fold_selected.csv",
    "all_hypotheses_summary.csv",
    "rejection_diagnostics.csv",
    "survivors.csv",
    "validation_queue.csv",
    "redundancy.csv",
    "queue_decisions.csv",
    "survivor_trades.parquet",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "artifact_root",
        nargs="?",
        default=str(DEFAULT_ARTIFACT_ROOT),
    )
    args = parser.parse_args()
    artifact_root = Path(args.artifact_root).resolve()
    config = yaml.safe_load(
        (ROOT / "config/strategy_generation_v2_22.yaml").read_text(encoding="utf-8")
    )

    required = (
        "blueprints.csv",
        "hypotheses.csv",
        "fold_candidates.csv",
        "fold_selected.csv",
        "all_hypotheses_summary.csv",
        "rejection_diagnostics.csv",
        "survivors.csv",
        "validation_queue.csv",
        "redundancy.csv",
        "queue_decisions.csv",
        "survivor_trades.parquet",
        "manifest.json",
        "audit.json",
    )
    missing = [name for name in required if not (artifact_root / name).is_file()]
    errors: list[str] = []
    if missing:
        errors.append("MISSING_ARTIFACTS:" + ",".join(missing))

    audit: dict = {}
    manifest: dict = {}
    if not missing:
        audit = json.loads((artifact_root / "audit.json").read_text())
        manifest = json.loads((artifact_root / "manifest.json").read_text())
        if audit.get("schema") != "strategy_generation_v2_22":
            errors.append("INVALID_AUDIT_SCHEMA")
        if bool(audit.get("automatic_finalist_promotion")):
            errors.append("AUTOMATIC_FINALIST_PROMOTION_ENABLED")
        if bool(audit.get("automatic_live_promotion")):
            errors.append("AUTOMATIC_LIVE_PROMOTION_ENABLED")
        if int(audit.get("broker_calls", -1)) != 0:
            errors.append("BROKER_CALLS_NONZERO")
        if int(audit.get("order_calls", -1)) != 0:
            errors.append("ORDER_CALLS_NONZERO")
        if str(audit.get("execution_authority")) != "NONE":
            errors.append("EXECUTION_AUTHORITY_NOT_NONE")

        manifest_names = set(manifest)
        expected_manifest_names = set(MANIFEST_ARTIFACTS)
        for name in sorted(expected_manifest_names - manifest_names):
            errors.append(f"MANIFEST_ENTRY_MISSING:{name}")
        for name in sorted(manifest_names - expected_manifest_names):
            errors.append(f"UNEXPECTED_MANIFEST_ENTRY:{name}")
        for name, metadata in manifest.items():
            path = artifact_root / name
            if not path.is_file():
                errors.append(f"MANIFEST_FILE_MISSING:{name}")
                continue
            if _sha256(path) != str(metadata.get("sha256")):
                errors.append(f"HASH_MISMATCH:{name}")
            if path.stat().st_size != int(metadata.get("bytes", -1)):
                errors.append(f"SIZE_MISMATCH:{name}")

    queue = _read_csv(artifact_root / "validation_queue.csv")
    survivors = _read_csv(artifact_root / "survivors.csv")
    hypotheses = _read_csv(artifact_root / "hypotheses.csv")
    diagnostics = _read_csv(artifact_root / "rejection_diagnostics.csv")
    trades = (
        pd.read_parquet(artifact_root / "survivor_trades.parquet")
        if (artifact_root / "survivor_trades.parquet").is_file()
        else pd.DataFrame()
    )

    for name, frame in (
        ("hypotheses", hypotheses),
        ("survivors", survivors),
        ("validation_queue", queue),
        ("rejection_diagnostics", diagnostics),
    ):
        if frame.empty:
            continue
        if "hypothesis_id" not in frame:
            errors.append(f"HYPOTHESIS_ID_MISSING:{name}")
            continue
        if frame["hypothesis_id"].astype(str).duplicated().any():
            errors.append(f"DUPLICATE_HYPOTHESIS_ID:{name}")

    survivor_ids = (
        set(survivors["hypothesis_id"].astype(str))
        if "hypothesis_id" in survivors
        else set()
    )
    queue_ids = (
        set(queue["hypothesis_id"].astype(str)) if "hypothesis_id" in queue else set()
    )
    trade_ids = (
        set(trades["hypothesis_id"].astype(str)) if "hypothesis_id" in trades else set()
    )
    if not queue_ids.issubset(survivor_ids):
        errors.append("QUEUE_NOT_SUBSET_OF_SURVIVORS")
    if survivor_ids != trade_ids:
        errors.append("SURVIVOR_TRADE_COVERAGE_MISMATCH")
    hypothesis_ids = (
        set(hypotheses["hypothesis_id"].astype(str))
        if "hypothesis_id" in hypotheses
        else set()
    )
    diagnostic_ids = (
        set(diagnostics["hypothesis_id"].astype(str))
        if "hypothesis_id" in diagnostics
        else set()
    )
    if diagnostic_ids != hypothesis_ids - survivor_ids:
        errors.append("REJECTION_DIAGNOSTIC_COVERAGE_MISMATCH")
    if not diagnostics.empty and not {
        "blockers",
        "blocker_count",
    }.issubset(diagnostics.columns):
        errors.append("REJECTION_DIAGNOSTIC_COLUMNS_MISSING")
    if audit:
        expected_counts = {
            "hypotheses": len(hypotheses),
            "survivors": len(survivors),
            "validation_queue": len(queue),
            "survivor_trade_rows": len(trades),
            "rejected_hypotheses": len(diagnostics),
        }
        for name, expected in expected_counts.items():
            if int(audit.get(name, -1)) != expected:
                errors.append(f"AUDIT_COUNT_MISMATCH:{name}")
        if audit.get("failed_hypotheses"):
            errors.append("FAILED_HYPOTHESES_PRESENT")
    if not queue.empty:
        if set(queue.get("execution_authority", pd.Series(dtype=str))) != {"NONE"}:
            errors.append("QUEUE_EXECUTION_AUTHORITY_NOT_NONE")
        if bool(
            queue.get("automatic_finalist_promotion", pd.Series(dtype=bool))
            .fillna(False)
            .astype(bool)
            .any()
        ):
            errors.append("QUEUE_AUTOMATIC_PROMOTION_ENABLED")
        maximum_total = int(config["diversity"]["maximum_validation_queue"])
        maximum_per_family = int(config["diversity"]["maximum_per_family"])
        if len(queue) > maximum_total:
            errors.append("QUEUE_TOTAL_CAP_EXCEEDED")
        if "family" not in queue:
            errors.append("QUEUE_FAMILY_MISSING")
        elif int(queue.groupby("family").size().max()) > maximum_per_family:
            errors.append("QUEUE_FAMILY_CAP_EXCEEDED")

    valid = not errors
    print("=" * 100)
    print("STRATEGY_GENERATION_AUDIT_V2_22", "VALID", valid)
    print("HYPOTHESES", len(hypotheses))
    print("SURVIVORS", len(survivors))
    print("VALIDATION_QUEUE", len(queue))
    print("REJECTION_DIAGNOSTICS", len(diagnostics))
    print("QUEUE_FAMILIES", int(queue["family"].nunique()) if not queue.empty else 0)
    print("ERRORS", "NONE" if not errors else "|".join(errors))
    print("AUTOMATIC_FINALIST_PROMOTION", False)
    print("AUTOMATIC_LIVE_PROMOTION", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    print("ARTIFACT_ROOT", artifact_root)
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
