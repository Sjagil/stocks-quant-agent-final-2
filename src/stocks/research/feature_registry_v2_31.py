from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping


class FeatureFamily(str, Enum):
    PRICE = "PRICE"
    TREND = "TREND"
    MOMENTUM = "MOMENTUM"
    VOLATILITY = "VOLATILITY"
    VOLUME_LIQUIDITY = "VOLUME_LIQUIDITY"
    CROSS_SECTIONAL = "CROSS_SECTIONAL"
    FACTOR = "FACTOR"
    FUNDAMENTAL = "FUNDAMENTAL"
    NEWS = "NEWS"
    MACRO = "MACRO"
    REGIME = "REGIME"
    EXECUTION = "EXECUTION"


@dataclass(frozen=True)
class FeatureSpec:
    feature_id: str
    family: FeatureFamily
    description: str
    required_columns: tuple[str, ...] = ()
    lookback_bars: int = 0
    normalization: str = "NONE"
    causal: bool = True
    point_in_time: bool = True
    cross_sectional: bool = False
    tags: tuple[str, ...] = ()
    execution_authority: str = "NONE"

    def __post_init__(self) -> None:
        feature_id = str(self.feature_id).strip()
        if not feature_id:
            raise ValueError("feature_id is required")
        if self.lookback_bars < 0:
            raise ValueError("lookback_bars cannot be negative")
        if not self.causal or not self.point_in_time:
            raise ValueError("v2.31 canonical features must be causal and point-in-time")
        if self.execution_authority != "NONE":
            raise ValueError("feature specs cannot grant execution authority")
        object.__setattr__(self, "feature_id", feature_id)
        object.__setattr__(
            self,
            "required_columns",
            tuple(dict.fromkeys(str(x).strip() for x in self.required_columns if str(x).strip())),
        )
        object.__setattr__(
            self,
            "tags",
            tuple(sorted({str(x).strip().lower() for x in self.tags if str(x).strip()})),
        )

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["family"] = self.family.value
        return payload


class FeatureRegistry:
    def __init__(self, specs: Iterable[FeatureSpec] = ()) -> None:
        self._specs: dict[str, FeatureSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: FeatureSpec) -> None:
        if spec.feature_id in self._specs:
            raise ValueError(f"duplicate feature_id: {spec.feature_id}")
        self._specs[spec.feature_id] = spec

    def get(self, feature_id: str) -> FeatureSpec:
        try:
            return self._specs[str(feature_id)]
        except KeyError as exc:
            raise KeyError(f"unknown feature_id: {feature_id}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._specs))

    def by_family(self, family: FeatureFamily | str) -> tuple[FeatureSpec, ...]:
        value = family if isinstance(family, FeatureFamily) else FeatureFamily(str(family))
        return tuple(spec for spec in self._specs.values() if spec.family is value)

    @property
    def specs(self) -> Mapping[str, FeatureSpec]:
        return MappingProxyType(dict(self._specs))

    def validate_columns(self, feature_id: str, available_columns: Iterable[str]) -> tuple[str, ...]:
        available = {str(x) for x in available_columns}
        return tuple(x for x in self.get(feature_id).required_columns if x not in available)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": "canonical_feature_registry_v2_31",
            "feature_count": len(self._specs),
            "features": [self._specs[key].as_dict() for key in sorted(self._specs)],
            "execution_authority": "NONE",
        }


