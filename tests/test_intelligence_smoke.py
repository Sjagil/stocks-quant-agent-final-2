import numpy as np
import pandas as pd

from stocks.intelligence_agent import AgentConfig, AssetClass, MarketIntelligenceAgent


def test_agent_builds_view_without_execution_authority():
    idx = pd.date_range("2025-01-01", periods=250, freq="D", tz="UTC")
    close = pd.Series(np.linspace(100, 150, len(idx)), index=idx)
    frame = pd.DataFrame({
        "open": close * 0.999,
        "high": close * 1.01,
        "low": close * 0.99,
        "close": close,
        "volume": np.linspace(1000, 3000, len(idx)),
    }, index=idx)
    agent = MarketIntelligenceAgent(AgentConfig())
    views = agent.build_views(
        market_data={"NVDA.US": frame},
        asset_classes={"NVDA.US": AssetClass.STOCK},
        news_signals=[],
    )
    assert len(views) == 1
    assert agent.execution_authority == "NONE"
