from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Mapping
import math
import pandas as pd

AUTHORITY_NONE = "NONE"

class AssetKindV235(str, Enum):
    STOCK = "STOCK"
    ETF = "ETF"
    COMMODITY = "COMMODITY"
    COMMODITY_ETF = "COMMODITY_ETF"

def _finite_mapping(values: Mapping[str, float] | None) -> dict[str, float]:
    result: dict[str, float] = {}
    for key, raw in (values or {}).items():
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError(f"non-finite exposure for {key}")
        if abs(value) > 10.0:
            raise ValueError(f"unreasonable exposure magnitude for {key}: {value}")
        result[str(key).strip().upper()] = value
    return result

@dataclass(frozen=True)
class InstrumentExposureProfile:
    symbol: str
    asset_kind: AssetKindV235
    sector: str = "UNKNOWN"
    industry: str = "UNKNOWN"
    country: str = "UNKNOWN"
    currency: str = "UNKNOWN"
    factor_exposures: Mapping[str, float] = field(default_factory=dict)
    commodity_exposures: Mapping[str, float] = field(default_factory=dict)
    data_asof: pd.Timestamp | str | None = None
    source: str = "UNKNOWN"
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol is required")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "sector", str(self.sector or "UNKNOWN").strip().upper())
        object.__setattr__(self, "industry", str(self.industry or "UNKNOWN").strip().upper())
        object.__setattr__(self, "country", str(self.country or "UNKNOWN").strip().upper())
        object.__setattr__(self, "currency", str(self.currency or "UNKNOWN").strip().upper())
        object.__setattr__(self, "factor_exposures", _finite_mapping(self.factor_exposures))
        object.__setattr__(self, "commodity_exposures", _finite_mapping(self.commodity_exposures))
        if self.data_asof is not None:
            ts = pd.Timestamp(self.data_asof)
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            object.__setattr__(self, "data_asof", ts)
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("exposure profile cannot grant execution authority")

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["asset_kind"] = self.asset_kind.value
        if self.data_asof is not None:
            payload["data_asof"] = pd.Timestamp(self.data_asof).isoformat()
        return payload

@dataclass(frozen=True)
class ExposurePolicyV235:
    max_sector_weight: float = 0.35
    max_industry_weight: float = 0.25
    max_country_weight: float = 0.80
    max_currency_weight: float = 0.90
    max_single_commodity_weight: float = 0.25
    max_unknown_lookthrough_weight: float = 0.15
    max_pairwise_etf_overlap: float = 0.70
    max_abs_factor_exposure: Mapping[str, float] = field(default_factory=lambda: {
        "MARKET": 1.25,
        "SIZE": 0.75,
        "VALUE": 0.75,
        "MOMENTUM": 0.75,
        "QUALITY": 0.75,
        "LOW_VOL": 0.75,
        "GROWTH": 0.75,
    })
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        for name in (
            "max_sector_weight","max_industry_weight","max_country_weight",
            "max_currency_weight","max_single_commodity_weight",
            "max_unknown_lookthrough_weight","max_pairwise_etf_overlap",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0,1]")
        factor_caps = _finite_mapping(self.max_abs_factor_exposure)
        if any(value <= 0 for value in factor_caps.values()):
            raise ValueError("factor exposure caps must be positive")
        object.__setattr__(self, "max_abs_factor_exposure", factor_caps)
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("exposure policy cannot grant execution authority")

@dataclass(frozen=True)
class ExposureConstraintResult:
    status: str
    blockers: tuple[str, ...]
    diagnostics: Mapping[str, object]
    execution_authority: str = AUTHORITY_NONE

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

__all__ = [
    "AUTHORITY_NONE","AssetKindV235","ExposureConstraintResult",
    "ExposurePolicyV235","InstrumentExposureProfile",
]
