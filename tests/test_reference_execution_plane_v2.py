import numpy as np
import pandas as pd

from stocks.capabilities import (
    CapabilityRegistry,
)
from stocks.research.engine_artifacts import (
    EngineArtifact,
)
from stocks.research.reference_actions import (
    ReferenceActionRegistry,
)
from stocks.research.skfolio_challenger import (
    skfolio_weight_challengers,
)


def test_all_reference_engines_have_actions() -> None:
    capabilities = (
        CapabilityRegistry.load(
            "config/capabilities.yaml"
        )
    )

    actions = (
        ReferenceActionRegistry.load(
            "config/reference_actions.yaml",
            capabilities=capabilities,
        )
    )

    assert len(
        capabilities.names()
    ) == 13

    assert (
        actions.summary()[
            "engine_count"
        ]
        == 13
    )


def test_research_artifact_is_execution_neutral() -> None:
    artifact = EngineArtifact(
        engine="qlib",
        stage="predictive_modeling",
        artifact_kind="prediction",
        hypothesis_id="ALPHA-TEST",
        symbols=("AAPL",),
        timeframes=("1h",),
    )

    assert (
        artifact.execution_authority
        == "NONE"
    )

    assert (
        artifact.broker_order_calls
        == 0
    )


def test_skfolio_challengers_generate_weights() -> None:
    rng = np.random.default_rng(
        20260813
    )

    returns = pd.DataFrame(
        rng.normal(
            loc=0.0003,
            scale=0.01,
            size=(300, 4),
        ),
        columns=[
            "AAPL",
            "AMD",
            "GLD",
            "SPY",
        ],
    )

    prices = (
        100.0
        * (1.0 + returns)
        .cumprod()
    )

    rows = (
        skfolio_weight_challengers(
            prices
        )
    )

    assert {
        row.model
        for row in rows
    } == {
        "equal_weight",
        "inverse_volatility",
        "risk_budgeting",
        "hrp",
    }

    for row in rows:
        assert row.long_only
        assert abs(
            row.net_weight - 1.0
        ) < 1e-6
