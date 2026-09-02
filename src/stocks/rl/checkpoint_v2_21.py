from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from .contracts_v2_21 import DEPLOYMENT_MODE, EXECUTION_AUTHORITY


def sha256_path_v221(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tensor_sha256(arrays: Mapping[str, np.ndarray]) -> str:
    digest = hashlib.sha256()
    for name in sorted(arrays):
        value = np.ascontiguousarray(arrays[name])
        digest.update(name.encode())
        digest.update(str(value.dtype).encode())
        digest.update(json.dumps(value.shape).encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False, default=str)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def _module_map(model: Any, algorithm: str) -> dict[str, Any]:
    normalized = algorithm.upper()
    if normalized == "MAPPO":
        names = ("actor", "critic")
    elif normalized == "MATD3":
        names = ("actor", "actor_target", "critic", "critic_target")
    else:
        raise ValueError(f"unsupported checkpoint algorithm: {algorithm}")
    modules = {name: getattr(model, name, None) for name in names}
    missing = [name for name, module in modules.items() if module is None]
    if missing:
        raise ValueError(f"checkpoint model missing modules: {missing}")
    return modules


def save_research_checkpoint_v221(
    model: Any,
    output_dir: str | Path,
    *,
    algorithm: str,
    seed: int,
    fold: int,
    dataset_hash: str,
    config_hash: str,
    code_commit: str,
    extra: Mapping[str, Any] | None = None,
) -> Path:
    """Save model weights without pickle and bind them to a SHA-256 manifest."""

    if any(len(value) != 64 for value in (dataset_hash, config_hash)):
        raise ValueError("dataset_hash and config_hash must be SHA-256")
    if seed < 0 or fold < 0:
        raise ValueError("seed and fold must be non-negative")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    weights_path = root / "weights.npz"
    manifest_path = root / "manifest.json"
    arrays: dict[str, np.ndarray] = {}
    for module_name, module in _module_map(model, algorithm).items():
        for key, tensor in module.state_dict().items():
            arrays[f"{module_name}.{key}"] = tensor.detach().cpu().numpy()
    if not arrays:
        raise RuntimeError("checkpoint has no model weights")

    with tempfile.NamedTemporaryFile(dir=root, delete=False) as handle:
        np.savez_compressed(handle, **arrays)
        temporary = Path(handle.name)
    temporary.replace(weights_path)
    weights_hash = sha256_path_v221(weights_path)
    model_manifest = dict(model.manifest())
    manifest = {
        "schema_version": "v2.21.1",
        "algorithm": algorithm.upper(),
        "seed": int(seed),
        "fold": int(fold),
        "dataset_hash": dataset_hash.lower(),
        "config_hash": config_hash.lower(),
        "code_commit": str(code_commit),
        "weights_file": weights_path.name,
        "weights_sha256": weights_hash,
        "tensor_sha256": _tensor_sha256(arrays),
        "tensor_count": len(arrays),
        "tensor_names": sorted(arrays),
        "model": model_manifest,
        "deployment_mode": DEPLOYMENT_MODE,
        "automatic_live_promotion": False,
        "execution_authority": EXECUTION_AUTHORITY,
        "broker_calls": 0,
        "order_calls": 0,
        "extra": dict(extra or {}),
    }
    _atomic_json(manifest_path, manifest)
    return manifest_path


def verify_research_checkpoint_v221(
    manifest_path: str | Path,
) -> dict[str, Any]:
    path = Path(manifest_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "algorithm",
        "weights_file",
        "weights_sha256",
        "tensor_sha256",
        "tensor_names",
        "execution_authority",
        "broker_calls",
        "order_calls",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(f"checkpoint manifest missing fields: {missing}")
    if manifest["schema_version"] != "v2.21.1":
        raise ValueError("unsupported checkpoint schema")
    if manifest["execution_authority"] != EXECUTION_AUTHORITY:
        raise ValueError("checkpoint attempts to grant execution authority")
    if int(manifest["broker_calls"]) or int(manifest["order_calls"]):
        raise ValueError("checkpoint reports external order activity")
    weights = path.parent / str(manifest["weights_file"])
    if not weights.is_file():
        raise FileNotFoundError(weights)
    if sha256_path_v221(weights) != str(manifest["weights_sha256"]).lower():
        raise ValueError("checkpoint weight hash mismatch")
    with np.load(weights, allow_pickle=False) as archive:
        names = sorted(archive.files)
        if names != sorted(str(name) for name in manifest["tensor_names"]):
            raise ValueError("checkpoint tensor inventory mismatch")
        if not names or not all(np.isfinite(archive[name]).all() for name in names):
            raise ValueError("checkpoint contains empty or non-finite tensors")
        arrays = {name: archive[name].copy() for name in names}
        if _tensor_sha256(arrays) != str(manifest["tensor_sha256"]).lower():
            raise ValueError("checkpoint tensor hash mismatch")
    return manifest


def load_research_checkpoint_v221(
    model: Any,
    manifest_path: str | Path,
) -> dict[str, Any]:
    manifest = verify_research_checkpoint_v221(manifest_path)
    modules = _module_map(model, str(manifest["algorithm"]))
    weights_path = Path(manifest_path).parent / str(manifest["weights_file"])
    with np.load(weights_path, allow_pickle=False) as archive:
        for module_name, module in modules.items():
            prefix = f"{module_name}."
            state = {
                name.removeprefix(prefix): archive[name].copy()
                for name in archive.files
                if name.startswith(prefix)
            }
            expected = set(module.state_dict())
            if set(state) != expected:
                raise ValueError(f"checkpoint state mismatch for {module_name}")
            try:
                import torch
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("PyTorch is required to load RL checkpoints") from exc
            module.load_state_dict({key: torch.from_numpy(value) for key, value in state.items()})
    return manifest
