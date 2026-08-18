from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

from _common import (
    add_repo_src,
    artifact_ref,
    base_health,
    run_worker,
)


CAPABILITIES = (
    "health",
    "broker_snapshot_read_only",
)


@dataclass(frozen=True)
class ObserverConfig:
    env_file: Path
    host: str
    port: int
    primary_client_id: int
    recon_client_id: int
    account_fingerprint_key: str
    request_timeout_seconds: float
    commission_grace_seconds: float
    snapshot_stability_delay_seconds: float
    read_only: bool = True
    live_trading_enabled: bool = False
    allow_order_transmission: bool = False
    execution_authority: str = "NONE"


def _repo(request: dict[str, Any]) -> Path:
    value = (request.get("context") or {}).get("repo_path")
    if not value:
        raise ValueError("reference repo_path missing")

    path = Path(value).resolve()
    if not path.is_dir():
        raise FileNotFoundError(path)

    return path


def _project_root(request: dict[str, Any]) -> Path:
    value = (request.get("context") or {}).get("project_root")
    if not value:
        raise ValueError("project_root missing")

    path = Path(value).resolve()
    if not path.is_dir():
        raise FileNotFoundError(path)

    return path


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name}_REQUIRED")
    return value


def _positive_int(name: str) -> int:
    raw = _required_env(name)
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name}_INVALID") from exc

    if value <= 0:
        raise ValueError(f"{name}_MUST_BE_POSITIVE")

    return value


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return float(default)

    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name}_INVALID") from exc

    if value <= 0:
        raise ValueError(f"{name}_MUST_BE_POSITIVE")

    return value


def observer_settings() -> dict[str, Any]:
    host = _required_env("IBKR_HOST")
    port = _positive_int("IBKR_PORT")
    primary = _positive_int("IBKR_CLIENT_ID")
    recon = _positive_int("IBKR_RECON_CLIENT_ID")
    fingerprint = _required_env(
        "IBKR_ACCOUNT_FINGERPRINT_KEY"
    )
    base = os.environ.get(
        "IBKR_ACCOUNT_BASE_CURRENCY",
        "EUR",
    ).strip().upper()

    if primary == 0 or recon == 0:
        raise ValueError("CLIENT_ID_ZERO_BLOCKED")

    if primary == recon:
        raise ValueError("CLIENT_ID_COLLISION_BLOCKED")

    if base != "EUR":
        raise ValueError(
            "V2_9_REQUIRES_EUR_BASE_CURRENCY"
        )

    return {
        "host": host,
        "port": port,
        "primary_client_id": primary,
        "recon_client_id": recon,
        "account_fingerprint_key": fingerprint,
        "base_currency": base,
        "request_timeout_seconds": _float_env(
            "IBKR_RECON_REQUEST_TIMEOUT_SECONDS",
            15.0,
        ),
        "commission_grace_seconds": _float_env(
            "IBKR_RECON_COMMISSION_GRACE_SECONDS",
            1.0,
        ),
        "snapshot_stability_delay_seconds": _float_env(
            "IBKR_RECON_SNAPSHOT_STABILITY_DELAY_SECONDS",
            1.0,
        ),
    }


def _health(request: dict[str, Any]) -> dict[str, Any]:
    repo = _repo(request)
    add_repo_src(repo)

    result = base_health(
        request,
        distributions=("ibapi", "filelock"),
        imports=(
            "ibapi",
            "stocks.ibkr.reconciliation.adapter",
            "stocks.ibkr.reconciliation.snapshots",
            "stocks.ibkr.reconciliation.account_state",
        ),
        capabilities=CAPABILITIES,
    )

    try:
        safe = observer_settings()
        result.setdefault("data", {})[
            "observer_config"
        ] = {
            "host_configured": bool(safe["host"]),
            "port": safe["port"],
            "primary_client_id_nonzero": (
                safe["primary_client_id"] != 0
            ),
            "recon_client_id_nonzero": (
                safe["recon_client_id"] != 0
            ),
            "client_ids_distinct": (
                safe["primary_client_id"]
                != safe["recon_client_id"]
            ),
            "fingerprint_key_configured": True,
            "base_currency": safe["base_currency"],
            "broker_writes_enabled": False,
        }
    except Exception as exc:
        result["state"] = "DEGRADED"
        result.setdefault("warnings", []).append(
            f"{type(exc).__name__}: {exc}"
        )

    return result


def _sum_counters(
    left: dict[str, int],
    right: dict[str, int],
) -> dict[str, int]:
    keys = set(left) | set(right)
    return {
        key: int(left.get(key, 0))
        + int(right.get(key, 0))
        for key in sorted(keys)
    }


