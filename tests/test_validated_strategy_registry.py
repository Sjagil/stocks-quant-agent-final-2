import pandas as pd

from stocks.research.validated_strategy_registry import (
    build_validated_strategy_registry,
)


def test_registry_merges_validation_layers(
    tmp_path,
):
    factory_root = (
        tmp_path
        / "artifacts"
        / "research_runtime"
        / "strategy_factory_1h"
    )

    pybroker_root = (
        tmp_path
        / "artifacts"
        / "research_runtime"
        / "pybroker_crosscheck"
    )

    market_root = (
        tmp_path
        / "artifacts"
        / "research_runtime"
        / "market_structure_15m_execution"
    )

    factory_root.mkdir(
        parents=True
    )

    pybroker_root.mkdir(
        parents=True
    )

    market_root.mkdir(
        parents=True
    )

    pd.DataFrame(
        [
            {
                "hypothesis_id": "RSI",
                "strategy": (
                    "rsi_threshold_exit"
                ),
                "family": (
                    "mean_reversion"
                ),
                "status": (
                    "STRONG_SURVIVOR"
                ),
                "params_json": "{}",
            },
            {
                "hypothesis_id": "ATR",
                "strategy": (
                    "return_atr_compression"
                ),
                "family": (
                    "volatility_mean_reversion"
                ),
                "status": (
                    "PROVISIONAL_SURVIVOR"
                ),
                "params_json": "{}",
            },
            {
                "hypothesis_id": "MS",
                "strategy": (
                    "market_structure_"
                    "atr_pullback"
                ),
                "family": (
                    "breakout_pullback"
                ),
                "status": (
                    "STRONG_SURVIVOR"
                ),
                "params_json": "{}",
            },
        ]
    ).to_csv(
        factory_root
        / "survivors.csv",
        index=False,
    )

    pd.DataFrame(
        [
            {
                "hypothesis_id": "RSI",
                "crosscheck_status": (
                    "CROSS_ENGINE_VALIDATED"
                ),
                "execution_contract": (
                    "NEXT_OPEN_REPLAY"
                ),
            },
            {
                "hypothesis_id": "ATR",
                "crosscheck_status": (
                    "CROSS_ENGINE_PROVISIONAL"
                ),
                "execution_contract": (
                    "NEXT_OPEN_REPLAY"
                ),
            },
        ]
    ).to_csv(
        pybroker_root
        / "summary.csv",
        index=False,
    )

    pd.DataFrame(
        [
            {
                "hypothesis_id": "MS",
                "status": (
                    "15M_EXECUTION_VALIDATED"
                ),
            }
        ]
    ).to_csv(
        market_root
        / "summary.csv",
        index=False,
    )

    frame, audit = (
        build_validated_strategy_registry(
            tmp_path
        )
    )

    stages = dict(
        zip(
            frame[
                "hypothesis_id"
            ],
            frame[
                "promotion_stage"
            ],
            strict=True,
        )
    )

    assert (
        stages["RSI"]
        == "FINALIST_CANDIDATE"
    )

    assert (
        stages["MS"]
        == "FINALIST_CANDIDATE"
    )

    assert (
        stages["ATR"]
        == "CHALLENGER"
    )

    assert (
        audit[
            "finalist_candidate_count"
        ]
        == 2
    )

    assert (
        audit[
            "live_ready"
        ]
        is False
    )
