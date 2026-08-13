from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PortfolioWeightChallenge:
    engine: str
    model: str
    weights: dict[str, float]
    gross_weight: float
    net_weight: float
    long_only: bool
    observations: int

    def to_dict(self) -> dict:
        return asdict(self)


def _returns_from_prices(
    prices: pd.DataFrame,
) -> pd.DataFrame:
    if prices.empty:
        raise ValueError(
            "prices cannot be empty"
        )

    work = (
        prices
        .sort_index()
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
    )

    returns = (
        work
        .pct_change(
            fill_method=None
        )
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .dropna()
    )

    if len(returns) < 60:
        raise ValueError(
            "at least 60 complete return "
            "observations are required"
        )

    if returns.shape[1] < 2:
        raise ValueError(
            "at least two assets are required"
        )

    return returns


def skfolio_weight_challengers(
    prices: pd.DataFrame,
) -> list[PortfolioWeightChallenge]:
    from skfolio.optimization import (
        EqualWeighted,
        HierarchicalRiskParity,
        InverseVolatility,
        RiskBudgeting,
    )

    returns = _returns_from_prices(
        prices
    )

    models = {
        "equal_weight": EqualWeighted(),
        "inverse_volatility": (
            InverseVolatility()
        ),
        "risk_budgeting": (
            RiskBudgeting()
        ),
        "hrp": (
            HierarchicalRiskParity()
        ),
    }

    rows: list[
        PortfolioWeightChallenge
    ] = []

    for name, model in models.items():
        model.fit(
            returns
        )

        values = np.asarray(
            model.weights_,
            dtype=float,
        ).reshape(-1)

        if len(values) != len(
            returns.columns
        ):
            raise RuntimeError(
                f"{name}: unexpected "
                "weight vector length"
            )

        weights = {
            str(symbol): float(weight)
            for symbol, weight
            in zip(
                returns.columns,
                values,
                strict=True,
            )
        }

        gross = float(
            np.abs(values).sum()
        )

        net = float(
            values.sum()
        )

        rows.append(
            PortfolioWeightChallenge(
                engine="skfolio",
                model=name,
                weights=weights,
                gross_weight=gross,
                net_weight=net,
                long_only=bool(
                    np.all(
                        values
                        >= -1e-10
                    )
                ),
                observations=len(
                    returns
                ),
            )
        )

    return rows
