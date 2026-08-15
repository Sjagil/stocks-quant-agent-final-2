from pathlib import Path

from stocks.research.dynamic_universe_generalization import build_universe_plan, discover_interval_sources


def test_source_discovery_prefers_first_canonical_directory(tmp_path: Path):
    first = tmp_path / "data/canonical/provider_fabric"
    second = tmp_path / "data/adjusted"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    (first / "XYZ_1h.parquet").touch()
    (second / "XYZ_1h.parquet").touch()
    sources = discover_interval_sources(tmp_path, "1h")
    assert sources["XYZ"] == first / "XYZ_1h.parquet"


def test_universe_plan_separates_seen_and_unseen(tmp_path: Path):
    fabric = tmp_path / "data/canonical/provider_fabric"
    fabric.mkdir(parents=True)
    (fabric / "AAPL_1h.parquet").touch()
    (fabric / "XYZ_1h.parquet").touch()
    plan = build_universe_plan(tmp_path, development_symbols={"AAPL"})
    rows = {row.symbol: row for row in plan.itertuples(index=False)}
    assert rows["AAPL"].eligible_unseen_1h is False
    assert rows["XYZ"].eligible_unseen_1h is True
