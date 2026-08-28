import sys
import types
from pathlib import Path
from stocks.learning.sb3_continuous_trainer_v2_40 import train_or_continue_sb3_v240


class FakeModel:
    loaded = False
    def __init__(self, policy, env, **kwargs): self.env=env
    @classmethod
    def load(cls, path, env=None): cls.loaded=True; return cls("MlpPolicy",env)
    def learn(self, total_timesteps, reset_num_timesteps=True): self.steps=total_timesteps; self.reset=reset_num_timesteps; return self
    def save(self, path):
        p=Path(path); actual=p if p.suffix==".zip" else p.with_suffix(".zip"); actual.write_bytes(b"model")
    def save_replay_buffer(self, path):
        p=Path(path); actual=p if p.suffix==".pkl" else p.with_suffix(".pkl"); actual.write_bytes(b"replay")
    def load_replay_buffer(self, path): self.replay_loaded=True


def install_fake():
    mod=types.ModuleType("stable_baselines3"); mod.PPO=FakeModel; mod.SAC=FakeModel; sys.modules["stable_baselines3"]=mod


def test_ppo_warm_start(tmp_path: Path):
    install_fake(); base=tmp_path/"model"
    first=train_or_continue_sb3_v240(algorithm="PPO",env=object(),model_base=base,total_timesteps=10,seed=1)
    assert not first["warm_started"]
    second=train_or_continue_sb3_v240(algorithm="PPO",env=object(),model_base=base,total_timesteps=10,seed=1)
    assert second["warm_started"]
    assert Path(second["model_path"]).is_file()


def test_sac_persists_replay(tmp_path: Path):
    install_fake(); base=tmp_path/"sac"; replay=tmp_path/"buffer.pkl"
    out=train_or_continue_sb3_v240(algorithm="SAC",env=object(),model_base=base,total_timesteps=10,seed=1,replay_buffer_path=replay)
    assert Path(out["replay_buffer_path"]).is_file()
