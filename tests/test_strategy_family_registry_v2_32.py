from stocks.research.strategy_family_registry_v2_32 import family_registry


def test_family_registry_is_broad_and_distinct():
    rows = family_registry()
    assert len(rows) >= 15
    assert len({x.family for x in rows}) == len(rows)
    assert all(x.primary_timeframe == "1h" for x in rows)
    assert all(x.max_complexity >= 4 for x in rows)
