from stocks.research.strategy_sources import strategy_sources


def test_internal_strategy_files_are_registered() -> None:
    sources = {
        item.name: item
        for item in strategy_sources()
    }

    assert "gex_rsi2_bollinger_orderflow" in sources
    assert "strategy_combo_lab_v2" in sources

    assert sources[
        "gex_rsi2_bollinger_orderflow"
    ].research_only is True

    assert sources[
        "strategy_combo_lab_v2"
    ].research_only is True
