from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .agent_runtime_v2_40 import train_agent_v240
from .config_v2_40 import agent_specs_v240, resolve_runtime_paths_v240
from .contracts_v2_40 import AgentStateV240
from .mappo_trainer_v2_40 import train_mappo_file_v240
from .research_bridge_v2_40 import maximum_drift_severity_v240, register_rl_training_evidence_v240, shadow_outcome_count_v240
from .state_store_v2_40 import LearningStoreV240, utc_now
from .subprocess_runner_v2_40 import run_allowlisted_component_v240
from .triggers_v2_40 import decide_retrain_v240


def _data_rows(path: Path) -> tuple[int, str | None]:
    if not path.is_file():
        return 0, None
    try:
        import pyarrow.parquet as pq
        return int(pq.ParquetFile(path).metadata.num_rows), None
    except Exception:
        frame = pd.read_parquet(path)
        latest = None
        if len(frame.index):
            value = frame.index[-1]
            latest = value.isoformat() if hasattr(value, "isoformat") else str(value)
        return len(frame), latest


def _run_component(root: Path, store: LearningStoreV240, cycle_id: int, name: str, args: list[str], timeout: int) -> dict:
    started = utc_now()
    try:
        result = run_allowlisted_component_v240(root, [str(root / ".venv/bin/python"), str(root / args[0]), *args[1:]], timeout=timeout)
        finished = utc_now()
        store.add_component_run(cycle_id, name, started_at=started, finished_at=finished, status=result.status, returncode=result.returncode, stdout=result.stdout_tail, stderr=result.stderr_tail)
        return result.as_dict()
    except Exception as exc:
        finished = utc_now()
        store.add_component_run(cycle_id, name, started_at=started, finished_at=finished, status="FAILED", returncode=99, stdout="", stderr=f"{type(exc).__name__}: {exc}")
        return {"component": name, "status": "FAILED", "returncode": 99, "error": f"{type(exc).__name__}: {exc}", "execution_authority": "NONE"}


