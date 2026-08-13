from pathlib import Path

from stocks.research import AlphaFactory, AlphaHypothesis


ROOT = Path(__file__).resolve().parents[1]


def test_plan_routes_through_full_research_pipeline() -> None:
    factory = AlphaFactory(ROOT)
    hypothesis = AlphaHypothesis(
        family="momentum_breakout",
        thesis="Test whether cross-sectional momentum improves breakout expectancy.",
        symbols=("SPY", "QQQ", "AMD"),
    )

    plan = factory.create_plan(hypothesis)

    assert plan.hypothesis_id.startswith("ALPHA-")
    assert plan.execution_authority == "NONE"
    assert {task.engine for task in plan.tasks} == set(
        factory.capabilities.names()
    )


def test_default_active_swing_timeframes_are_complete() -> None:
    hypothesis = AlphaHypothesis(
        family="active_swing",
        thesis="Example",
        symbols=("SPY",),
    )
    assert hypothesis.timeframes == (
        "15m",
        "1h",
        "2h",
        "4h",
        "1d",
        "1w",
    )
