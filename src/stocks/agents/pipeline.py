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


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return False
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", "", "nan", "none"}:
        return False
    raise ValueError(f"ambiguous boolean value: {value!r}")


def _load_manifest(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    candidate = Path(str(path))
    if not candidate.is_file():
        return None
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    if payload.get("research_status") != "SHADOW_VALIDATED":
        return None
    if str(payload.get("execution_authority", "NONE")).upper() != "NONE":
        raise ValueError("agent deployment manifest grants forbidden authority")
    return payload


def _validated_deployments(
    root: Path,
    *,
    timeframe: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    path = (
        root
        / "artifacts/research_runtime/"
        "agent_validation_v2_13/registry.csv"
    )
    if not path.is_file():
        return {}

    frame = pd.read_csv(path)
    deployments: dict[tuple[str, str], dict[str, Any]] = {}

    for row in frame.to_dict(orient="records"):
        if str(row.get("timeframe")) != timeframe:
            continue
        if str(row.get("registry_status")) != "VALIDATED_AGENT_CHALLENGER":
            continue
        manifest = _load_manifest(row.get("deployment_manifest"))
        if manifest is None:
            continue
        key = (
            str(row["symbol"]).upper(),
            str(row["algorithm"]).upper(),
        )
        deployments[key] = manifest

    return deployments


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
            reason="VALIDATED_DQN_DEPLOYMENT_MISSING",
        )

    try:
        from stable_baselines3 import DQN

        model = DQN.load(manifest["model_path"])
        action, _ = model.predict(
            observation,
            deterministic=True,
        )
        mapping = {
            0: "HOLD",
            1: "ENTER_LONG",
            2: "EXIT_TO_CASH",
        }
        text = mapping[
            int(np.asarray(action).reshape(-1)[0])
        ]
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
            reason="VALIDATED_SAC_DEPLOYMENT_MISSING",
        )

    try:
        from stable_baselines3 import SAC

        model = SAC.load(manifest["model_path"])
        action, _ = model.predict(
            observation,
            deterministic=True,
        )
        target = float(
            np.clip(
                np.asarray(action).reshape(-1)[0],
                0.0,
                1.0,
            )
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
            confidence=0.0,
            available=False,
            reason="RISK_AGENT_NOT_APPLICABLE_WHILE_FLAT",
        )

    if not manifest:
        return AgentVote(
            agent="MASKABLE_PPO_RISK",
            role="POSITION_RISK_REDUCTION",
            symbol=symbol,
            action="KEEP",
            available=False,
            reason="VALIDATED_RISK_DEPLOYMENT_MISSING",
        )

    try:
        from sb3_contrib import MaskablePPO

        model = MaskablePPO.load(manifest["model_path"])
        action, _ = model.predict(
            observation,
            deterministic=True,
            action_masks=np.array(
                [True, True, True, True],
                dtype=bool,
            ),
        )
        mapping = {
            0: "KEEP",
            1: "CUT_25",
            2: "CUT_50",
            3: "FLAT",
        }
        text = mapping[
            int(np.asarray(action).reshape(-1)[0])
        ]
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


def _broker_state(
    root: Path,
) -> tuple[bool, dict[str, float]]:
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
        and economic.get("execution_status")
        == "EXECUTION_ACCOUNT_READY"
        and int(payload.get("broker_write_calls", 0)) == 0
    )

    positions: dict[str, float] = {}
    raw_positions = (
        ((payload.get("snapshot") or {}).get("positions") or {})
        .get("positions", [])
    )

    for row in raw_positions:
        symbol = str(
            row.get("symbol")
            or row.get("local_symbol")
            or ""
        ).upper()

        quantity_value = (
            row.get("position_quantity")
            if "position_quantity" in row
            else row.get("position", row.get("quantity", 0.0))
        )

        try:
            quantity = float(quantity_value or 0.0)
        except (TypeError, ValueError):
            quantity = 0.0

        if symbol:
            positions[symbol] = quantity

    return ready, positions


def _shariah_map(
    root: Path,
) -> dict[str, bool]:
    path = (
        root
        / "artifacts/research_runtime/"
        "shariah_financial_verification/verification.csv"
    )
    if not path.is_file():
        return {}

    frame = pd.read_csv(path)
    output = {}

    for row in frame.to_dict(orient="records"):
        symbol = str(row["symbol"]).upper()
        output[symbol] = _as_bool(
            row.get("trade_eligible", False)
        )

    return output


