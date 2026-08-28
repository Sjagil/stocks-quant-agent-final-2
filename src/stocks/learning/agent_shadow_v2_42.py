from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stocks.learning.config_v2_40 import agent_specs_v240, load_learning_config_v240, resolve_runtime_paths_v240
from stocks.learning.dataset_v2_40 import load_dataset_v240
from stocks.learning.state_store_v2_40 import LearningStoreV240
from stocks.research.continuous.contracts_v2_39 import EntityV239, EvidenceRecordV239
from stocks.research.continuous.store_v2_39 import ResearchStoreV239
from stocks.learning.research_bridge_v2_40 import research_db_path_v240
from stocks.rl.config import load_rl_yaml


def _load_model(algorithm: str, path: Path):
    from stable_baselines3 import PPO, SAC
    cls = PPO if algorithm.upper() == "PPO" else SAC
    return cls.load(str(path))


def _latest_observation(features: pd.DataFrame, window_size: int) -> np.ndarray:
    if len(features) < int(window_size):
        raise ValueError("insufficient features for latest agent observation")
    window = features.tail(int(window_size)).to_numpy(dtype=np.float32).reshape(-1)
    state = np.asarray([0.0, 1.0, 0.0], dtype=np.float32)
    return np.concatenate([window, state]).astype(np.float32)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def _register_shadow(root: Path, agent_id: str, algorithm: str, as_of: str, metrics: dict[str, Any], source_ref: str) -> bool:
    db = research_db_path_v240(root)
    if not db.is_file():
        return False
    store = ResearchStoreV239(db)
    entity_id = f"RL:{agent_id}"
    if store.get_entity(entity_id) is None:
        store.upsert_entity(EntityV239(entity_id=entity_id, entity_type="RL_POLICY", family=algorithm, source="AGENT_SHADOW_V2_42"))
    return store.add_evidence(EvidenceRecordV239(
        entity_id=entity_id,
        evidence_type="SHADOW_TRADE",
        as_of=as_of,
        sample_count=1,
        metrics={**metrics, "passed": False, "status": "RL_SHADOW_OBSERVATION", "execution_authority": "NONE"},
        source="AGENT_SHADOW_V2_42",
        source_ref=source_ref,
    ))


def run_agent_shadow_v242(root: str | Path) -> dict[str, Any]:
    root = Path(root).resolve()
    cfg = load_learning_config_v240(root)
    paths = resolve_runtime_paths_v240(root, cfg)
    store = LearningStoreV240(paths["database"])
    reward_cfg, env_cfg, _, _ = load_rl_yaml(root / "config/rl.yaml")
    shadow_root = root / "artifacts/research_runtime/agent_shadow_v2_42"
    adv_path = shadow_root / "advisories.jsonl"
    outcome_path = shadow_root / "outcomes.jsonl"
    previous = _read_jsonl(adv_path)
    outcomes = _read_jsonl(outcome_path)
    outcome_refs = {str(x.get("source_ref")) for x in outcomes}
    generated = []
    realized = []

    for spec in agent_specs_v240(cfg):
        if not spec.enabled or spec.algorithm.upper() not in {"PPO", "SAC"}:
            continue
        data_path = Path(spec.data_path)
        if not data_path.is_absolute():
            data_path = root / data_path
        features, close = load_dataset_v240(data_path)
        latest_time = pd.Timestamp(features.index[-1])
        latest_close = float(close.iloc[-1])
        state = store.agent(spec.agent_id) or {}
        test = dict(state.get("latest_test") or {})
        test_trades = int(test.get("trades") or 0)
        quality = "DEGENERATE_ZERO_ACTIVITY" if test_trades == 0 else ("INSUFFICIENT_EVIDENCE" if test_trades < 30 else "SHADOW_ELIGIBLE")

        # Realize each prior advisory on its immediately following observed bar exactly once.
        prior_rows = [x for x in previous if x.get("agent_id") == spec.agent_id]
        for prior in prior_rows:
            source_ref = f"{spec.agent_id}:{prior.get('data_time')}"
            if source_ref in outcome_refs:
                continue
            prior_time = pd.Timestamp(prior["data_time"])
            later = close.index[close.index > prior_time]
            if len(later) == 0:
                continue
            next_time = later[0]
            p0 = float(prior["close"])
            p1 = float(close.loc[next_time])
            exposure = float(prior["target_exposure"])
            if exposure < float(env_cfg.min_trade_delta):
                # Zero-activity observations are not counted as shadow trades.
                continue
            asset_return = p1 / p0 - 1.0
            cost = exposure * (float(reward_cfg.transaction_cost_bps) + float(reward_cfg.slippage_bps)) / 10000.0
            net_return = exposure * asset_return - cost
            row = {
                "agent_id": spec.agent_id, "algorithm": spec.algorithm.upper(),
                "source_ref": source_ref, "signal_time": str(prior_time), "outcome_time": str(next_time),
                "target_exposure": exposure, "asset_return": asset_return, "net_return": net_return,
                "execution_authority": "NONE",
            }
            _append_jsonl(outcome_path, row)
            _register_shadow(root, spec.agent_id, spec.algorithm.upper(), str(next_time), row, source_ref)
            outcome_refs.add(source_ref)
            realized.append(row)

        model_path = Path(str(state.get("model_path") or ""))
        if not model_path.is_file():
            continue
        model = _load_model(spec.algorithm, model_path)
        obs = _latest_observation(features, int(env_cfg.window_size))
        action, _ = model.predict(obs, deterministic=True)
        target = float(np.asarray(action).reshape(-1)[0])
        target = float(np.clip(target, 0.0, float(env_cfg.max_position)))
        source_ref = f"{spec.agent_id}:{latest_time.isoformat()}"
        if not any(x.get("source_ref") == source_ref for x in previous):
            row = {
                "source_ref": source_ref,
                "agent_id": spec.agent_id, "algorithm": spec.algorithm.upper(), "symbol": spec.symbol,
                "data_time": latest_time.isoformat(), "close": latest_close,
                "target_exposure": target, "quality": quality, "test_trades": test_trades,
                "decision_influence": False, "execution_authority": "NONE",
            }
            _append_jsonl(adv_path, row)
            generated.append(row)

    latest_path = shadow_root / "latest.json"
    payload = {
        "schema": "agent_shadow_v2_42", "generated": generated, "realized": realized,
        "total_advisories": len(_read_jsonl(adv_path)), "total_outcomes": len(_read_jsonl(outcome_path)),
        "direct_broker_control": False, "execution_authority": "NONE",
    }
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    return payload
