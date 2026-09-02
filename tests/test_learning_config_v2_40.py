import json
from pathlib import Path
import pytest
from stocks.learning.config_v2_40 import agent_specs_v240, load_learning_config_v240


def base():
    return {
        "schema": "autonomous_continuous_learning_v2_40",
        "execution_authority": "NONE",
        "broker_submission_enabled": False,
        "automatic_live_promotion": False,
        "automatic_champion_promotion": False,
        "agents": [{"agent_id":"p","algorithm":"PPO","symbol":"SPY","timeframe":"1h","data_path":"x"}],
    }


def test_config_rejects_authority(tmp_path: Path):
    p = tmp_path / "c.json"
    x = base(); x["execution_authority"] = "LIVE"; p.write_text(json.dumps(x))
    with pytest.raises(ValueError):
        load_learning_config_v240(tmp_path, p)


def test_agent_specs_are_none_authority(tmp_path: Path):
    p = tmp_path / "c.json"; p.write_text(json.dumps(base()))
    cfg = load_learning_config_v240(tmp_path, p)
    assert agent_specs_v240(cfg)[0].execution_authority == "NONE"
