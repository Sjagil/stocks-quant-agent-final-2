from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProductionStoreV241:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init(self) -> None:
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS kv (
              key TEXT PRIMARY KEY,
              value_json TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS baseline_positions (
              symbol TEXT PRIMARY KEY,
              quantity REAL NOT NULL,
              adopted_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS intents (
              intent_id TEXT PRIMARY KEY,
              symbol TEXT NOT NULL,
              action TEXT NOT NULL,
              quantity INTEGER NOT NULL,
              source TEXT NOT NULL,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
              broker_order_id INTEGER PRIMARY KEY,
              intent_id TEXT NOT NULL,
              role TEXT NOT NULL,
              status TEXT NOT NULL,
              order_ref TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              FOREIGN KEY(intent_id) REFERENCES intents(intent_id)
            );
            CREATE TABLE IF NOT EXISTS fills (
              exec_id TEXT PRIMARY KEY,
              broker_order_id INTEGER,
              intent_id TEXT,
              symbol TEXT NOT NULL,
              side TEXT NOT NULL,
              shares REAL NOT NULL,
              price REAL NOT NULL,
              filled_at TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS daily_equity (
              date_utc TEXT PRIMARY KEY,
              opening_net_liq REAL NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cycles (
              cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
              started_at TEXT NOT NULL,
              finished_at TEXT,
              status TEXT NOT NULL,
              summary_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inactive_counts (
              symbol TEXT PRIMARY KEY,
              count INTEGER NOT NULL,
              updated_at TEXT NOT NULL
            );
            """)

    def set(self, key: str, value: Any) -> None:
        now = utcnow()
        with self.connect() as c:
            c.execute(
                """INSERT INTO kv(key,value_json,updated_at) VALUES(?,?,?)
                   ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,
                   updated_at=excluded.updated_at""",
                (key, json.dumps(value, sort_keys=True, default=str), now),
            )

    def get(self, key: str, default: Any = None) -> Any:
        with self.connect() as c:
            row = c.execute("SELECT value_json FROM kv WHERE key=?", (key,)).fetchone()
        return default if row is None else json.loads(row["value_json"])

    def adopt_baseline(self, positions: dict[str, float]) -> None:
        now = utcnow()
        with self.connect() as c:
            c.execute("DELETE FROM baseline_positions")
            c.executemany(
                "INSERT INTO baseline_positions(symbol,quantity,adopted_at) VALUES(?,?,?)",
                [(s.upper(), float(q), now) for s, q in sorted(positions.items()) if abs(float(q)) > 1e-12],
            )
        self.set("baseline_adopted", True)

    def baseline(self) -> dict[str, float]:
        with self.connect() as c:
            rows = c.execute("SELECT symbol,quantity FROM baseline_positions").fetchall()
        return {r["symbol"]: float(r["quantity"]) for r in rows}

    def claim_intent(self, payload: dict[str, Any]) -> bool:
        now = utcnow()
        try:
            with self.connect() as c:
                c.execute(
                    """INSERT INTO intents(intent_id,symbol,action,quantity,source,status,
                       created_at,updated_at,payload_json) VALUES(?,?,?,?,?,?,?,?,?)""",
                    (
                        payload["intent_id"], payload["symbol"], payload["action"],
                        int(payload["quantity"]), payload.get("source", "production_v2_41"),
                        "CLAIMED", now, now, json.dumps(payload, sort_keys=True, default=str),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def update_intent(self, intent_id: str, status: str, payload: dict[str, Any] | None = None) -> None:
        now = utcnow()
        with self.connect() as c:
            if payload is None:
                c.execute("UPDATE intents SET status=?,updated_at=? WHERE intent_id=?", (status, now, intent_id))
            else:
                c.execute(
                    "UPDATE intents SET status=?,updated_at=?,payload_json=? WHERE intent_id=?",
                    (status, now, json.dumps(payload, sort_keys=True, default=str), intent_id),
                )

    def record_order(self, *, broker_order_id: int, intent_id: str, role: str,
                     status: str, order_ref: str, payload: dict[str, Any]) -> None:
        now = utcnow()
        with self.connect() as c:
            c.execute(
                """INSERT INTO orders(broker_order_id,intent_id,role,status,order_ref,
                   created_at,updated_at,payload_json) VALUES(?,?,?,?,?,?,?,?)
                   ON CONFLICT(broker_order_id) DO UPDATE SET status=excluded.status,
                   updated_at=excluded.updated_at,payload_json=excluded.payload_json""",
                (int(broker_order_id), intent_id, role, status, order_ref, now, now,
                 json.dumps(payload, sort_keys=True, default=str)),
            )

    def record_fill(self, fill: dict[str, Any]) -> bool:
        try:
            with self.connect() as c:
                c.execute(
                    """INSERT INTO fills(exec_id,broker_order_id,intent_id,symbol,side,shares,
                       price,filled_at,payload_json) VALUES(?,?,?,?,?,?,?,?,?)""",
                    (
                        fill["exec_id"], fill.get("broker_order_id"), fill.get("intent_id"),
                        fill["symbol"], fill["side"], float(fill["shares"]), float(fill["price"]),
                        fill["filled_at"], json.dumps(fill, sort_keys=True, default=str),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def expected_positions(self) -> dict[str, float]:
        expected = self.baseline()
        with self.connect() as c:
            rows = c.execute("SELECT symbol,side,shares FROM fills").fetchall()
        for r in rows:
            s = r["symbol"].upper()
            signed = float(r["shares"]) * (1.0 if str(r["side"]).upper() in {"BOT", "BUY"} else -1.0)
            expected[s] = expected.get(s, 0.0) + signed
        return {s: q for s, q in expected.items() if abs(q) > 1e-9}

    def known_order_ids(self) -> set[int]:
        with self.connect() as c:
            rows = c.execute("SELECT broker_order_id FROM orders").fetchall()
        return {int(r[0]) for r in rows}


    def known_intent_ids(self) -> set[str]:
        with self.connect() as c:
            rows = c.execute("SELECT intent_id FROM intents").fetchall()
        return {str(r[0]) for r in rows}

    def intent_exists(self, intent_id: str) -> bool:
        with self.connect() as c:
            row = c.execute("SELECT 1 FROM intents WHERE intent_id=?", (str(intent_id),)).fetchone()
        return row is not None

    def intent_for_order(self, broker_order_id: int) -> str | None:
        with self.connect() as c:
            row = c.execute(
                "SELECT intent_id FROM orders WHERE broker_order_id=?",
                (int(broker_order_id),),
            ).fetchone()
        return None if row is None else str(row[0])

    def managed_symbols(self) -> set[str]:
        with self.connect() as c:
            rows = c.execute(
                "SELECT DISTINCT symbol FROM fills WHERE intent_id IS NOT NULL AND intent_id != ''"
            ).fetchall()
        return {str(r[0]).upper() for r in rows}

    def recent_intents(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as c:
            rows = c.execute(
                "SELECT * FROM intents ORDER BY created_at DESC LIMIT ?", (int(limit),)
            ).fetchall()
        return [dict(r) for r in rows]

    def latest_cycles(self, limit: int = 10) -> list[dict[str, Any]]:
        with self.connect() as c:
            rows = c.execute(
                "SELECT * FROM cycles ORDER BY cycle_id DESC LIMIT ?", (int(limit),)
            ).fetchall()
        return [dict(r) for r in rows]

    def orders_today(self, date_utc: str) -> int:
        with self.connect() as c:
            row = c.execute(
                "SELECT COUNT(*) FROM intents WHERE substr(created_at,1,10)=? AND action='BUY' AND status NOT IN ('REJECTED','PLANNED','FAILED')",
                (date_utc,),
            ).fetchone()
        return int(row[0])

    def opening_equity(self, date_utc: str, current: float) -> float:
        with self.connect() as c:
            row = c.execute("SELECT opening_net_liq FROM daily_equity WHERE date_utc=?", (date_utc,)).fetchone()
            if row is None:
                c.execute(
                    "INSERT INTO daily_equity(date_utc,opening_net_liq,updated_at) VALUES(?,?,?)",
                    (date_utc, float(current), utcnow()),
                )
                return float(current)
            return float(row[0])

    def inactive_count(self, symbol: str, active: bool) -> int:
        symbol = symbol.upper()
        now = utcnow()
        with self.connect() as c:
            row = c.execute("SELECT count FROM inactive_counts WHERE symbol=?", (symbol,)).fetchone()
            count = 0 if active else (int(row[0]) + 1 if row else 1)
            c.execute(
                """INSERT INTO inactive_counts(symbol,count,updated_at) VALUES(?,?,?)
                   ON CONFLICT(symbol) DO UPDATE SET count=excluded.count,updated_at=excluded.updated_at""",
                (symbol, count, now),
            )
        return count

    def start_cycle(self) -> int:
        with self.connect() as c:
            cur = c.execute(
                "INSERT INTO cycles(started_at,status,summary_json) VALUES(?,?,?)",
                (utcnow(), "RUNNING", "{}"),
            )
            return int(cur.lastrowid)

    def finish_cycle(self, cycle_id: int, status: str, summary: dict[str, Any]) -> None:
        with self.connect() as c:
            c.execute(
                "UPDATE cycles SET finished_at=?,status=?,summary_json=? WHERE cycle_id=?",
                (utcnow(), status, json.dumps(summary, sort_keys=True, default=str), int(cycle_id)),
            )
