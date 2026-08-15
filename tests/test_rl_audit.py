import json
from pathlib import Path

from stocks.rl.audit import (
    audit_experiment,
)


def test_rl_audit_applies_drawdown_gate(
    tmp_path: Path,
) -> None:
    payload = {
        "algorithm": "SAC",
        "symbol": "TEST",
        "timeframe": "1h",
        "folds": [
            {
                "fold": 1,
                "selected_seed": 11,
                "selected_test": {
                    "total_return": 0.10,
                    "sharpe": 1.0,
                    "max_drawdown": 0.20,
                    "trades": 20,
                },
                "buy_hold_test": {
                    "total_return": 0.05,
                    "sharpe": 0.5,
                    "max_drawdown": 0.25,
                },
            },
            {
                "fold": 2,
                "selected_seed": 29,
                "selected_test": {
                    "total_return": 0.08,
                    "sharpe": 0.8,
                    "max_drawdown": 0.10,
                    "trades": 15,
                },
                "buy_hold_test": {
                    "total_return": 0.04,
                    "sharpe": 0.4,
                    "max_drawdown": 0.15,
                },
            },
        ],
    }

    path = (
        tmp_path
        / "experiment.json"
    )

    path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    audit = audit_experiment(
        path,
        maximum_drawdown=0.15,
    )

    assert (
        audit.drawdown_gate
        is False
    )

    assert (
        audit.promotion_candidate
        is False
    )

    assert (
        audit.beat_buy_hold_return_ratio
        == 1.0
    )
