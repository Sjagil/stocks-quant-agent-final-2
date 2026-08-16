from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from stocks.rl.config import EnvironmentConfig, RewardConfig
from stocks.rl.splits import purged_walk_forward_splits

from .environments import (
    ContinuousLongOnlySizingEnv,
    DiscreteLongOnlyTimingEnv,
    RiskReductionEnv,
)
from .evaluation import buy_hold_metrics, evaluate_agent
from .trainers import load_agent_model, train_agent


ALGORITHMS = ("DQN", "SAC", "MASKABLE_PPO")


def load_validation_config(
    path: str | Path,
) -> dict[str, Any]:
    payload = yaml.safe_load(
        Path(path).read_text(encoding="utf-8")
    ) or {}
    if str(payload.get("execution_authority", "NONE")).upper() != "NONE":
        raise ValueError("agent validation config may not grant execution authority")
    return payload


def _splits(
    n_rows: int,
    config: dict[str, Any],
):
    data_cfg = config["data"]
    minimum_rows = int(data_cfg["minimum_rows"])
    if n_rows < minimum_rows:
        raise ValueError(
            f"need at least {minimum_rows} rows, got {n_rows}"
        )

    train_size = int(n_rows * 0.50)
    validation_size = int(n_rows * 0.15)
    test_size = int(n_rows * 0.15)

    result = purged_walk_forward_splits(
        n_rows,
        train_size=train_size,
        validation_size=validation_size,
        test_size=test_size,
        purge=int(data_cfg["purge_bars"]),
        embargo=int(data_cfg["embargo_bars"]),
        step_size=test_size,
    )
    result = result[: int(data_cfg["max_folds"])]

    if len(result) < int(config["gates"]["minimum_folds"]):
        raise ValueError(
            f"not enough purged walk-forward folds: {len(result)}"
        )
    return result


def _environment(
    algorithm: str,
    frame: pd.DataFrame,
    reward: RewardConfig,
):
    algorithm = algorithm.upper()
    kwargs = dict(
        env_cfg=EnvironmentConfig(),
        reward_cfg=reward,
        random_start=False,
        episode_length=None,
    )
    if algorithm == "DQN":
        return DiscreteLongOnlyTimingEnv(frame, **kwargs)
    if algorithm == "SAC":
        return ContinuousLongOnlySizingEnv(frame, **kwargs)
    if algorithm == "MASKABLE_PPO":
        return RiskReductionEnv(frame, **kwargs)
    raise ValueError(algorithm)