def run_learning_cycle_v240(project_root: str | Path, config: dict, *, force_train: bool = False, force_strategy_refresh: bool = False) -> dict:
    root = Path(project_root).resolve()
    paths = resolve_runtime_paths_v240(root, config)
    paths["runtime_root"].mkdir(parents=True, exist_ok=True)
    paths["models"].mkdir(parents=True, exist_ok=True)
    paths["reports"].mkdir(parents=True, exist_ok=True)
    store = LearningStoreV240(paths["database"])
    specs = agent_specs_v240(config)
    for spec in specs:
        store.upsert_agent(spec)

    cycle_id = store.begin_cycle()
    cycle_index = int(store.cursor("cycle_index", 0))
    runtime_cfg = config.get("runtime") or {}
    strategy_cfg = config.get("strategy_runtime") or {}
    timeout = int(runtime_cfg.get("training_timeout_seconds", 7200))
    components = []
    trained = []
    skipped = []
    errors = []

    try:
        shadow_every = max(1, int(runtime_cfg.get("shadow_reconcile_every_cycles", 1)))
        if cycle_index % shadow_every == 0 and (root / strategy_cfg.get("shadow_lifecycle_script", "")).is_file():
            components.append(_run_component(root, store, cycle_id, "shadow_reconcile", [strategy_cfg["shadow_lifecycle_script"]], timeout))

        evidence_every = max(1, int(runtime_cfg.get("evidence_refresh_every_cycles", 4)))
        if cycle_index % evidence_every == 0 and (root / strategy_cfg.get("evidence_production_script", "")).is_file():
            components.append(_run_component(
                root, store, cycle_id, "evidence_production",
                [strategy_cfg["evidence_production_script"], "produce-due", "--max-entities", str(int(strategy_cfg.get("produce_due_max_entities", 5)))], timeout,
            ))

        research_every = max(1, int(runtime_cfg.get("research_reassess_every_cycles", 4)))
        if cycle_index % research_every == 0 and (root / strategy_cfg.get("continuous_research_script", "")).is_file():
            components.append(_run_component(
                root, store, cycle_id, "continuous_research",
                [strategy_cfg["continuous_research_script"], "cycle", "--max-jobs", str(int(strategy_cfg.get("research_max_jobs", 50)))], timeout,
            ))

        refresh_every = max(1, int(runtime_cfg.get("strategy_refresh_every_cycles", 96)))
        if (force_strategy_refresh or cycle_index % refresh_every == 0) and bool(strategy_cfg.get("run_discovery", True)) and (root / strategy_cfg.get("parallel_research_script", "")).is_file():
            components.append(_run_component(root, store, cycle_id, "strategy_discovery", [strategy_cfg["parallel_research_script"]], timeout))

        drift = maximum_drift_severity_v240(root)
        learning = config.get("learning") or {}
        max_jobs = max(0, int(runtime_cfg.get("max_training_jobs_per_cycle", 2)))
        jobs_used = 0
        for spec in specs:
            if not spec.enabled:
                skipped.append({"agent_id": spec.agent_id, "reason": "DISABLED"})
                continue
            state = store.agent(spec.agent_id) or {}
            data_path = Path(spec.data_path)
            if not data_path.is_absolute():
                data_path = root / data_path
            rows, latest = _data_rows(data_path)
            agent_shadow_count = shadow_outcome_count_v240(root, since=state.get("last_success_at"))
            decision = decide_retrain_v240(
                current_rows=rows,
                previous_rows=int(state.get("last_data_rows") or 0),
                last_success_at=state.get("last_success_at"),
                last_attempt_at=state.get("last_train_at"),
                shadow_outcomes_since_train=agent_shadow_count,
                drift_severity=drift,
                policy=learning,
                force=force_train,
            )
            if not decision.should_train:
                state_name = AgentStateV240.WAITING_DATA.value if "INSUFFICIENT_DATA_ROWS" in decision.blockers else AgentStateV240.IDLE.value
                store.set_agent_state(spec.agent_id, state_name)
                skipped.append({"agent_id": spec.agent_id, "decision": decision.as_dict(), "data_rows": rows, "latest_data_time": latest})
                continue
            if jobs_used >= max_jobs:
                skipped.append({"agent_id": spec.agent_id, "reason": "CYCLE_TRAINING_CAP", "decision": decision.as_dict()})
                continue
            jobs_used += 1
            run_id = store.begin_training(spec.agent_id, decision.as_dict())
            try:
                result = train_agent_v240(root, spec, config).as_dict()
                store.finish_training(run_id, spec.agent_id, status="SUCCEEDED", result=result)
                register_rl_training_evidence_v240(root, result)
                trained.append(result)
            except Exception as exc:
                msg = f"{type(exc).__name__}: {exc}"
                store.finish_training(run_id, spec.agent_id, status="FAILED", error=msg)
                errors.append({"agent_id": spec.agent_id, "error": msg})
                if not bool(runtime_cfg.get("continue_on_component_failure", True)):
                    raise

        mappo_cfg = config.get("mappo") or {}
        if mappo_cfg.get("enabled"):
            dataset = Path(mappo_cfg.get("dataset_path", ""))
            if not dataset.is_absolute():
                dataset = root / dataset
            if dataset.is_file():
                checkpoint = paths["models"] / "mappo_portfolio" / "current.pt"
                try:
                    mresult = train_mappo_file_v240(dataset, checkpoint, mappo_cfg)
                    trained.append({"agent_id": "mappo_portfolio", "algorithm": "MAPPO", "status": "SUCCEEDED", **mresult})
                except Exception as exc:
                    errors.append({"agent_id": "mappo_portfolio", "error": f"{type(exc).__name__}: {exc}"})
            else:
                skipped.append({"agent_id": "mappo_portfolio", "reason": "MAPPO_DATASET_NOT_READY", "dataset_path": str(dataset)})

        summary = {
            "cycle_id": cycle_id,
            "cycle_index": cycle_index,
            "components": components,
            "trained": trained,
            "skipped": skipped,
            "errors": errors,
            "shadow_outcomes_seen": shadow_outcome_count_v240(root),
            "maximum_drift_severity": drift,
            "automatic_champion_promotion": False,
            "automatic_live_promotion": False,
            "broker_submission_enabled": False,
            "order_calls": 0,
            "execution_authority": "NONE",
        }
        status = "SUCCEEDED" if not errors else "COMPLETED_WITH_ERRORS"
        store.finish_cycle(cycle_id, status=status, summary=summary)
        store.set_cursor("cycle_index", cycle_index + 1)
        report = paths["reports"] / "latest_cycle.json"
        report.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        return summary
    except Exception as exc:
        store.finish_cycle(cycle_id, status="FAILED", summary={"error": f"{type(exc).__name__}: {exc}", "execution_authority": "NONE"})
        raise


__all__ = ["run_learning_cycle_v240"]