def _snapshot(request: dict[str, Any], artifact_dir: Path):
    repo = _repo(request)
    project_root = _project_root(request)
    add_repo_src(repo)

    from stocks.ibkr.reconciliation.account_state import (
        derive_economic_account_state,
    )
    from stocks.ibkr.reconciliation.models import (
        model_to_jsonable,
    )
    from stocks.ibkr.reconciliation.snapshots import (
        capture_snapshot,
        snapshot_components_complete,
        stability_status,
    )

    settings = observer_settings()

    config = ObserverConfig(
        env_file=project_root / ".env",
        host=settings["host"],
        port=settings["port"],
        primary_client_id=settings[
            "primary_client_id"
        ],
        recon_client_id=settings[
            "recon_client_id"
        ],
        account_fingerprint_key=settings[
            "account_fingerprint_key"
        ],
        request_timeout_seconds=settings[
            "request_timeout_seconds"
        ],
        commission_grace_seconds=settings[
            "commission_grace_seconds"
        ],
        snapshot_stability_delay_seconds=settings[
            "snapshot_stability_delay_seconds"
        ],
    )

    first, read_1, write_1 = capture_snapshot(config)

    time.sleep(
        config.snapshot_stability_delay_seconds
    )

    second, read_2, write_2 = capture_snapshot(config)

    stability = stability_status(first, second)
    snapshot = model_to_jsonable(second)

    economic = derive_economic_account_state(
        snapshot,
        expected_base_currency=settings[
            "base_currency"
        ],
        snapshot_hash_verified=bool(
            second.content_hash
        ),
        execution_max_age=timedelta(
            seconds=float(
                os.environ.get(
                    "IBKR_EXECUTION_STATE_MAX_AGE_SECONDS",
                    "120",
                )
            )
        ),
    )

    complete = snapshot_components_complete(second)
    stable = bool(stability.get("stable", False))

    if not stable:
        blockers = list(
            economic.get("execution_blockers") or []
        )
        blockers.append(
            "BROKER_DOUBLE_SNAPSHOT_NOT_STABLE"
        )
        economic["execution_blockers"] = sorted(
            set(blockers)
        )
        economic["execution_status"] = "NO_GO"

    reads = _sum_counters(read_1, read_2)
    writes = _sum_counters(write_1, write_2)

    write_total = sum(
        int(value)
        for key, value in writes.items()
        if key.endswith("_calls")
    )

    if write_total != 0:
        raise RuntimeError(
            "BROKER_WRITE_COUNTER_NONZERO_BLOCKED"
        )

    payload = {
        "schema": "ibkr_readonly_snapshot_v2_9",
        "broker_observation_authority": (
            "READ_ONLY_OBSERVATION"
        ),
        "execution_authority": "NONE",
        "snapshot_components_complete": complete,
        "double_snapshot_stable": stable,
        "stability": stability,
        "economic_account_state": economic,
        "snapshot": snapshot,
        "read_counters": reads,
        "write_counters": writes,
        "broker_write_calls": write_total,
        "config": {
            "host": settings["host"],
            "port": settings["port"],
            "primary_client_id_nonzero": True,
            "recon_client_id_nonzero": True,
            "client_ids_distinct": True,
            "account_fingerprint_key_configured": True,
            "base_currency": settings[
                "base_currency"
            ],
            "read_only": True,
            "live_trading_enabled_by_worker": False,
            "allow_order_transmission_by_worker": False,
        },
    }

    output = (
        artifact_dir
        / "ibkr_readonly_snapshot_v2_9.json"
    )
    output.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    state = (
        "OK"
        if complete and stable
        else "DEGRADED"
    )

    return {
        "state": state,
        "data": {
            "snapshot_components_complete": complete,
            "double_snapshot_stable": stable,
            "lifecycle_state": economic.get(
                "lifecycle_state"
            ),
            "research_status": economic.get(
                "research_status"
            ),
            "execution_account_status": economic.get(
                "execution_status"
            ),
            "reporting_value_eur": economic.get(
                "reporting_value_eur"
            ),
            "spendable_eur": economic.get(
                "spendable_eur"
            ),
            "execution_sizing_capacity_eur": economic.get(
                "execution_sizing_capacity_eur"
            ),
            "broker_write_calls": write_total,
            "execution_authority": "NONE",
        },
        "artifacts": [
            artifact_ref(
                output,
                media_type="application/json",
            )
        ],
        "warnings": (
            []
            if complete and stable
            else [
                "BROKER_SNAPSHOT_NOT_EXECUTION_STABLE"
            ]
        ),
    }


def handle(
    request: dict[str, Any],
    artifact_dir: Path,
) -> dict[str, Any]:
    action = request.get("action")

    if action == "health":
        return _health(request)

    if action == "broker_snapshot_read_only":
        return _snapshot(
            request,
            artifact_dir,
        )

    raise ValueError(
        f"unsupported action: {action}"
    )


if __name__ == "__main__":
    run_worker(handle)