def default_feature_registry() -> FeatureRegistry:
    specs = (
        FeatureSpec("trend_regression_slope_20", FeatureFamily.TREND, "OLS slope of log close over 20 closed bars", ("close",), 20, "ROBUST_Z", tags=("trend", "regression")),
        FeatureSpec("trend_regression_r2_20", FeatureFamily.TREND, "R-squared of log-price trend over 20 closed bars", ("close",), 20, "ROBUST_Z", tags=("trend", "quality")),
        FeatureSpec("trend_regression_tstat_20", FeatureFamily.TREND, "t-statistic of log-price slope over 20 closed bars", ("close",), 20, "ROBUST_Z", tags=("trend", "significance")),
        FeatureSpec("kaufman_efficiency_20", FeatureFamily.TREND, "Directional efficiency over 20 closed bars", ("close",), 20, "NONE", tags=("trend", "efficiency")),
        FeatureSpec("risk_adjusted_momentum_20", FeatureFamily.MOMENTUM, "20-bar log momentum divided by realized volatility", ("close",), 20, "ROBUST_Z", tags=("momentum", "risk-adjusted")),
        FeatureSpec("relative_strength_20", FeatureFamily.MOMENTUM, "20-bar asset return minus benchmark return", ("close", "benchmark_close"), 20, "CROSS_SECTIONAL_ROBUST_Z", tags=("relative-strength",)),
        FeatureSpec("volatility_expansion_10_40", FeatureFamily.VOLATILITY, "Short/long realized-volatility ratio minus one", ("close",), 40, "ROBUST_Z", tags=("volatility", "expansion")),
        FeatureSpec("cross_sectional_momentum_rank_20", FeatureFamily.CROSS_SECTIONAL, "Cross-sectional percentile rank of 20-bar momentum", ("symbol", "timestamp", "close"), 20, "PERCENTILE_RANK", True, True, True, tags=("cross-sectional", "momentum")),
        FeatureSpec("sector_neutral_momentum_z_20", FeatureFamily.CROSS_SECTIONAL, "Sector-neutral robust z-score of 20-bar momentum", ("symbol", "timestamp", "sector", "close"), 20, "SECTOR_ROBUST_Z", True, True, True, tags=("sector-neutral", "momentum")),
        FeatureSpec("rolling_market_beta_60", FeatureFamily.FACTOR, "Rolling beta to market factor", ("return", "market_return"), 60, "ROBUST_Z", tags=("factor", "beta")),
        FeatureSpec("residual_momentum_20", FeatureFamily.FACTOR, "Compounded residual momentum after factor projection", ("return",), 20, "CROSS_SECTIONAL_ROBUST_Z", tags=("factor", "residual")),
        FeatureSpec("roic", FeatureFamily.FUNDAMENTAL, "NOPAT divided by invested capital using PIT fundamentals", ("nopat", "invested_capital"), 0, "CROSS_SECTIONAL_ROBUST_Z", True, True, True, tags=("quality",)),
        FeatureSpec("fcf_margin", FeatureFamily.FUNDAMENTAL, "Free cash flow divided by revenue", ("free_cash_flow", "revenue"), 0, "CROSS_SECTIONAL_ROBUST_Z", True, True, True, tags=("quality",)),
        FeatureSpec("earnings_surprise", FeatureFamily.FUNDAMENTAL, "PIT actual versus consensus earnings surprise", ("actual_eps", "consensus_eps"), 0, "CROSS_SECTIONAL_ROBUST_Z", True, True, True, tags=("revision", "surprise")),
        FeatureSpec("eps_revision", FeatureFamily.FUNDAMENTAL, "Change in consensus EPS estimate known at decision time", ("eps_estimate", "eps_estimate_prior"), 0, "CROSS_SECTIONAL_ROBUST_Z", True, True, True, tags=("revision",)),
        FeatureSpec("news_weighted_sentiment", FeatureFamily.NEWS, "PIT weighted news/event sentiment with event-specific time decay", (), 0, "ROBUST_Z", tags=("news", "sentiment")),
        FeatureSpec("news_source_diversity", FeatureFamily.NEWS, "Independent source diversity of current news evidence", (), 0, "NONE", tags=("news", "diversity")),
        FeatureSpec("news_event_intensity", FeatureFamily.NEWS, "Decayed weighted event evidence intensity", (), 0, "ROBUST_Z", tags=("news", "event")),
    )
    return FeatureRegistry(specs)


__all__ = ["FeatureFamily", "FeatureRegistry", "FeatureSpec", "default_feature_registry"]