def _broadly_validated_hypotheses(
    root: Path,
) -> set[str]:
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
    return set(
        selected["hypothesis_id"].astype(str)
    )


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
            "schema": "agent_shadow_pipeline_v2_13",
            "rows": 0,
            "reason": "FORWARD_SIGNAL_STATE_MISSING",
            "execution_authority": "NONE",
        }

    forward = pd.read_csv(forward_path)
    broker_ready, positions = _broker_state(root)
    shariah = _shariah_map(root)
    validated_hypotheses = (
        _broadly_validated_hypotheses(root)
    )
    deployments = _validated_deployments(
        root,
        timeframe=timeframe,
    )

    rows: list[dict[str, Any]] = []
    env_cfg = EnvironmentConfig()

    for row in forward.to_dict(orient="records"):
        symbol = str(row["symbol"]).upper()

        try:
            frame = frame_for_timeframe(
                root,
                symbol,
                timeframe,
            )
            current_quantity = float(
                positions.get(symbol, 0.0)
            )
            current_exposure = (
                1.0
                if current_quantity > 0
                else 0.0
            )
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
            candle_error = (
                f"{type(exc).__name__}:{exc}"
            )
            current_exposure = 0.0
            observation = None

        dqn_manifest = deployments.get(
            (symbol, "DQN")
        )
        sac_manifest = deployments.get(
            (symbol, "SAC")
        )
        risk_manifest = deployments.get(
            (symbol, "MASKABLE_PPO")
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

        nlp = read_nlp_context(
            root,
            symbol,
        )
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

        fresh = _as_bool(
            row.get("new_entry_ready", False)
        )
        hypothesis_id = str(
            row.get("hypothesis_id") or ""
        )
        validated_strategy = (
            hypothesis_id
            in validated_hypotheses
        )

        envelope = fuse_agent_votes(
            symbol=symbol,
            fresh_validated_entry=fresh,
            shariah_verified=bool(
                shariah.get(symbol, False)
            ),
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
                "shariah_verified": bool(
                    shariah.get(symbol, False)
                ),
                "fresh_validated_entry": fresh,
                "current_exposure": current_exposure,
                "dqn_model_validated": (
                    dqn_manifest is not None
                ),
                "dqn_action": timing_vote.action,
                "dqn_vote_available": timing_vote.available,
                "sac_model_validated": (
                    sac_manifest is not None
                ),
                "sac_target_exposure": (
                    envelope.sac_target_exposure
                ),
                "sac_vote_available": sizing_vote.available,
                "risk_model_validated": (
                    risk_manifest is not None
                ),
                "risk_applicable": (
                    current_exposure > 1e-12
                ),
                "risk_action": risk_vote.action,
                "risk_vote_available": risk_vote.available,
                "nlp_sentiment": nlp.sentiment,
                "nlp_confidence": nlp.confidence,
                "nlp_modifier": nlp.modifier,
                "shadow_target_exposure": (
                    envelope.shadow_target_exposure
                ),
                "hard_gates_pass": (
                    envelope.hard_gates_pass
                ),
                "blockers": "|".join(
                    envelope.blockers
                ),
                "money_control": False,
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": "NONE",
            }
        )

    result = pd.DataFrame(rows)
    audit = {
        "schema": "agent_shadow_pipeline_v2_13",
        "rows": int(len(result)),
        "broker_account_ready": bool(broker_ready),
        "validated_dqn_models": int(
            result["dqn_model_validated"].sum()
        ) if not result.empty else 0,
        "validated_sac_models": int(
            result["sac_model_validated"].sum()
        ) if not result.empty else 0,
        "validated_risk_models": int(
            result["risk_model_validated"].sum()
        ) if not result.empty else 0,
        "risk_applicable_rows": int(
            result["risk_applicable"].sum()
        ) if not result.empty else 0,
        "hard_gate_passes": int(
            result["hard_gates_pass"].sum()
        ) if not result.empty else 0,
        "positive_shadow_targets": int(
            (
                result["shadow_target_exposure"]
                > 0
            ).sum()
        ) if not result.empty else 0,
        "smoke_models_accepted": 0,
        "money_control": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    return result, audit
