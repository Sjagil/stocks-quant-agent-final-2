from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from stocks.research.cost_stress_v2_33 import cost_stress_trade_returns
from stocks.execution.cost_stress_v2_36 import stress_executable_edge

from .evidence_production_contracts_v2_39_3 import CostStressProductionResultV2393
from .oos_observation_validation_v2_39_3 import profit_factor, write_json


def _net_returns_factory_contract(gross: np.ndarray, *, per_side_bps: float) -> np.ndarray:
    cost = float(per_side_bps) / 10_000.0
    if cost < 0 or cost >= 1:
        raise ValueError("invalid per-side cost")
    return (1.0 + gross) * (1.0 - cost) / (1.0 + cost) - 1.0


def produce_cost_stress_from_oos(
    observations: pd.DataFrame,
    *,
    entity_id: str,
    base_cost_bps_per_side: float,
    effective_observations: int,
    minimum_effective_observations: int,
    output_dir: Path,
    config: dict,
    provenance_hash: str,
) -> tuple[CostStressProductionResultV2393, list[dict]]:
    gross = pd.to_numeric(observations.get("gross_return", pd.Series(dtype=float)), errors="coerce").to_numpy(dtype=float)
    gross = gross[np.isfinite(gross)]
    multipliers = tuple(float(x) for x in config.get("multipliers", (1.0, 1.5, 2.0, 3.0)))
    required = float(config.get("required_multiplier", 2.0))
    v233 = {float(x.multiple): x for x in cost_stress_trade_returns(
        gross, baseline_round_trip_cost_bps=2.0 * float(base_cost_bps_per_side), multiples=multipliers
    )} if len(gross) else {}
    gross_edge_bps = float(np.mean(gross) * 10_000.0) if len(gross) else math.nan
    v236 = {float(x.multiple): x for x in stress_executable_edge(
        gross_edge_bps, 2.0 * float(base_cost_bps_per_side), multiples=multipliers
    )} if len(gross) else {}
    rows: list[dict] = []
    for multiplier in multipliers:
        net = _net_returns_factory_contract(gross, per_side_bps=base_cost_bps_per_side * multiplier) if len(gross) else np.asarray([], dtype=float)
        expectancy = float(np.mean(net)) if len(net) else math.nan
        pf = float(profit_factor(net)) if len(net) else math.nan
        sample_ok = effective_observations >= minimum_effective_observations
        positive = bool(len(net) and np.isfinite(expectancy) and expectancy > 0)
        passed = bool(positive and (sample_ok or not config.get("require_effective_sample_for_pass", True)))
        rows.append({
            "stress_multiplier": multiplier,
            "cost_bps_per_side": float(base_cost_bps_per_side * multiplier),
            "round_trip_cost_bps_approx": float(2.0 * base_cost_bps_per_side * multiplier),
            "raw_trades": int(len(net)),
            "effective_observations": int(effective_observations),
            "expectancy": expectancy if np.isfinite(expectancy) else None,
            "expectancy_bps": expectancy * 10_000.0 if np.isfinite(expectancy) else None,
            "profit_factor": pf if np.isfinite(pf) else None,
            "v233_linear_expectancy_bps": (float(v233[multiplier].expectancy) * 10_000.0) if multiplier in v233 and np.isfinite(v233[multiplier].expectancy) else None,
            "v233_linear_profit_factor": float(v233[multiplier].profit_factor) if multiplier in v233 and np.isfinite(v233[multiplier].profit_factor) else None,
            "v236_mean_edge_after_cost_bps": float(v236[multiplier].net_edge_bps) if multiplier in v236 and np.isfinite(v236[multiplier].net_edge_bps) else None,
            "positive": positive,
            "passed": passed,
            "provenance_hash": provenance_hash,
            "execution_authority": "NONE",
        })
    scenarios_path = output_dir / "cost_stress_scenarios.csv"
    pd.DataFrame(rows).to_csv(scenarios_path, index=False)
    positive_multipliers = [r["stress_multiplier"] for r in rows if r["passed"]]
    max_positive = max(positive_multipliers, default=0.0)
    required_passed = any(abs(r["stress_multiplier"] - required) <= 1e-12 and r["passed"] for r in rows)
    reasons: list[str] = []
    if effective_observations < minimum_effective_observations:
        reasons.append("INSUFFICIENT_EFFECTIVE_OOS_SAMPLE")
    if not required_passed:
        reasons.append(f"COST_STRESS_{required:g}X_NOT_POSITIVE")
    evidence_payload = {
        "schema": "cost_stress_evidence_v2_39_3",
        "entity_id": entity_id,
        "source": "v2.36_practical_cost_stress_v2.39.3",
        "required_multiplier": required,
        "max_positive_multiplier": float(max_positive),
        "effective_observations": int(effective_observations),
        "minimum_effective_observations": int(minimum_effective_observations),
        "required_multiplier_passed": bool(required_passed),
        "provenance_hash": provenance_hash,
        "scenarios": rows,
        "execution_authority": "NONE",
    }
    evidence_path = output_dir / "cost_evidence.json"
    write_json(evidence_path, evidence_payload)
    return CostStressProductionResultV2393(
        entity_id=entity_id,
        status="QUALIFIED" if required_passed else "INSUFFICIENT",
        required_multiplier=required,
        max_positive_multiplier=float(max_positive),
        effective_observations=int(effective_observations),
        required_multiplier_passed=bool(required_passed),
        scenarios_path=str(scenarios_path),
        evidence_path=str(evidence_path),
        reasons=tuple(reasons),
    ), rows


__all__ = ["produce_cost_stress_from_oos"]
