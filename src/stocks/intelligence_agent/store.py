from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import PortfolioPlan


_SCHEMA = """
CREATE TABLE IF NOT EXISTS intelligence_portfolio_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    equity REAL NOT NULL,
    cash_weight REAL NOT NULL,
    execution_authority TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
"""


class DecisionStore:
    def __init__(self, db_url: str) -> None:
        if not db_url.startswith("sqlite:///"):
            raise ValueError("This addon currently supports sqlite:/// DB_URL only")
        path = Path(db_url.removeprefix("sqlite:///"))
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(_SCHEMA)
        self.connection.commit()

    def append_plan(self, plan: PortfolioPlan) -> None:
        payload = {
            "targets": [
                {
                    "symbol": t.symbol,
                    "asset_class": t.asset_class.value,
                    "current_weight": t.current_weight,
                    "target_weight": t.target_weight,
                    "delta_weight": t.delta_weight,
                    "target_notional": t.target_notional,
                    "action": t.action,
                    "confidence": t.confidence,
                    "rationale": list(t.rationale),
                }
                for t in plan.targets
            ],
            "risk_flags": list(plan.risk_flags),
            "metadata": plan.metadata,
        }
        self.connection.execute(
            "INSERT INTO intelligence_portfolio_plans(created_at,equity,cash_weight,execution_authority,payload_json) VALUES(?,?,?,?,?)",
            (plan.created_at.isoformat(), plan.equity, plan.cash_weight, plan.execution_authority, json.dumps(payload, sort_keys=True)),
        )
        self.connection.commit()
