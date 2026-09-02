from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


SCHEMA = "strategy_dna_v2_32"
EXECUTION_AUTHORITY_NONE = "NONE"


class ConditionOperator(str, Enum):
    GT = "GT"
    GE = "GE"
    LT = "LT"
    LE = "LE"
    BETWEEN = "BETWEEN"
    ABS_GT = "ABS_GT"
    CROSS_ABOVE = "CROSS_ABOVE"
    CROSS_BELOW = "CROSS_BELOW"


@dataclass(frozen=True)
class ConditionSpec:
    feature_id: str
    operator: ConditionOperator
    value: float | None = None
    second_value: float | None = None
    value_param: str | None = None
    second_value_param: str | None = None

    def __post_init__(self) -> None:
        if not str(self.feature_id).strip():
            raise ValueError("feature_id is required")
        if self.operator is ConditionOperator.BETWEEN and self.second_value is None and self.second_value_param is None:
            raise ValueError("BETWEEN requires an upper bound")
        if self.value is None and self.value_param is None:
            raise ValueError("condition requires value or value_param")

    def resolve(self, params: Mapping[str, Any]) -> tuple[float, float | None]:
        first = self.value if self.value_param is None else params[self.value_param]
        second = self.second_value if self.second_value_param is None else params[self.second_value_param]
        return float(first), None if second is None else float(second)


@dataclass(frozen=True)
class StopSpec:
    method: str
    atr_multiple: float | None = None
    percent_floor: float | None = None
    structural_lookback: int | None = None

    def __post_init__(self) -> None:
        if self.atr_multiple is not None and self.atr_multiple <= 0:
            raise ValueError("atr_multiple must be positive")
        if self.percent_floor is not None and not 0 < self.percent_floor < 1:
            raise ValueError("percent_floor must be in (0,1)")


@dataclass(frozen=True)
class SizingSpec:
    method: str = "RISK_BUDGET_THEN_PORTFOLIO"
    base_risk_pct: float = 0.007
    max_risk_pct: float = 0.011
    volatility_target: float | None = 0.15
    whole_shares: bool = True
    leverage_allowed: bool = False

    def __post_init__(self) -> None:
        if not 0 < self.base_risk_pct <= self.max_risk_pct <= 0.011:
            raise ValueError("v2.32 risk envelope must remain <= 1.10% per trade")
        if self.leverage_allowed:
            raise ValueError("v2.32 strategy DNA cannot allow leverage")


@dataclass(frozen=True)
class HorizonSpec:
    minimum_bars: int
    target_bars: int
    maximum_bars: int
    signal_expiry_bars: int

    def __post_init__(self) -> None:
        if not (1 <= self.minimum_bars <= self.target_bars <= self.maximum_bars):
            raise ValueError("invalid holding horizon")
        if not 1 <= self.signal_expiry_bars <= self.maximum_bars:
            raise ValueError("invalid signal expiry")


@dataclass(frozen=True)
class StrategyDNA:
    family: str
    variant_name: str
    universe_id: str
    primary_timeframe: str
    regime_allowlist: tuple[str, ...]
    setup_features: tuple[str, ...]
    entry_conditions: tuple[ConditionSpec, ...]
    filter_conditions: tuple[ConditionSpec, ...]
    exit_conditions: tuple[ConditionSpec, ...]
    stop: StopSpec
    sizing: SizingSpec
    horizon: HorizonSpec
    parameters: Mapping[str, Any] = field(default_factory=dict)
    rationale: str = ""
    source_engine: str = "strategy_generator_v2_32"
    research_stage: str = "GENERATED_RESEARCH"
    research_compliance_gate_applied: bool = False
    execution_authority: str = EXECUTION_AUTHORITY_NONE

    def __post_init__(self) -> None:
        if not self.family or not self.variant_name or not self.universe_id:
            raise ValueError("family, variant_name and universe_id are required")
        if self.primary_timeframe not in {"15m", "1h", "2h", "4h", "1d"}:
            raise ValueError("unsupported primary timeframe")
        if not self.setup_features:
            raise ValueError("strategy requires setup features")
        if not self.entry_conditions:
            raise ValueError("strategy requires entry conditions")
        if self.research_compliance_gate_applied:
            raise ValueError("v2.32 research generation must not apply compliance gate")
        if self.execution_authority != EXECUTION_AUTHORITY_NONE:
            raise ValueError("strategy DNA cannot grant execution authority")
        object.__setattr__(self, "setup_features", tuple(dict.fromkeys(self.setup_features)))
        object.__setattr__(self, "regime_allowlist", tuple(dict.fromkeys(self.regime_allowlist)))
        object.__setattr__(self, "parameters", dict(sorted(dict(self.parameters).items())))

    @property
    def all_feature_ids(self) -> tuple[str, ...]:
        values = list(self.setup_features)
        for condition in (*self.entry_conditions, *self.filter_conditions, *self.exit_conditions):
            values.append(condition.feature_id)
        return tuple(dict.fromkeys(values))

    @property
    def complexity(self) -> int:
        return len(self.entry_conditions) + len(self.filter_conditions) + len(self.exit_conditions)

    def canonical_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("entry_conditions", "filter_conditions", "exit_conditions"):
            for row in payload[key]:
                row["operator"] = row["operator"].value if isinstance(row["operator"], ConditionOperator) else str(row["operator"])
        payload["schema"] = SCHEMA
        return payload

    @property
    def dna_id(self) -> str:
        raw = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    def as_dict(self) -> dict[str, Any]:
        payload = self.canonical_payload()
        payload["dna_id"] = self.dna_id
        return payload


__all__ = [
    "ConditionOperator",
    "ConditionSpec",
    "EXECUTION_AUTHORITY_NONE",
    "HorizonSpec",
    "SCHEMA",
    "SizingSpec",
    "StopSpec",
    "StrategyDNA",
]
