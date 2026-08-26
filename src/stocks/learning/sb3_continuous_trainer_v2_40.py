from __future__ import annotations

import hashlib
import os
from pathlib import Path


def _classes():
    try:
        from stable_baselines3 import PPO, SAC
    except Exception as exc:  # pragma: no cover
        raise ImportError("stable-baselines3 is required; install the rl extra") from exc
    return PPO, SAC


def _atomic_model_save(model, final_base: Path) -> Path:
    final_base.parent.mkdir(parents=True, exist_ok=True)
    final_zip = Path(str(final_base) + ".zip")
    tmp_zip = final_zip.with_name(f"{final_zip.stem}.tmp.zip")
    if tmp_zip.exists():
        tmp_zip.unlink()

    # Stable-Baselines3 normalizes model paths to .zip. Supplying an
    # already-.zip temp path makes the actual output filename deterministic.
    model.save(str(tmp_zip))
    if not tmp_zip.is_file():
        raise FileNotFoundError(
            f"SB3 checkpoint save did not create expected temp file: {tmp_zip}"
        )

    os.replace(tmp_zip, final_zip)
    return final_zip

def _atomic_replay_save(model, final_path: Path) -> Path:
    final_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = final_path.suffix or ".pkl"
    stem = final_path.stem if final_path.suffix else final_path.name
    tmp = final_path.with_name(f"{stem}.tmp{suffix}")
    if tmp.exists():
        tmp.unlink()

    # save_replay_buffer uses suffix-aware path handling too. Keep the
    # temporary filename on the final suffix so no hidden rename occurs.
    model.save_replay_buffer(str(tmp))
    if not tmp.is_file():
        raise FileNotFoundError(
            f"SB3 replay-buffer save did not create expected temp file: {tmp}"
        )

    os.replace(tmp, final_path)
    return final_path

def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def train_or_continue_sb3_v240(
    *,
    algorithm: str,
    env,
    model_base: str | Path,
    total_timesteps: int,
    seed: int,
    warm_start: bool = True,
    replay_buffer_path: str | Path | None = None,
    model_kwargs: dict | None = None,
) -> dict:
    PPO, SAC = _classes()
    name = str(algorithm).upper()
    if name not in {"PPO", "SAC"}:
        raise ValueError("algorithm must be PPO or SAC")
    cls = PPO if name == "PPO" else SAC
    model_base = Path(model_base)
    final_zip = Path(str(model_base) + ".zip")
    warm = bool(warm_start and final_zip.is_file())

    if warm:
        model = cls.load(str(final_zip), env=env)
    else:
        kwargs = {"verbose": 0, "seed": int(seed)}
        kwargs.update(model_kwargs or {})
        model = cls("MlpPolicy", env, **kwargs)

    replay = Path(replay_buffer_path) if replay_buffer_path else None
    replay_loaded = False
    if name == "SAC" and replay is not None and replay.is_file() and warm:
        model.load_replay_buffer(str(replay))
        replay_loaded = True

    model.learn(total_timesteps=int(total_timesteps), reset_num_timesteps=not warm)
    saved = _atomic_model_save(model, model_base)
    saved_replay = None
    if name == "SAC" and replay is not None:
        saved_replay = _atomic_replay_save(model, replay)

    return {
        "algorithm": name,
        "warm_started": warm,
        "replay_loaded": replay_loaded,
        "model_path": str(saved),
        "model_sha256": sha256_file(saved),
        "replay_buffer_path": str(saved_replay) if saved_replay else None,
        "timesteps": int(total_timesteps),
        "execution_authority": "NONE",
    }


__all__ = ["train_or_continue_sb3_v240", "sha256_file"]
