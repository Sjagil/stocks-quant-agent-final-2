from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


class LearningStoreV240:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    @contextmanager
    def transaction(self):
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.connect() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS agents(
                  agent_id TEXT PRIMARY KEY,
                  algorithm TEXT NOT NULL,
                  symbol TEXT NOT NULL,
                  timeframe TEXT NOT NULL,
                  data_path TEXT NOT NULL,
                  state TEXT NOT NULL,
                  enabled INTEGER NOT NULL,
                  last_data_rows INTEGER NOT NULL DEFAULT 0,
                  last_data_time TEXT,
                  last_train_at TEXT,
                  last_success_at TEXT,
                  model_path TEXT,
                  replay_buffer_path TEXT,
                  latest_validation_json TEXT NOT NULL DEFAULT '{}',
                  latest_test_json TEXT NOT NULL DEFAULT '{}',
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS training_runs(
                  run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  agent_id TEXT NOT NULL REFERENCES agents(agent_id),
                  started_at TEXT NOT NULL,
                  finished_at TEXT,
                  status TEXT NOT NULL,
                  trigger_json TEXT NOT NULL,
                  result_json TEXT NOT NULL DEFAULT '{}',
                  error TEXT
                );
                CREATE INDEX IF NOT EXISTS ix_training_runs_agent ON training_runs(agent_id, started_at DESC);
                CREATE TABLE IF NOT EXISTS cycles(
                  cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  started_at TEXT NOT NULL,
                  finished_at TEXT,
                  status TEXT NOT NULL,
                  summary_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS cursors(
                  cursor_key TEXT PRIMARY KEY,
                  value_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS component_runs(
                  component_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  cycle_id INTEGER REFERENCES cycles(cycle_id),
                  component TEXT NOT NULL,
                  started_at TEXT NOT NULL,
                  finished_at TEXT NOT NULL,
                  status TEXT NOT NULL,
                  returncode INTEGER NOT NULL,
                  stdout_tail TEXT NOT NULL,
                  stderr_tail TEXT NOT NULL
                );
                """
            )

    def upsert_agent(self, spec, *, state: str = "IDLE") -> None:
        now = utc_now()
        with self.transaction() as c:
            c.execute(
                """INSERT INTO agents(agent_id,algorithm,symbol,timeframe,data_path,state,enabled,updated_at)
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(agent_id) DO UPDATE SET algorithm=excluded.algorithm,symbol=excluded.symbol,
                timeframe=excluded.timeframe,data_path=excluded.data_path,enabled=excluded.enabled,updated_at=excluded.updated_at""",
                (spec.agent_id, spec.algorithm.upper(), spec.symbol.upper(), spec.timeframe, spec.data_path, state, int(spec.enabled), now),
            )

    def agent(self, agent_id: str) -> dict | None:
        with self.connect() as c:
            row = c.execute("SELECT * FROM agents WHERE agent_id=?", (agent_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["latest_validation"] = json.loads(d.pop("latest_validation_json"))
        d["latest_test"] = json.loads(d.pop("latest_test_json"))
        return d

    def agents(self) -> list[dict]:
        with self.connect() as c:
            rows = c.execute("SELECT * FROM agents ORDER BY agent_id").fetchall()
        out = []
        for row in rows:
            d = dict(row)
            d["latest_validation"] = json.loads(d.pop("latest_validation_json"))
            d["latest_test"] = json.loads(d.pop("latest_test_json"))
            out.append(d)
        return out

    def set_agent_state(self, agent_id: str, state: str) -> None:
        with self.transaction() as c:
            c.execute("UPDATE agents SET state=?,updated_at=? WHERE agent_id=?", (state, utc_now(), agent_id))

    def begin_training(self, agent_id: str, trigger: dict) -> int:
        now = utc_now()
        with self.transaction() as c:
            c.execute("UPDATE agents SET state='TRAINING',last_train_at=?,updated_at=? WHERE agent_id=?", (now, now, agent_id))
            cur = c.execute(
                "INSERT INTO training_runs(agent_id,started_at,status,trigger_json) VALUES(?,?,?,?)",
                (agent_id, now, "RUNNING", canonical_json(trigger)),
            )
            return int(cur.lastrowid)

    def finish_training(self, run_id: int, agent_id: str, *, status: str, result: dict | None = None, error: str | None = None) -> None:
        now = utc_now()
        result = result or {}
        next_state = "READY" if status == "SUCCEEDED" else "FAILED"
        with self.transaction() as c:
            c.execute(
                "UPDATE training_runs SET finished_at=?,status=?,result_json=?,error=? WHERE run_id=?",
                (now, status, canonical_json(result), error, int(run_id)),
            )
            if status == "SUCCEEDED":
                c.execute(
                    """UPDATE agents SET state=?,last_success_at=?,last_data_rows=?,last_data_time=?,model_path=?,replay_buffer_path=?,
                    latest_validation_json=?,latest_test_json=?,updated_at=? WHERE agent_id=?""",
                    (
                        next_state, now, int(result.get("data_rows", 0)), result.get("latest_data_time"),
                        result.get("model_path"), result.get("replay_buffer_path"), canonical_json(result.get("validation") or {}),
                        canonical_json(result.get("test") or {}), now, agent_id,
                    ),
                )
            else:
                c.execute("UPDATE agents SET state=?,updated_at=? WHERE agent_id=?", (next_state, now, agent_id))

    def begin_cycle(self) -> int:
        with self.transaction() as c:
            cur = c.execute("INSERT INTO cycles(started_at,status) VALUES(?,?)", (utc_now(), "RUNNING"))
            return int(cur.lastrowid)

    def finish_cycle(self, cycle_id: int, *, status: str, summary: dict) -> None:
        with self.transaction() as c:
            c.execute("UPDATE cycles SET finished_at=?,status=?,summary_json=? WHERE cycle_id=?", (utc_now(), status, canonical_json(summary), int(cycle_id)))

    def add_component_run(self, cycle_id: int, component: str, *, started_at: str, finished_at: str, status: str, returncode: int, stdout: str, stderr: str) -> None:
        with self.transaction() as c:
            c.execute(
                "INSERT INTO component_runs(cycle_id,component,started_at,finished_at,status,returncode,stdout_tail,stderr_tail) VALUES(?,?,?,?,?,?,?,?)",
                (int(cycle_id), component, started_at, finished_at, status, int(returncode), stdout[-12000:], stderr[-12000:]),
            )

    def cursor(self, key: str, default=None):
        with self.connect() as c:
            row = c.execute("SELECT value_json FROM cursors WHERE cursor_key=?", (key,)).fetchone()
        return json.loads(row["value_json"]) if row else default

    def set_cursor(self, key: str, value) -> None:
        now = utc_now()
        with self.transaction() as c:
            c.execute(
                """INSERT INTO cursors(cursor_key,value_json,updated_at) VALUES(?,?,?)
                ON CONFLICT(cursor_key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at""",
                (key, canonical_json(value), now),
            )

    def status(self) -> dict:
        with self.connect() as c:
            cycle = c.execute("SELECT * FROM cycles ORDER BY cycle_id DESC LIMIT 1").fetchone()
            train = c.execute("SELECT * FROM training_runs ORDER BY run_id DESC LIMIT 10").fetchall()
        return {
            "agents": self.agents(),
            "last_cycle": dict(cycle) if cycle else None,
            "recent_training_runs": [dict(row) for row in train],
            "execution_authority": "NONE",
        }


__all__ = ["LearningStoreV240", "utc_now"]