def _median_validation_seed(
    seed_rows: list[dict],
) -> dict:
    ranked = sorted(
        seed_rows,
        key=lambda row: (
            float(row["validation"]["sharpe"]),
            int(row["seed"]),
        ),
    )
    return ranked[len(ranked) // 2]


def _deployment_seed(
    folds: list[dict],
    seeds: list[int],
) -> int:
    values: dict[int, list[float]] = defaultdict(list)
    for fold in folds:
        for row in fold["seeds"]:
            values[int(row["seed"])].append(
                float(row["validation"]["sharpe"])
            )

    ranked = sorted(
        (
            (
                statistics.mean(values[seed])
                if values[seed]
                else float("-inf"),
                int(seed),
            )
            for seed in seeds
        ),
        key=lambda item: (item[0], item[1]),
    )
    return ranked[len(ranked) // 2][1]


def _gate_summary(
    folds: list[dict],
    config: dict[str, Any],
) -> dict[str, Any]:
    gates = config["gates"]

    test_returns = [
        float(row["test"]["total_return"])
        for row in folds
    ]
    stress_returns = [
        float(row["stress_test"]["total_return"])
        for row in folds
    ]
    test_sharpes = [
        float(row["test"]["sharpe"])
        for row in folds
    ]
    drawdowns = [
        float(row["test"]["max_drawdown"])
        for row in folds
    ]
    trades = [
        int(row["test"]["trades"])
        for row in folds
    ]

    positive_test_ratio = sum(
        value > 0 for value in test_returns
    ) / len(test_returns)
    positive_stress_ratio = sum(
        value > 0 for value in stress_returns
    ) / len(stress_returns)

    benchmark_edge_ratio = sum(
        (
            float(row["test"]["total_return"])
            > float(row["buy_hold"]["total_return"])
        )
        or (
            float(row["test"]["sharpe"])
            > float(row["buy_hold"]["sharpe"])
        )
        for row in folds
    ) / len(folds)

    summary = {
        "folds": len(folds),
        "positive_test_fold_ratio": positive_test_ratio,
        "positive_stress_fold_ratio": positive_stress_ratio,
        "median_test_return": statistics.median(test_returns),
        "median_test_sharpe": statistics.median(test_sharpes),
        "worst_test_drawdown": max(drawdowns),
        "benchmark_edge_ratio": benchmark_edge_ratio,
        "median_test_trades": statistics.median(trades),
    }

    gate_results = {
        "fold_count_gate": (
            summary["folds"]
            >= int(gates["minimum_folds"])
        ),
        "positive_test_gate": (
            positive_test_ratio
            >= float(gates["minimum_positive_test_fold_ratio"])
        ),
        "stress_gate": (
            positive_stress_ratio
            >= float(gates["minimum_positive_stress_fold_ratio"])
        ),
        "return_gate": (
            summary["median_test_return"]
            > float(gates["minimum_median_test_return"])
        ),
        "sharpe_gate": (
            summary["median_test_sharpe"]
            > float(gates["minimum_median_test_sharpe"])
        ),
        "drawdown_gate": (
            summary["worst_test_drawdown"]
            <= float(gates["maximum_worst_test_drawdown"])
        ),
        "benchmark_gate": (
            benchmark_edge_ratio
            >= float(gates["minimum_benchmark_edge_ratio"])
        ),
        "trades_gate": (
            summary["median_test_trades"]
            >= int(gates["minimum_median_test_trades"])
        ),
    }
    summary["gates"] = gate_results
    summary["validated"] = all(gate_results.values())
    return summary


def validate_algorithm(
    frame: pd.DataFrame,
    *,
    symbol: str,
    timeframe: str,
    algorithm: str,
    project_root: str | Path,
    config: dict[str, Any],
    smoke: bool,
    deploy: bool,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    algorithm = algorithm.upper()
    seeds = [int(seed) for seed in config["training"]["seeds"]]
    split_rows = _splits(len(frame), config)

    timesteps_cfg = (
        config["training"]["smoke_timesteps"]
        if smoke
        else config["training"]["full_timesteps"]
    )
    timesteps = int(timesteps_cfg[algorithm])
    episode_length = int(config["training"]["episode_length"])

    base_reward = RewardConfig()
    stress_reward = replace(
        base_reward,
        transaction_cost_bps=float(
            config["stress"]["transaction_cost_bps"]
        ),
        slippage_bps=float(
            config["stress"]["slippage_bps"]
        ),
    )

    run_root = (
        root
        / "artifacts/research_runtime/"
        "agent_validation_v2_13"
        / symbol.upper()
        / timeframe
        / algorithm
    )
    run_root.mkdir(parents=True, exist_ok=True)

    fold_results: list[dict] = []

    for fold_number, split in enumerate(split_rows, start=1):
        train_frame = frame.iloc[
            split.train_start:split.train_end
        ].copy()
        validation_frame = frame.iloc[
            split.validation_start:split.validation_end
        ].copy()
        test_frame = frame.iloc[
            split.test_start:split.test_end
        ].copy()

        seed_rows: list[dict] = []

        for seed in seeds:
            output_dir = (
                run_root
                / f"fold_{fold_number:02d}"
                / f"seed_{seed}"
            )
            manifest = train_agent(
                algorithm,
                train_frame,
                output_dir=output_dir,
                timesteps=timesteps,
                seed=seed,
                training_mode=(
                    "SMOKE"
                    if smoke
                    else "VALIDATION_FOLD"
                ),
                episode_length=episode_length,
            )
            model = load_agent_model(
                algorithm,
                manifest["model_path"],
            )
            validation_env = _environment(
                algorithm,
                validation_frame,
                base_reward,
            )
            validation = evaluate_agent(
                model,
                validation_env,
            )
            seed_rows.append(
                {
                    "seed": seed,
                    "manifest": manifest["manifest"],
                    "model_path": manifest["model_path"],
                    "validation": validation.to_dict(),
                }
            )

        selected = _median_validation_seed(seed_rows)
        selected_model = load_agent_model(
            algorithm,
            selected["model_path"],
        )

        test_env = _environment(
            algorithm,
            test_frame,
            base_reward,
        )
        stress_env = _environment(
            algorithm,
            test_frame,
            stress_reward,
        )

        test_result = evaluate_agent(
            selected_model,
            test_env,
        )
        stress_result = evaluate_agent(
            selected_model,
            stress_env,
        )
        buy_hold = buy_hold_metrics(
            test_frame["close"],
            transaction_cost_bps=base_reward.transaction_cost_bps,
            slippage_bps=base_reward.slippage_bps,
        )

        fold_results.append(
            {
                "fold": fold_number,
                "split": asdict(split),
                "seeds": seed_rows,
                "selected_seed": int(selected["seed"]),
                "selection_policy": "MEDIAN_VALIDATION_SHARPE",
                "test_used_for_seed_selection": False,
                "test": test_result.to_dict(),
                "stress_test": stress_result.to_dict(),
                "buy_hold": buy_hold,
            }
        )

    summary = _gate_summary(fold_results, config)

    if smoke:
        registry_status = "SMOKE_EVALUATED"
    elif summary["validated"]:
        registry_status = "VALIDATED_AGENT_CHALLENGER"
    else:
        registry_status = "REJECTED"

    deployment_manifest = None
    if (
        not smoke
        and summary["validated"]
        and deploy
    ):
        deployment_seed = _deployment_seed(
            fold_results,
            seeds,
        )
        deployment_dir = (
            root
            / "artifacts/agent_models/v2_13"
            / symbol.upper()
            / timeframe
            / algorithm
            / "deployment"
        )
        deployment = train_agent(
            algorithm,
            frame,
            output_dir=deployment_dir,
            timesteps=int(
                config["training"]["full_timesteps"][algorithm]
            ),
            seed=deployment_seed,
            training_mode="DEPLOYMENT",
            episode_length=episode_length,
        )
        deployment["validated_by"] = (
            "PURGED_WALK_FORWARD_V2_13"
        )
        deployment["validation_summary"] = summary
        Path(deployment["manifest"]).write_text(
            json.dumps(
                deployment,
                indent=2,
                sort_keys=True,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
        deployment_manifest = deployment["manifest"]

    payload = {
        "schema": "agent_validation_v2_13",
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "algorithm": algorithm,
        "smoke": bool(smoke),
        "timesteps_per_seed_fold": timesteps,
        "folds": fold_results,
        "summary": summary,
        "registry_status": registry_status,
        "deployment_manifest": deployment_manifest,
        "money_control": False,
        "execution_authority": "NONE",
    }

    artifact = run_root / "validation.json"
    artifact.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    payload["artifact"] = str(artifact)
    return payload


def upsert_registry(
    project_root: str | Path,
    results: list[dict[str, Any]],
) -> Path:
    root = Path(project_root).resolve()
    output_dir = (
        root
        / "artifacts/research_runtime/"
        "agent_validation_v2_13"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "registry.csv"

    rows = []
    if path.is_file():
        rows.extend(
            pd.read_csv(path).to_dict(orient="records")
        )

    replacements = {
        (
            result["symbol"],
            result["timeframe"],
            result["algorithm"],
        )
        for result in results
    }
    rows = [
        row
        for row in rows
        if (
            str(row.get("symbol")),
            str(row.get("timeframe")),
            str(row.get("algorithm")),
        )
        not in replacements
    ]

    for result in results:
        summary = result["summary"]
        rows.append(
            {
                "symbol": result["symbol"],
                "timeframe": result["timeframe"],
                "algorithm": result["algorithm"],
                "registry_status": result["registry_status"],
                "smoke": result["smoke"],
                "folds": summary["folds"],
                "positive_test_fold_ratio": summary[
                    "positive_test_fold_ratio"
                ],
                "positive_stress_fold_ratio": summary[
                    "positive_stress_fold_ratio"
                ],
                "median_test_return": summary[
                    "median_test_return"
                ],
                "median_test_sharpe": summary[
                    "median_test_sharpe"
                ],
                "worst_test_drawdown": summary[
                    "worst_test_drawdown"
                ],
                "benchmark_edge_ratio": summary[
                    "benchmark_edge_ratio"
                ],
                "median_test_trades": summary[
                    "median_test_trades"
                ],
                "deployment_manifest": (
                    result["deployment_manifest"] or ""
                ),
                "execution_authority": "NONE",
            }
        )

    pd.DataFrame(rows).sort_values(
        ["symbol", "timeframe", "algorithm"]
    ).to_csv(path, index=False)
    return path
