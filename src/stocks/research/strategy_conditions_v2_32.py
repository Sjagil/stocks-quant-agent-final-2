from __future__ import annotations

import numpy as np
import pandas as pd

from .strategy_dna_v2_32 import ConditionOperator, ConditionSpec


def evaluate_condition(frame: pd.DataFrame, condition: ConditionSpec, params: dict[str, object]) -> pd.Series:
    if condition.feature_id not in frame.columns:
        raise ValueError(f"feature missing from panel: {condition.feature_id}")
    values = pd.to_numeric(frame[condition.feature_id], errors="coerce")
    first, second = condition.resolve(params)
    op = condition.operator
    if op is ConditionOperator.GT:
        mask = values > first
    elif op is ConditionOperator.GE:
        mask = values >= first
    elif op is ConditionOperator.LT:
        mask = values < first
    elif op is ConditionOperator.LE:
        mask = values <= first
    elif op is ConditionOperator.ABS_GT:
        mask = values.abs() > first
    elif op is ConditionOperator.BETWEEN:
        assert second is not None
        low, high = sorted((first, second))
        mask = values.between(low, high, inclusive="both")
    elif op is ConditionOperator.CROSS_ABOVE:
        mask = (values > first) & (values.shift(1) <= first)
    elif op is ConditionOperator.CROSS_BELOW:
        mask = (values < first) & (values.shift(1) >= first)
    else:  # pragma: no cover
        raise ValueError(f"unsupported condition operator: {op}")
    return mask.fillna(False).astype(bool)


def evaluate_conditions(
    frame: pd.DataFrame,
    conditions: tuple[ConditionSpec, ...],
    params: dict[str, object],
) -> pd.Series:
    if not conditions:
        return pd.Series(True, index=frame.index, dtype=bool)
    result = pd.Series(True, index=frame.index, dtype=bool)
    for condition in conditions:
        result &= evaluate_condition(frame, condition, params)
    return result.astype(bool)


def evaluate_strategy_panel(frame: pd.DataFrame, dna) -> pd.DataFrame:
    entry = evaluate_conditions(frame, dna.entry_conditions, dict(dna.parameters))
    filters = evaluate_conditions(frame, dna.filter_conditions, dict(dna.parameters))
    exits = evaluate_conditions(frame, dna.exit_conditions, dict(dna.parameters))
    output = pd.DataFrame(index=frame.index)
    output["entry"] = (entry & filters).astype(bool)
    output["exit"] = exits.astype(bool)
    output["signal"] = np.where(output["entry"], 1, np.where(output["exit"], -1, 0)).astype(np.int8)
    return output


__all__ = ["evaluate_condition", "evaluate_conditions", "evaluate_strategy_panel"]
