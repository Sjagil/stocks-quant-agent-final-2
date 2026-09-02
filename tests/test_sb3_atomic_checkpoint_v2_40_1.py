from pathlib import Path
import sys
import types

from stocks.learning.sb3_continuous_trainer_v2_40 import train_or_continue_sb3_v240


class RealisticSuffixModel:
    def __init__(self, policy, env, **kwargs):
        self.env = env

    @classmethod
    def load(cls, path, env=None):
        return cls("MlpPolicy", env)

    def learn(self, total_timesteps, reset_num_timesteps=True):
        return self

    def save(self, path):
        p = Path(path)
        actual = p if p.suffix == ".zip" else p.with_suffix(".zip")
        actual.write_bytes(b"model")

    def save_replay_buffer(self, path):
        p = Path(path)
        actual = p if p.suffix == ".pkl" else p.with_suffix(".pkl")
        actual.write_bytes(b"replay")

    def load_replay_buffer(self, path):
        pass


def install_fake():
    mod = types.ModuleType("stable_baselines3")
    mod.PPO = RealisticSuffixModel
    mod.SAC = RealisticSuffixModel
    sys.modules["stable_baselines3"] = mod


def test_explicit_zip_temp_is_atomically_promoted(tmp_path):
    install_fake()
    out = train_or_continue_sb3_v240(
        algorithm="PPO",
        env=object(),
        model_base=tmp_path / "current",
        total_timesteps=5,
        seed=7,
    )
    assert Path(out["model_path"]) == tmp_path / "current.zip"
    assert Path(out["model_path"]).is_file()
    assert not (tmp_path / "current.tmp.zip").exists()


def test_sac_model_and_replay_persist(tmp_path):
    install_fake()
    out = train_or_continue_sb3_v240(
        algorithm="SAC",
        env=object(),
        model_base=tmp_path / "sac_current",
        total_timesteps=5,
        seed=8,
        replay_buffer_path=tmp_path / "replay.pkl",
    )
    assert Path(out["model_path"]).is_file()
    assert Path(out["replay_buffer_path"]).is_file()
    assert not (tmp_path / "sac_current.tmp.zip").exists()
    assert not (tmp_path / "replay.tmp.pkl").exists()
