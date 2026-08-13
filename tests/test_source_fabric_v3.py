from pathlib import Path

from stocks.providers.contracts import (
    SourceResult,
    SourceState,
)
from stocks.providers.fabric import (
    SourceFabric,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def test_source_result_finishes() -> None:
    result = SourceResult(
        provider="test",
        domain="bars",
        state=SourceState.OK,
    ).finish()

    assert result.completed_at is not None


def test_source_fabric_is_execution_neutral() -> None:
    fabric = SourceFabric(
        ROOT
    )

    assert (
        fabric.project_root
        ==
        ROOT.resolve()
    )


def test_safe_provider_failure_is_captured() -> None:
    result = SourceFabric._safe(
        "test",
        "news",
        lambda:
        (_ for _ in ())
        .throw(
            RuntimeError(
                "boom"
            )
        ),
    )

    assert (
        result.state
        is SourceState.ERROR
    )

    assert "boom" in (
        result.error or ""
    )
