from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from stocks.training.pit_dataset_v2_24 import (
    audit_pit_training_frame_v224,
    build_purged_walk_forward_splits_v224,
    write_pit_training_splits_v224,
)


def _read(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    return pd.read_csv(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--decision-time-column", default="decision_time")
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--train-size", type=int, required=True)
    parser.add_argument("--validation-size", type=int, required=True)
    parser.add_argument("--test-size", type=int, required=True)
    parser.add_argument("--purge", type=int, required=True)
    parser.add_argument("--embargo", type=int, required=True)
    parser.add_argument("--step-size", type=int, default=None)
    args = parser.parse_args()

    dataset_path = Path(args.dataset).resolve()
    frame = _read(dataset_path)
    audit = audit_pit_training_frame_v224(
        frame,
        decision_time=args.decision_time_column,
        label_columns=tuple(args.target),
    )
    if not audit["valid"]:
        raise ValueError("PIT dataset audit failed: " + "|".join(audit["errors"]))
    splits = build_purged_walk_forward_splits_v224(
        len(frame),
        train_size=args.train_size,
        validation_size=args.validation_size,
        test_size=args.test_size,
        purge=args.purge,
        embargo=args.embargo,
        step_size=args.step_size,
    )
    output = write_pit_training_splits_v224(
        frame,
        splits,
        args.output,
        metadata={
            "source_dataset": str(dataset_path),
            "decision_time_column": args.decision_time_column,
            "target_columns": list(args.target),
        },
        label_columns=tuple(args.target),
    )
    print("PIT_TRAINING_SPLITS_V2_24 READY True")
    print("ROWS", len(frame))
    print("FOLDS", len(splits))
    print("DATASET_SHA256", audit["dataset_sha256"])
    print("PREPROCESSING_FIT_SCOPE TRAIN_ONLY")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
