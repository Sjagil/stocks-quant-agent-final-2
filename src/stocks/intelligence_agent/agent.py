from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from .allocator import ConstrainedAllocator
from .config import AgentConfig
from .indicators import score_latest, technical_features
from .models import AssetClass, AssetView, NewsArticle, NewsSignal, PortfolioPlan
from .nlp.engine import FinancialNLP
from .scoring import aggregate_news, build_asset_view


class MarketIntelligenceAgent:
    """News + indicators + allocator orchestrator.

    It intentionally exposes no order placement method. The output is a
    PortfolioPlan that an existing risk/execution subsystem may accept or reject.
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig()
        self.config.assert_safe_agent_mode()
        self.nlp = FinancialNLP(
            model_name=self.config.finbert_model,
            half_life_hours=self.config.news_half_life_hours,
        )
        self.allocator = ConstrainedAllocator(self.config)

    @property
    def execution_authority(self) -> str:
        return "NONE"

    def analyze_news(
        self,
        articles: list[NewsArticle],
        *,
        symbol_aliases: dict[str, list[str]],
        source_quality: dict[str, float] | None = None,
        now: datetime | None = None,
    ) -> list[NewsSignal]:
        now = now or datetime.now(timezone.utc)
        result: list[NewsSignal] = []
        source_quality = source_quality or {}
        for article in sorted(articles, key=lambda a: a.published_at):
            result.extend(
                self.nlp.classify_article(
                    article,
                    symbol_aliases=symbol_aliases,
                    source_quality=source_quality.get(article.source, 0.75),
                    now=now,
                )
            )
        return result

    def build_views(
        self,
        *,
        market_data: dict[str, pd.DataFrame],
        asset_classes: dict[str, AssetClass],
        news_signals: list[NewsSignal],
        macro_scores: dict[str, float] | None = None,
        risk_scores: dict[str, float] | None = None,
    ) -> list[AssetView]:
        news = aggregate_news(news_signals)
        macro_scores = macro_scores or {}
        risk_scores = risk_scores or {}
        views: list[AssetView] = []
        for symbol, frame in market_data.items():
            if len(frame) < 60:
                continue
            features = technical_features(frame)
            technical = score_latest(features.dropna(how="all"))
            news_score, news_conf = news.get(symbol, (0.0, 0.0))
            views.append(
                build_asset_view(
                    symbol=symbol,
                    asset_class=asset_classes[symbol],
                    technical_score=technical,
                    news_score=news_score,
                    news_confidence=news_conf,
                    macro_score=macro_scores.get(symbol, 0.0),
                    risk_score=risk_scores.get(symbol, 0.0),
                )
            )
        return views

    def plan(
        self,
        *,
        views: list[AssetView],
        covariance: pd.DataFrame,
        current_weights: dict[str, float],
        equity: float,
        risk_flags: list[str] | None = None,
    ) -> PortfolioPlan:
        allocation = self.allocator.allocate(
            views=views,
            covariance=covariance,
            current_weights=current_weights,
            equity=equity,
        )
        return PortfolioPlan(
            created_at=datetime.now(timezone.utc),
            equity=equity,
            cash_weight=allocation.cash_weight,
            targets=allocation.targets,
            execution_authority="NONE",
            risk_flags=tuple(risk_flags or ()),
            metadata={
                "solver_status": allocation.solver_status,
                "max_global_open_risk": self.config.max_global_open_risk,
                "live_trading_allowed_env": self.config.live_trading_allowed,
                "ibkr_read_only_env": self.config.ibkr_read_only,
            },
        )
