from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from stocks.rl.checkpoint_v2_21 import sha256_path_v221
from stocks.rl.contracts_v2_21 import DEPLOYMENT_MODE, EXECUTION_AUTHORITY
from stocks.rl.dataset_v2_21 import load_portfolio_dataset_v221
from stocks.rl.pipeline_v2_21 import (
    RLMARLPipelineConfigV221,
    _atomic_json,
    _atomic_text,
    _canonical_hash,
    _git_commit,
    _promotion_summary,
    _train_trial,
)
from stocks.rl.pit_shariah_dataset_v2_25 import apply_pit_shariah_mask_v225
from stocks.rl.research_automation_v2_21 import RLTrialSpecV221, run_trial_matrix_v221
from stocks.rl.validation_v2_21 import build_walk_forward_plan_v221


def run_pit_shariah_rl_marl_pipeline_v225(
    pipeline: RLMARLPipelineConfigV221,
    *,
    shariah_ledger: pd.DataFrame,
    smoke: bool = False,
    maximum_folds: int | None = None,
    algorithms: Sequence[str] | None = None,
    seeds: Sequence[int] | None = None,
    verify_reproducibility: bool = False,
    project_root: str | Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Run the existing MAPPO/MATD3 research trainer on a PIT Shariah mask.

    This reuses v2.21's training/evaluation/promotion machinery; only the
    dataset episode is replaced with a mask that can narrow, never widen, the
    original tradable universe based on historical Shariah evidence available
    at each observation timestamp.
    """
    root = Path(project_root or Path.cwd()).resolve()
    selected_algorithms = tuple(
        str(value).upper() for value in (algorithms or pipeline.algorithms)
    )
    selected_seeds = tuple(int(value) for value in (seeds or pipeline.seeds))
    if smoke:
        selected_algorithms = selected_algorithms[:1]
        selected_seeds = selected_seeds[:1]
        maximum_folds = 1 if maximum_folds is None else maximum_folds
    if not smoke and len(selected_seeds) != 10:
        raise ValueError("non-smoke pipeline runs require exactly ten seeds")
    if any(value not in pipeline.algorithms for value in selected_algorithms):
        raise ValueError("requested algorithm is not enabled by config")

    base = load_portfolio_dataset_v221(
        pipeline.data_root,
        symbols=pipeline.symbols,
        timeframe=pipeline.timeframe,
        benchmark_symbol=pipeline.benchmark_symbol,
        verify_hash=pipeline.verify_source_hashes,
    )
    dataset, shariah_audit = apply_pit_shariah_mask_v225(base, shariah_ledger)
    folds = build_walk_forward_plan_v221(
        dataset.episode.steps,
        train_size=pipeline.train_size,
        validation_size=pipeline.validation_size,
        test_size=pipeline.test_size,
        purge=pipeline.purge,
        embargo=pipeline.embargo,
    )
    if maximum_folds is not None:
        if maximum_folds < 1:
            raise ValueError("maximum_folds must be positive")
        folds = folds[:maximum_folds]
    if not folds:
        raise ValueError("no walk-forward folds available")

    run_root = (
        pipeline.output_root
        / "pit_shariah_v2_25"
        / f"{pipeline.config_hash[:12]}-{dataset.dataset_hash[:12]}"
    )
    run_root.mkdir(parents=True, exist_ok=True)
    code_commit = _git_commit(root)
    trials = tuple(
        RLTrialSpecV221(algorithm=algorithm, seed=seed, fold=fold)
        for algorithm in selected_algorithms
        for fold in range(len(folds))
        for seed in selected_seeds
    )

    def evaluator(trial: RLTrialSpecV221) -> Mapping[str, Any]:
        primary = _train_trial(
            trial,
            split=folds[trial.fold],
            full_episode=dataset.episode,
            pipeline=pipeline,
            dataset_hash=dataset.dataset_hash,
            code_commit=code_commit,
            run_root=run_root,
        )
        if not verify_reproducibility:
            return primary
        repeated = _train_trial(
            trial,
            split=folds[trial.fold],
            full_episode=dataset.episode,
            pipeline=pipeline,
            dataset_hash=dataset.dataset_hash,
            code_commit=code_commit,
            run_root=run_root / "reproducibility",
        )
        comparable = (
            "strategy_return",
            "baseline_return",
            "cost_stress_return",
            "severe_stress_return",
            "maximum_drawdown",
            "maximum_concentration",
            "constraint_violations",
            "checkpoint_tensor_sha256",
        )
        primary["reproducible"] = all(primary[key] == repeated[key] for key in comparable)
        primary["reproducibility_hash"] = _canonical_hash(
            {key: repeated[key] for key in comparable}
        )
        return primary

    results, seed_ledger = run_trial_matrix_v221(
        trials,
        evaluator,
        config_hash=pipeline.config_hash,
    )
    trial_path = run_root / "trials.jsonl"
    seed_ledger_path = run_root / "ledger.jsonl"
    config_path = run_root / "config.snapshot.json"
    dataset_path = run_root / "dataset.manifest.json"
    _atomic_text(
        trial_path,
        "".join(
            json.dumps(
                row,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
                default=str,
            ) + "\n"
            for row in results
        ),
    )
    _atomic_text(seed_ledger_path, seed_ledger.to_jsonl())
    _atomic_json(config_path, pipeline.to_dict())
    dataset_manifest = {
        **dataset.manifest(),
        "schema": "pit_shariah_rl_dataset_v2_25",
        "pit_shariah": shariah_audit,
    }
    _atomic_json(dataset_path, dataset_manifest)
    decisions = _promotion_summary(
        results,
        pipeline,
        dataset_hash=dataset.dataset_hash,
        code_commit=code_commit,
        smoke=smoke,
        algorithms=selected_algorithms,
    )
    summary = {
        "schema_version": "v2.21.1",
        "extension_schema": "pit_shariah_rl_pipeline_v2_25",
        "status": "PIPELINE_COMPLETE",
        "smoke": smoke,
        "algorithms": list(selected_algorithms),
        "seeds": list(selected_seeds),
        "folds": len(folds),
        "trials": len(results),
        "reproducibility_verified": bool(verify_reproducibility),
        "dataset_hash": dataset.dataset_hash,
        "base_dataset_hash": base.dataset_hash,
        "pit_shariah_ledger_sha256": shariah_audit["pit_shariah_ledger_sha256"],
        "pit_shariah_mask_applied": True,
        "unknown_shariah_is_ineligible": True,
        "config_hash": pipeline.config_hash,
        "code_commit": code_commit,
        "promotion": decisions,
        "artifacts": {
            "trials.jsonl": sha256_path_v221(trial_path),
            "ledger.jsonl": sha256_path_v221(seed_ledger_path),
            "config.snapshot.json": sha256_path_v221(config_path),
            "dataset.manifest.json": sha256_path_v221(dataset_path),
        },
        "deployment_mode": DEPLOYMENT_MODE,
        "automatic_live_promotion": False,
        "execution_authority": EXECUTION_AUTHORITY,
        "broker_calls": 0,
        "order_calls": 0,
    }
    _atomic_json(run_root / "summary.json", summary)
    return run_root, shariah_audit


__all__ = ["run_pit_shariah_rl_marl_pipeline_v225"]
