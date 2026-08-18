from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stocks.agents.candle_fabric import candle_summary
from stocks.agents.contracts import AgentVote
from stocks.agents.ensemble import fuse_agent_votes
from stocks.agents.environments import (
    DiscreteLongOnlyTimingEnv,
    RiskReductionEnv,
)
from stocks.agents.marl import coordinate_roles
from stocks.agents.nlp_context import bounded_modifier


def sample_frame(rows: int = 400) -> pd.DataFrame:
    index = pd.date_range(
        "2025-01-01",
        periods=rows,
        freq="h",
        tz="UTC",
    )
    close = 100.0 + np.linspace(0.0, 20.0, rows)
    return pd.DataFrame(
        {
            "open": close - 0.10,
            "high": close + 0.50,
            "low": close - 0.50,
            "close": close,
            "volume": np.linspace(1000.0, 2000.0, rows),
        },
        index=index,
    )


def votes(symbol: str = "TEST"):
    return (
        AgentVote(
            agent="DQN",
            role="TIMING",
            symbol=symbol,
            action="ENTER_LONG",
            available=True,
        ),
        AgentVote(
            agent="SAC",
            role="SIZING",
            symbol=symbol,
            action="TARGET",
            target_exposure=0.80,
            available=True,
        ),
        AgentVote(
            agent="RISK",
            role="RISK",
            symbol=symbol,
            action="KEEP",
            available=True,
        ),
        AgentVote(
            agent="NLP",
            role="CONTEXT",
            symbol=symbol,
            action="MODIFIER",
            modifier=1.10,
            available=True,
        ),
    )


def test_dqn_environment_is_discrete_and_long_only():
    env = DiscreteLongOnlyTimingEnv(sample_frame())
    assert env.action_space.n == 3
    _obs, info = env.reset()
    assert info["position"] == 0.0
    _obs, _reward, _terminated, _truncated, info = env.step(
        DiscreteLongOnlyTimingEnv.ENTER_LONG
    )
    assert info["position"] == 1.0
    _obs, _reward, _terminated, _truncated, info = env.step(
        DiscreteLongOnlyTimingEnv.EXIT_TO_CASH
    )
    assert info["position"] == 0.0


def test_risk_environment_can_only_reduce():
    env = RiskReductionEnv(sample_frame())
    _obs, info = env.reset()
    assert info["position"] == 1.0
    _obs, _reward, _terminated, _truncated, info = env.step(
        RiskReductionEnv.CUT_50
    )
    assert info["position"] == pytest.approx(0.5)
    _obs, _reward, _terminated, _truncated, info = env.step(
        RiskReductionEnv.KEEP
    )
    assert info["position"] == pytest.approx(0.5)


def test_risk_mask_for_flat_position_prevents_opening():
    env = RiskReductionEnv(sample_frame())
    env.reset()
    env._position = 0.0
    assert env.action_masks().tolist() == [True, False, False, False]


def test_nlp_modifier_is_bounded():
    assert bounded_modifier(10.0, 1.0) == pytest.approx(1.10)
    assert bounded_modifier(-10.0, 1.0) == pytest.approx(0.90)


def test_agents_cannot_bypass_missing_shariah_gate():
    timing, sizing, risk, nlp = votes()
    result = fuse_agent_votes(
        symbol="TEST",
        fresh_validated_entry=True,
        shariah_verified=False,
        broker_account_ready=True,
        validated_strategy=True,
        current_exposure=0.0,
        timing_vote=timing,
        sizing_vote=sizing,
        risk_vote=risk,
        nlp_vote=nlp,
    )
    assert result.shadow_target_exposure == 0.0
    assert "SHARIAH_VERIFIED_REQUIRED" in result.blockers
    assert result.execution_authority == "NONE"


def test_agents_cannot_manufacture_entry_without_fresh_trigger():
    timing, sizing, risk, nlp = votes()
    result = fuse_agent_votes(
        symbol="TEST",
        fresh_validated_entry=False,
        shariah_verified=True,
        broker_account_ready=True,
        validated_strategy=True,
        current_exposure=0.0,
        timing_vote=timing,
        sizing_vote=sizing,
        risk_vote=risk,
        nlp_vote=nlp,
    )
    assert result.shadow_target_exposure == 0.0
    assert "FRESH_VALIDATED_ENTRY_REQUIRED" in result.blockers


def test_coordinator_never_shorts():
    result = coordinate_roles(
        current_exposure=0.2,
        timing_action="ENTER_LONG",
        sizing_target=-10.0,
        risk_action="KEEP",
    )
    assert result.resulting_exposure == 0.0

    result = coordinate_roles(
        current_exposure=0.8,
        timing_action="HOLD",
        sizing_target=1.0,
        risk_action="FLAT",
    )
    assert result.resulting_exposure == 0.0


def test_candle_validation_rejects_bad_high_low():
    frame = sample_frame()
    frame.iloc[-1, frame.columns.get_loc("high")] = 1.0
    with pytest.raises(ValueError):
        candle_summary(frame)


def test_pettingzoo_parallel_contract_when_installed():
    pytest.importorskip("pettingzoo")
    from stocks.agents.marl import SpecialistParallelTradingEnv

    env = SpecialistParallelTradingEnv(sample_frame())
    obs, infos = env.reset(seed=42)
    assert set(obs) == {"timing", "sizing", "risk"}
    assert all(
        info["execution_authority"] == "NONE"
        for info in infos.values()
    )
    result = env.step(
        {
            "timing": 1,
            "sizing": np.array([0.8], dtype=np.float32),
            "risk": 0,
        }
    )
    rewards = result[1]
    assert set(rewards) == {"timing", "sizing", "risk"}
