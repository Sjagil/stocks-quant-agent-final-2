from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stocks.rl.config import EnvironmentConfig

from .candle_fabric import frame_for_timeframe
from .contracts import AgentVote
from .ensemble import fuse_agent_votes
from .environments import latest_market_observation
from .nlp_context import read_nlp_context


def _latest_manifest(
    root: Path,
    symbol: str,
    timeframe: str,
    algorithm: str,
) -> Path | None:
    directory = (
        root
        / "artifacts/agent_models/v2_12"
        / symbol.upper()
        / timeframe
        / algorithm.upper()
    )
    manifests = sorted(directory.glob("seed_*/manifest.json"))
    return manifests[-1] if manifests else None


def _load_manifest(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _predict_dqn(
    manifest: dict[str, Any] | None,
    observation: np.ndarray,
    symbol: str,
) -> AgentVote:
    if not manifest:
        return AgentVote(
            agent="DQN_TIMING",
            role="ENTRY_EXIT_TIMING",
            symbol=symbol,
            action="HOLD",
            available=False,
            reason="DQN_MODEL_NOT_TRAINED",
        )

    try:
        from stable_baselines3 import DQN

        model = DQN.load(manifest["model_path"])
        action, _ = model.predict(observation, deterministic=True)
        mapping = {
            0: "HOLD",
            1: "ENTER_LONG",
            2: "EXIT_TO_CASH",
        }
        text = mapping[int(np.asarray(action).reshape(-1)[0])]
        return AgentVote(
            agent="DQN_TIMING",
            role="ENTRY_EXIT_TIMING",
            symbol=symbol,
            action=text,
            confidence=0.50,
            model_id=manifest["model_path"],
        )
    except Exception as exc:
        return AgentVote(
            agent="DQN_TIMING",
            role="ENTRY_EXIT_TIMING",
            symbol=symbol,
            action="HOLD",
            available=False,
            reason=f"{type(exc).__name__}:{exc}",
        )


def _predict_sac(
    manifest: dict[str, Any] | None,
    observation: np.ndarray,
    symbol: str,
    current_exposure: float,
) -> AgentVote:
    if not manifest:
        return AgentVote(
            agent="SAC_SIZING",
            role="CONTINUOUS_TARGET_EXPOSURE",
            symbol=symbol,
            action="KEEP_CURRENT",
            target_exposure=float(current_exposure),
            available=False,
            reason="SAC_MODEL_NOT_TRAINED",
        )

    try:
        from stable_baselines3 import SAC

        model = SAC.load(manifest["model_path"])
        action, _ = model.predict(observation, deterministic=True)
        target = float(
            np.clip(np.asarray(action).reshape(-1)[0], 0.0, 1.0)
        )
        return AgentVote(
            agent="SAC_SIZING",
            role="CONTINUOUS_TARGET_EXPOSURE",
            symbol=symbol,
            action="TARGET_EXPOSURE",
            target_exposure=target,
            confidence=0.50,
            model_id=manifest["model_path"],
        )
    except Exception as exc:
        return AgentVote(
            agent="SAC_SIZING",
            role="CONTINUOUS_TARGET_EXPOSURE",
            symbol=symbol,
            action="KEEP_CURRENT",
            target_exposure=float(current_exposure),
            available=False,
            reason=f"{type(exc).__name__}:{exc}",
        )


def _predict_risk(
    manifest: dict[str, Any] | None,
    observation: np.ndarray,
    symbol: str,
    current_exposure: float,
) -> AgentVote:
    if current_exposure <= 1e-12:
        return AgentVote(
            agent="MASKABLE_PPO_RISK",
            role="POSITION_RISK_REDUCTION",
            symbol=symbol,
            action="KEEP",
            confidence=1.0,
            available=True,
            reason="NO_EXISTING_POSITION_TO_REDUCE",
        )

    if not manifest:
        return AgentVote(
            agent="MASKABLE_PPO_RISK",
            role="POSITION_RISK_REDUCTION",
            symbol=symbol,
            action="KEEP",
            available=False,
            reason="RISK_MODEL_NOT_TRAINED",
        )

    try:
        from sb3_contrib import MaskablePPO

        model = MaskablePPO.load(manifest["model_path"])
        action, _ = model.predict(observation, deterministic=True)
        mapping = {
            0: "KEEP",
            1: "CUT_25",
            2: "CUT_50",
            3: "FLAT",
        }
        text = mapping[int(np.asarray(action).reshape(-1)[0])]
        return AgentVote(
            agent="MASKABLE_PPO_RISK",
            role="POSITION_RISK_REDUCTION",
            symbol=symbol,
            action=text,
            confidence=0.50,
            model_id=manifest["model_path"],
        )
    except Exception as exc:
        return AgentVote(
            agent="MASKABLE_PPO_RISK",
            role="POSITION_RISK_REDUCTION",
            symbol=symbol,
            action="KEEP",
            available=False,
            reason=f"{type(exc).__name__}:{exc}",
        )


def _broker_state(root: Path) -> tuple[bool, dict[str, float]]:
    path = (
        root
        / "artifacts/research_runtime/"
        "ibkr_readonly_v2_9/snapshot.json"
    )
    if not path.is_file():
        return False, {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    economic = payload.get("economic_account_state") or {}
    ready = bool(
        payload.get("double_snapshot_stable")
        and economic.get("execution_status") == "EXECUTION_ACCOUNT_READY"
        and int(payload.get("broker_write_calls", 0)) == 0
    )

    positions: dict[str, float] = {}
    for row in (
        ((payload.get("snapshot") or {}).get("positions") or {})
        .get("positions", [])
    ):
        symbol = str(row.get("symbol") or "").upper()
        try:
            quantity = float(row.get("position_quantity") or 0.0)
        except (TypeError, ValueError):
            quantity = 0.0
        if symbol:
            positions[symbol] = quantity

    return ready, positions


def _shariah_map(root: Path) -> dict[str, bool]:
    path = (
        root
        / "artifacts/research_runtime/"
        "shariah_financial_verification/verification.csv"
    )
    if not path.is_file():
        return {}
    frame = pd.read_csv(path)
    return {
        str(row["symbol"]).upper(): bool(row.get("trade_eligible", False))
        for row in frame.to_dict(orient="records")
    }


def _broadly_validated_hypotheses(root: Path) -> set[str]:
    path = (
        root
        / "artifacts/research_runtime/"
        "final_strategy_roster/roster.csv"
    )
    if not path.is_file():
        return set()

    frame = pd.read_csv(path)
    if frame.empty or "hypothesis_id" not in frame.columns:
        return set()

    if "roster_status" not in frame.columns:
        return set()

    selected = frame.loc[
        frame["roster_status"].astype(str)
        == "BROADLY_VALIDATED_FINALIST"
    ]
    return set(selected["hypothesis_id"].astype(str))


def build_agent_shadow_decisions(
    project_root: str | Path,
    *,
    timeframe: str = "1h",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()
    forward_path = (
        root
        / "artifacts/research_runtime/"
        "forward_signal_state/signals.csv"
    )
    if not forward_path.is_file():
        return pd.DataFrame(), {
            "schema": "agent_shadow_pipeline_v2_12",
            "rows": 0,
            "reason": "FORWARD_SIGNAL_STATE_MISSING",
            "execution_authority": "NONE",
        }

    forward = pd.read_csv(forward_path)
    broker_ready, positions = _broker_state(root)
    shariah = _shariah_map(root)
    validated_hypotheses = _broadly_validated_hypotheses(root)

    rows: list[dict[str, Any]] = []
    env_cfg = EnvironmentConfig()

    for row in forward.to_dict(orient="records"):
        symbol = str(row["symbol"]).upper()

        try:
            frame = frame_for_timeframe(root, symbol, timeframe)
            current_quantity = float(positions.get(symbol, 0.0))
            current_exposure = 1.0 if current_quantity > 0 else 0.0
            observation = latest_market_observation(
                frame,
                window_size=env_cfg.window_size,
                position=current_exposure,
                drawdown=0.0,
            )
            candle_ready = True
            candle_error = None
        except Exception as exc:
            candle_ready = False
            candle_error = f"{type(exc).__name__}:{exc}"
            current_exposure = 0.0
            observation = None

        dqn_manifest = _load_manifest(
            _latest_manifest(root, symbol, timeframe, "DQN")
        )
        sac_manifest = _load_manifest(
            _latest_manifest(root, symbol, timeframe, "SAC")
        )
        risk_manifest = _load_manifest(
            _latest_manifest(root, symbol, timeframe, "MASKABLE_PPO")
        )

        if observation is not None:
            timing_vote = _predict_dqn(
                dqn_manifest,
                observation,
                symbol,
            )
            sizing_vote = _predict_sac(
                sac_manifest,
                observation,
                symbol,
                current_exposure,
            )
            risk_vote = _predict_risk(
                risk_manifest,
                observation,
                symbol,
                current_exposure,
            )
        else:
            timing_vote = AgentVote(
                agent="DQN_TIMING",
                role="ENTRY_EXIT_TIMING",
                symbol=symbol,
                action="HOLD",
                available=False,
                reason=candle_error,
            )
            sizing_vote = AgentVote(
                agent="SAC_SIZING",
                role="CONTINUOUS_TARGET_EXPOSURE",
                symbol=symbol,
                action="KEEP_CURRENT",
                target_exposure=current_exposure,
                available=False,
                reason=candle_error,
            )
            risk_vote = AgentVote(
                agent="MASKABLE_PPO_RISK",
                role="POSITION_RISK_REDUCTION",
                symbol=symbol,
                action="KEEP",
                available=False,
                reason=candle_error,
            )

        nlp = read_nlp_context(root, symbol)
        nlp_vote = AgentVote(
            agent="NLP_CONTEXT",
            role="NEWS_CONTEXT_MODIFIER",
            symbol=symbol,
            action="MODIFY_CONVICTION_ONLY",
            confidence=nlp.confidence,
            modifier=nlp.modifier,
            available=True,
            reason=nlp.source,
        )

        fresh = bool(row.get("new_entry_ready", False))
        hypothesis_id = str(row.get("hypothesis_id") or "")
        validated_strategy = (
            hypothesis_id in validated_hypotheses
        )

        envelope = fuse_agent_votes(
            symbol=symbol,
            fresh_validated_entry=fresh,
            shariah_verified=bool(shariah.get(symbol, False)),
            broker_account_ready=broker_ready,
            validated_strategy=validated_strategy,
            current_exposure=current_exposure,
            timing_vote=timing_vote,
            sizing_vote=sizing_vote,
            risk_vote=risk_vote,
            nlp_vote=nlp_vote,
        )

        rows.append(
            {
                "symbol": symbol,
                "strategy": row.get("strategy"),
                "hypothesis_id": hypothesis_id,
                "validated_strategy": validated_strategy,
                "timeframe": timeframe,
                "candle_ready": candle_ready,
                "broker_account_ready": broker_ready,
                "shariah_verified": bool(shariah.get(symbol, False)),
                "fresh_validated_entry": fresh,
                "current_exposure": current_exposure,
                "dqn_action": timing_vote.action,
                "dqn_available": timing_vote.available,
                "sac_target_exposure": envelope.sac_target_exposure,
                "sac_available": sizing_vote.available,
                "risk_action": risk_vote.action,
                "risk_available": risk_vote.available,
                "nlp_sentiment": nlp.sentiment,
                "nlp_confidence": nlp.confidence,
                "nlp_modifier": nlp.modifier,
                "shadow_target_exposure": envelope.shadow_target_exposure,
                "hard_gates_pass": envelope.hard_gates_pass,
                "blockers": "|".join(envelope.blockers),
                "money_control": False,
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": "NONE",
            }
        )

    frame = pd.DataFrame(rows)
    audit = {
        "schema": "agent_shadow_pipeline_v2_12",
        "rows": int(len(frame)),
        "broker_account_ready": bool(broker_ready),
        "trained_dqn_votes": int(frame["dqn_available"].sum()) if not frame.empty else 0,
        "trained_sac_votes": int(frame["sac_available"].sum()) if not frame.empty else 0,
        "trained_risk_votes": int(frame["risk_available"].sum()) if not frame.empty else 0,
        "hard_gate_passes": int(frame["hard_gates_pass"].sum()) if not frame.empty else 0,
        "positive_shadow_targets": int(
            (frame["shadow_target_exposure"] > 0).sum()
        ) if not frame.empty else 0,
        "money_control": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    return frame, audit
