import numpy as np
import pandas as pd

from stocks.research.fast_discovery import (
    optuna_ma_search,
    vectorbt_ma_screen,
)


def trending_frame(rows: int = 400) -> pd.DataFrame:
    index = pd.date_range(
        "2024-01-01",
        periods=rows,
        freq="D",
        tz="UTC",
    )

    close = (
        100
        + np.linspace(0, 50, rows)
        + np.sin(np.arange(rows) / 8)
    )

    return pd.DataFrame(
        {
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(rows, 1_000_000.0),
        },
        index=index,
    )


def test_vectorbt_screen_returns_ranked_candidates() -> None:
    result = vectorbt_ma_screen(trending_frame())

    assert result
    assert result[0].engine == "vectorbt"
    assert result[0].fast_window < result[0].slow_window


def test_optuna_keeps_test_out_of_optimization() -> None:
    result = optuna_ma_search(
        trending_frame(),
        n_trials=5,
    )

    assert result["engine"] == "optuna"
    assert result["test_used_for_optimization"] is False
    assert "test" in result["metrics"]
