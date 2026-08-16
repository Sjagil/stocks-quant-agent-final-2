from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stocks.agents.contracts import AgentVote
from stocks.agents.ensemble import fuse_agent_votes
from stocks.agents.environments import (
    ContinuousLongOnlySizingEnv,
    DiscreteLongOnlyTimingEnv,
    RiskReductionEnv,
)
from stocks.agents.pipeline import (
    _as_bool,
    _load_manifest,
)


def sample_frame(rows: int = 700) -> pd.DataFrame:
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
            "volume": np.linspace(
                1000.0,
                2000.0,
                rows,
            ),
        },
        index=index,
    )


def test_episode_randomization_is_bounded():
    env = DiscreteLongOnlyTimingEnv(
        sample_frame(),
        random_start=True,
        episode_length=64,
    )
    starts = []
    for seed in (1, 2, 3, 4):
        _obs, info = env.reset(seed=seed)
        starts.append(info["episode_start"])
        assert (
            info["episode_last"]
            - info["episode_start"]
            <= 63
        )
    assert len(set(starts)) > 1


def test_continuous_sizing_never_short():
    env = ContinuousLongOnlySizingEnv(
        sample_frame(),
        episode_length=64,
    )
    env.reset()
    _obs, _reward, _terminated, _truncated, info = env.step(
        np.array([-10.0], dtype=np.float32)
    )
    assert info["position"] == 0.0


def test_risk_flat_terminates_episode():
    env = RiskReductionEnv(
        sample_frame(),
        episode_length=64,
    )
    env.reset()
    _obs, _reward, terminated, _truncated, info = env.step(
        RiskReductionEnv.FLAT
    )
    assert terminated is True
    assert info["position"] == 0.0


def _votes(
    *,
    risk_action: str = "KEEP",
    nlp_modifier: float = 1.0,
):
    timing = AgentVote(
        agent="DQN",
        role="TIMING",
        symbol="TEST",
        action="ENTER_LONG",
        available=True,
    )
    sizing = AgentVote(
        agent="SAC",
        role="SIZING",
        symbol="TEST",
        action="TARGET",
        target_exposure=0.80,
        available=True,
    )
    risk = AgentVote(
        agent="RISK",
        role="RISK",
        symbol="TEST",
        action=risk_action,
        available=True,
    )
    nlp = AgentVote(
        agent="NLP",
        role="CONTEXT",
        symbol="TEST",
        action="MODIFIER",
        modifier=nlp_modifier,
        available=True,
    )
    return timing, sizing, risk, nlp


def test_positive_nlp_cannot_undo_risk_cap():
    timing, sizing, risk, nlp = _votes(
        risk_action="CUT_50",
        nlp_modifier=1.10,
    )
    result = fuse_agent_votes(
        symbol="TEST",
        fresh_validated_entry=True,
        shariah_verified=True,
        broker_account_ready=True,
        validated_strategy=True,
        current_exposure=0.0,
        timing_vote=timing,
        sizing_vote=sizing,
        risk_vote=risk,
        nlp_vote=nlp,
    )
    # 0.8 * 1.10 = 0.88, risk is final and halves that to 0.44.
    assert result.shadow_target_exposure == pytest.approx(
        0.44
    )


def test_missing_hard_gate_still_forces_zero():
    timing, sizing, risk, nlp = _votes(
        nlp_modifier=1.10,
    )
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


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("False", False),
        ("TRUE", True),
        (0, False),
        (1, True),
        (False, False),
        (True, True),
    ],
)
def test_bool_parser_is_explicit(value, expected):
    assert _as_bool(value) is expected


def test_unvalidated_manifest_is_rejected(tmp_path: Path):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "research_status": "SMOKE_ONLY",
                "execution_authority": "NONE",
            }
        ),
        encoding="utf-8",
    )
    assert _load_manifest(path) is None


def test_shadow_validated_manifest_is_accepted(tmp_path: Path):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "research_status": "SHADOW_VALIDATED",
                "execution_authority": "NONE",
                "model_path": "fake.zip",
            }
        ),
        encoding="utf-8",
    )
    assert _load_manifest(path) is not None


def test_manifest_with_authority_is_rejected(tmp_path: Path):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "research_status": "SHADOW_VALIDATED",
                "execution_authority": "LIVE",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        _load_manifest(path)
