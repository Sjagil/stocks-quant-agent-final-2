from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ForwardForecastConfig:
    quantiles: tuple[float, ...] = (0.10, 0.50, 0.90)
    learning_rate: float = 0.05
    max_iter: int = 200
    max_leaf_nodes: int = 15
    l2_regularization: float = 1.0
    random_state: int = 28030

    def __post_init__(self) -> None:
        cleaned = tuple(sorted({float(q) for q in self.quantiles}))
        if not cleaned or any(not 0.0 < q < 1.0 for q in cleaned):
            raise ValueError("quantiles must be unique values in (0,1)")
        object.__setattr__(self, "quantiles", cleaned)


class ForwardQuantileForecaster:
    """Research-only mean + quantile forecaster.

    The caller owns temporal splitting. `fit` never performs a random split.
    """

    def __init__(self, config: ForwardForecastConfig | None = None) -> None:
        self.config = config or ForwardForecastConfig()
        self._mean_model = None
        self._quantile_models: dict[float, object] = {}
        self._columns: tuple[str, ...] = ()

    @staticmethod
    def _dependencies():
        try:
            from sklearn.ensemble import HistGradientBoostingRegressor
            from sklearn.impute import SimpleImputer
            from sklearn.pipeline import Pipeline
        except Exception as exc:  # pragma: no cover
            raise ImportError("scikit-learn is required for forward forecasting") from exc
        return HistGradientBoostingRegressor, SimpleImputer, Pipeline

    def _pipeline(self, *, quantile: float | None):
        HGB, Imputer, Pipeline = self._dependencies()
        loss = "squared_error" if quantile is None else "quantile"
        model = HGB(
            loss=loss,
            quantile=quantile,
            learning_rate=self.config.learning_rate,
            max_iter=self.config.max_iter,
            max_leaf_nodes=self.config.max_leaf_nodes,
            l2_regularization=self.config.l2_regularization,
            random_state=self.config.random_state,
        )
        return Pipeline([("imputer", Imputer(strategy="median")), ("model", model)])

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "ForwardQuantileForecaster":
        if not isinstance(features, pd.DataFrame) or features.empty:
            raise ValueError("features must be a non-empty DataFrame")
        y = pd.to_numeric(target, errors="coerce")
        common = features.index.intersection(y.dropna().index)
        if len(common) < 50:
            raise ValueError("need at least 50 labeled training rows")
        x = features.loc[common].apply(pd.to_numeric, errors="coerce")
        y_train = y.loc[common].astype(float)
        self._columns = tuple(x.columns)
        self._mean_model = self._pipeline(quantile=None).fit(x, y_train)
        self._quantile_models = {
            q: self._pipeline(quantile=q).fit(x, y_train)
            for q in self.config.quantiles
        }
        return self

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        if self._mean_model is None or not self._quantile_models:
            raise RuntimeError("forecaster is not fitted")
        x = features.reindex(columns=self._columns).apply(pd.to_numeric, errors="coerce")
        out = pd.DataFrame(index=x.index)
        out["mean"] = self._mean_model.predict(x)
        quantile_columns: list[str] = []
        raw: list[np.ndarray] = []
        for q, model in sorted(self._quantile_models.items()):
            name = f"q{int(round(q * 100)):02d}"
            quantile_columns.append(name)
            raw.append(np.asarray(model.predict(x), dtype=float))
        matrix = np.column_stack(raw)
        matrix.sort(axis=1)  # deterministic no-crossing projection
        for idx, name in enumerate(quantile_columns):
            out[name] = matrix[:, idx]
        out["interval_width"] = out[quantile_columns[-1]] - out[quantile_columns[0]]
        return out
