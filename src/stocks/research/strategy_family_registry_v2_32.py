from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .strategy_dna_v2_32 import ConditionOperator as Op, ConditionSpec, HorizonSpec, SizingSpec, StopSpec


@dataclass(frozen=True)
class StrategyFamilyTemplate:
    family: str
    rationale: str
    setup_features: tuple[str, ...]
    entry_conditions: tuple[ConditionSpec, ...]
    filter_conditions: tuple[ConditionSpec, ...]
    exit_conditions: tuple[ConditionSpec, ...]
    default_parameters: dict[str, Any]
    parameter_space: dict[str, tuple[Any, ...]]
    regime_allowlist: tuple[str, ...]
    horizon: HorizonSpec
    stop: StopSpec = StopSpec("ATR_WITH_PERCENT_FLOOR", atr_multiple=2.0, percent_floor=0.02)
    sizing: SizingSpec = SizingSpec()
    universe_id: str = "LIQUID_US_EQUITIES"
    primary_timeframe: str = "1h"
    max_complexity: int = 8


def C(feature: str, op: Op, *, value=None, param=None, second=None, second_param=None) -> ConditionSpec:
    return ConditionSpec(feature, op, value=value, value_param=param, second_value=second, second_value_param=second_param)


def family_registry() -> tuple[StrategyFamilyTemplate, ...]:
    H = HorizonSpec
    base_regimes = ("BULL_TREND", "NORMAL", "RISK_ON")
    return (
        StrategyFamilyTemplate(
            "trend_quality_breakout",
            "Persistent log-price trend with statistical quality, directional efficiency and controlled volatility expansion.",
            ("trend_regression_slope_20", "trend_regression_r2_20", "trend_regression_tstat_20", "kaufman_efficiency_20", "volatility_expansion_10_40"),
            (C("trend_regression_slope_20", Op.GT, param="slope_min"), C("trend_regression_tstat_20", Op.GT, param="tstat_min")),
            (C("trend_regression_r2_20", Op.GT, param="r2_min"), C("kaufman_efficiency_20", Op.GT, param="er_min"), C("volatility_expansion_10_40", Op.LT, param="vol_max")),
            (C("trend_regression_slope_20", Op.CROSS_BELOW, value=0.0),),
            {"slope_min": 0.0, "tstat_min": 1.5, "r2_min": 0.25, "er_min": 0.25, "vol_max": 1.5},
            {"tstat_min": (1.0, 1.5, 2.0), "r2_min": (0.15, 0.25, 0.40), "er_min": (0.20, 0.30, 0.40), "vol_max": (0.8, 1.2, 1.8)},
            base_regimes, H(4, 20, 80, 4),
        ),
        StrategyFamilyTemplate(
            "risk_adjusted_momentum",
            "Momentum normalized by realized risk, filtered by trend significance and volatility state.",
            ("risk_adjusted_momentum_20", "trend_regression_tstat_20", "volatility_expansion_10_40"),
            (C("risk_adjusted_momentum_20", Op.GT, param="momentum_min"),),
            (C("trend_regression_tstat_20", Op.GT, param="tstat_min"), C("volatility_expansion_10_40", Op.LT, param="vol_max")),
            (C("risk_adjusted_momentum_20", Op.CROSS_BELOW, value=0.0),),
            {"momentum_min": 0.15, "tstat_min": 1.0, "vol_max": 1.5},
            {"momentum_min": (0.05, 0.15, 0.30, 0.50), "tstat_min": (0.5, 1.0, 1.5), "vol_max": (0.8, 1.2, 1.8)},
            base_regimes, H(4, 20, 63, 4),
        ),
        StrategyFamilyTemplate(
            "relative_strength_trend",
            "Positive benchmark-relative performance that is supported by persistent trend quality.",
            ("relative_strength_20", "trend_regression_slope_20", "trend_regression_r2_20"),
            (C("relative_strength_20", Op.GT, param="rs_min"),),
            (C("trend_regression_slope_20", Op.GT, value=0.0), C("trend_regression_r2_20", Op.GT, param="r2_min")),
            (C("relative_strength_20", Op.CROSS_BELOW, value=0.0),),
            {"rs_min": 0.0, "r2_min": 0.20},
            {"rs_min": (0.0, 0.25, 0.50), "r2_min": (0.10, 0.20, 0.35)},
            base_regimes, H(8, 30, 100, 6),
        ),
        StrategyFamilyTemplate(
            "cross_sectional_momentum",
            "Select upper-tail cross-sectional momentum while requiring sector-neutral confirmation.",
            ("cross_sectional_momentum_rank_20", "sector_neutral_momentum_z_20", "trend_regression_slope_20"),
            (C("cross_sectional_momentum_rank_20", Op.GT, param="rank_min"),),
            (C("sector_neutral_momentum_z_20", Op.GT, param="sector_z_min"), C("trend_regression_slope_20", Op.GT, value=0.0)),
            (C("cross_sectional_momentum_rank_20", Op.CROSS_BELOW, param="rank_exit"),),
            {"rank_min": 0.75, "sector_z_min": 0.25, "rank_exit": 0.50},
            {"rank_min": (0.65, 0.75, 0.85, 0.90), "sector_z_min": (0.0, 0.25, 0.50, 0.75), "rank_exit": (0.40, 0.50, 0.60)},
            base_regimes, H(8, 40, 120, 8),
        ),
        StrategyFamilyTemplate(
            "sector_neutral_momentum",
            "Momentum after removing sector-level crowding, with residual return confirmation.",
            ("sector_neutral_momentum_z_20", "residual_momentum_20", "rolling_market_beta_60"),
            (C("sector_neutral_momentum_z_20", Op.GT, param="sector_z_min"), C("residual_momentum_20", Op.GT, param="residual_min")),
            (C("rolling_market_beta_60", Op.BETWEEN, param="beta_min", second_param="beta_max"),),
            (C("sector_neutral_momentum_z_20", Op.CROSS_BELOW, value=0.0),),
            {"sector_z_min": 0.50, "residual_min": 0.0, "beta_min": 0.30, "beta_max": 1.50},
            {"sector_z_min": (0.25, 0.50, 0.75, 1.0), "residual_min": (0.0, 0.01, 0.03), "beta_max": (1.0, 1.25, 1.50)},
            base_regimes, H(8, 40, 120, 8),
        ),
        StrategyFamilyTemplate(
            "residual_momentum",
            "Trade idiosyncratic momentum after factor projection instead of raw market beta.",
            ("residual_momentum_20", "rolling_market_beta_60", "trend_regression_r2_20"),
            (C("residual_momentum_20", Op.GT, param="residual_min"),),
            (C("rolling_market_beta_60", Op.BETWEEN, param="beta_min", second_param="beta_max"), C("trend_regression_r2_20", Op.GT, param="r2_min")),
            (C("residual_momentum_20", Op.CROSS_BELOW, value=0.0),),
            {"residual_min": 0.01, "beta_min": 0.20, "beta_max": 1.60, "r2_min": 0.10},
            {"residual_min": (0.0, 0.01, 0.03, 0.05), "beta_max": (1.0, 1.3, 1.6), "r2_min": (0.05, 0.10, 0.20)},
            base_regimes, H(8, 40, 120, 8),
        ),
        StrategyFamilyTemplate(
            "low_beta_relative_strength",
            "Positive relative strength with deliberately bounded systematic market exposure.",
            ("relative_strength_20", "rolling_market_beta_60", "trend_regression_slope_20"),
            (C("relative_strength_20", Op.GT, param="rs_min"),),
            (C("rolling_market_beta_60", Op.LT, param="beta_max"), C("trend_regression_slope_20", Op.GT, value=0.0)),
            (C("relative_strength_20", Op.CROSS_BELOW, value=0.0),),
            {"rs_min": 0.0, "beta_max": 0.90},
            {"rs_min": (0.0, 0.20, 0.40), "beta_max": (0.70, 0.90, 1.10)},
            ("NORMAL", "RISK_OFF", "BULL_TREND"), H(8, 40, 120, 8),
        ),
        StrategyFamilyTemplate(
            "earnings_revision_momentum",
            "PIT earnings-estimate revisions aligned with price momentum.",
            ("eps_revision", "risk_adjusted_momentum_20", "trend_regression_slope_20"),
            (C("eps_revision", Op.GT, param="revision_min"), C("risk_adjusted_momentum_20", Op.GT, param="momentum_min")),
            (C("trend_regression_slope_20", Op.GT, value=0.0),),
            (C("risk_adjusted_momentum_20", Op.CROSS_BELOW, value=0.0),),
            {"revision_min": 0.0, "momentum_min": 0.05},
            {"revision_min": (0.0, 0.10, 0.25, 0.50), "momentum_min": (0.0, 0.10, 0.25)},
            base_regimes, H(8, 40, 120, 8),
        ),
        StrategyFamilyTemplate(
            "earnings_surprise_continuation",
            "PIT earnings surprise combined with post-event trend continuation rather than surprise alone.",
            ("earnings_surprise", "risk_adjusted_momentum_20", "kaufman_efficiency_20"),
            (C("earnings_surprise", Op.GT, param="surprise_min"),),
            (C("risk_adjusted_momentum_20", Op.GT, param="momentum_min"), C("kaufman_efficiency_20", Op.GT, param="er_min")),
            (C("risk_adjusted_momentum_20", Op.CROSS_BELOW, value=0.0),),
            {"surprise_min": 0.0, "momentum_min": 0.05, "er_min": 0.20},
            {"surprise_min": (0.0, 0.20, 0.50, 1.0), "momentum_min": (0.0, 0.10, 0.25), "er_min": (0.15, 0.25, 0.35)},
            base_regimes, H(4, 30, 100, 6),
        ),
        StrategyFamilyTemplate(
            "quality_momentum",
            "PIT profitability quality combined with price momentum, avoiding static quality-only allocation.",
            ("roic", "fcf_margin", "risk_adjusted_momentum_20"),
            (C("risk_adjusted_momentum_20", Op.GT, param="momentum_min"),),
            (C("roic", Op.GT, param="roic_min"), C("fcf_margin", Op.GT, param="fcf_min")),
            (C("risk_adjusted_momentum_20", Op.CROSS_BELOW, value=0.0),),
            {"momentum_min": 0.05, "roic_min": 0.0, "fcf_min": 0.0},
            {"momentum_min": (0.0, 0.10, 0.25), "roic_min": (-0.25, 0.0, 0.25), "fcf_min": (-0.25, 0.0, 0.25)},
            base_regimes, H(8, 50, 140, 10),
        ),
        StrategyFamilyTemplate(
            "revision_quality_momentum",
            "Estimate revisions backed by quality and sector-neutral price strength.",
            ("eps_revision", "roic", "sector_neutral_momentum_z_20"),
            (C("eps_revision", Op.GT, param="revision_min"), C("sector_neutral_momentum_z_20", Op.GT, param="sector_z_min")),
            (C("roic", Op.GT, param="roic_min"),),
            (C("sector_neutral_momentum_z_20", Op.CROSS_BELOW, value=0.0),),
            {"revision_min": 0.0, "sector_z_min": 0.25, "roic_min": 0.0},
            {"revision_min": (0.0, 0.10, 0.25), "sector_z_min": (0.0, 0.25, 0.50), "roic_min": (-0.25, 0.0, 0.25)},
            base_regimes, H(8, 50, 140, 10),
        ),
        StrategyFamilyTemplate(
            "news_event_momentum",
            "Decayed independent news-event evidence aligned with price trend.",
            ("news_weighted_sentiment", "news_event_intensity", "trend_regression_slope_20"),
            (C("news_weighted_sentiment", Op.GT, param="sentiment_min"), C("news_event_intensity", Op.GT, param="intensity_min")),
            (C("trend_regression_slope_20", Op.GT, value=0.0),),
            (C("news_weighted_sentiment", Op.CROSS_BELOW, value=0.0),),
            {"sentiment_min": 0.10, "intensity_min": 0.05},
            {"sentiment_min": (0.05, 0.10, 0.20, 0.35), "intensity_min": (0.02, 0.05, 0.10, 0.20)},
            base_regimes, H(2, 16, 60, 3),
        ),
        StrategyFamilyTemplate(
            "news_diversity_confirmed_trend",
            "Trend entry only when news evidence is positive and comes from sufficiently diverse independent sources.",
            ("news_weighted_sentiment", "news_source_diversity", "relative_strength_20"),
            (C("news_weighted_sentiment", Op.GT, param="sentiment_min"), C("relative_strength_20", Op.GT, param="rs_min")),
            (C("news_source_diversity", Op.GT, param="diversity_min"),),
            (C("news_weighted_sentiment", Op.CROSS_BELOW, value=0.0),),
            {"sentiment_min": 0.10, "diversity_min": 0.40, "rs_min": 0.0},
            {"sentiment_min": (0.05, 0.10, 0.20), "diversity_min": (0.25, 0.40, 0.60), "rs_min": (0.0, 0.20, 0.40)},
            base_regimes, H(2, 20, 80, 4),
        ),
        StrategyFamilyTemplate(
            "volatility_expansion_momentum",
            "Controlled volatility expansion with positive risk-adjusted momentum and directional efficiency.",
            ("volatility_expansion_10_40", "risk_adjusted_momentum_20", "kaufman_efficiency_20"),
            (C("volatility_expansion_10_40", Op.GT, param="vol_min"), C("risk_adjusted_momentum_20", Op.GT, param="momentum_min")),
            (C("kaufman_efficiency_20", Op.GT, param="er_min"), C("volatility_expansion_10_40", Op.LT, param="vol_max")),
            (C("risk_adjusted_momentum_20", Op.CROSS_BELOW, value=0.0),),
            {"vol_min": 0.05, "vol_max": 1.5, "momentum_min": 0.10, "er_min": 0.20},
            {"vol_min": (0.0, 0.10, 0.25), "vol_max": (0.8, 1.2, 1.8), "momentum_min": (0.05, 0.15, 0.30), "er_min": (0.15, 0.25, 0.35)},
            base_regimes, H(3, 20, 70, 4),
        ),
        StrategyFamilyTemplate(
            "multi_evidence_confluence",
            "Technical trend, PIT earnings revision and decayed news evidence must independently agree.",
            ("trend_regression_tstat_20", "eps_revision", "news_weighted_sentiment"),
            (C("trend_regression_tstat_20", Op.GT, param="tstat_min"), C("eps_revision", Op.GT, param="revision_min"), C("news_weighted_sentiment", Op.GT, param="sentiment_min")),
            (),
            (C("trend_regression_tstat_20", Op.CROSS_BELOW, value=0.0),),
            {"tstat_min": 1.0, "revision_min": 0.0, "sentiment_min": 0.05},
            {"tstat_min": (0.5, 1.0, 1.5), "revision_min": (0.0, 0.10, 0.25), "sentiment_min": (0.0, 0.10, 0.20)},
            base_regimes, H(4, 30, 100, 6),
        ),
        StrategyFamilyTemplate(
            "regime_adaptive_trend",
            "High-quality trend candidate explicitly restricted to trend/risk-on regimes.",
            ("trend_regression_tstat_20", "kaufman_efficiency_20", "risk_adjusted_momentum_20"),
            (C("trend_regression_tstat_20", Op.GT, param="tstat_min"), C("risk_adjusted_momentum_20", Op.GT, param="momentum_min")),
            (C("kaufman_efficiency_20", Op.GT, param="er_min"),),
            (C("trend_regression_tstat_20", Op.CROSS_BELOW, value=0.0),),
            {"tstat_min": 1.5, "momentum_min": 0.10, "er_min": 0.25},
            {"tstat_min": (1.0, 1.5, 2.0), "momentum_min": (0.0, 0.10, 0.25), "er_min": (0.20, 0.30, 0.40)},
            ("BULL_TREND", "RISK_ON"), H(4, 30, 100, 6),
        ),
    )


__all__ = ["StrategyFamilyTemplate", "family_registry"]
