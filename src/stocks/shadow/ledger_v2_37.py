from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Iterable

GENESIS_HASH = "0" * 64

def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)

def _event_hash(prev_hash: str, event_id: str, event_type: str, aggregate_id: str, event_time: str, payload_json: str) -> str:
    raw = "|".join((prev_hash, event_id, event_type, aggregate_id, event_time, payload_json)).encode()
    return hashlib.sha256(raw).hexdigest()

@dataclass(frozen=True)
class ShadowEventV237:
    seq: int
    event_id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    event_time: str
    idempotency_key: str | None
    payload: dict
    prev_hash: str
    event_hash: str

class ShadowLedgerV237:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS shadow_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                aggregate_type TEXT NOT NULL,
                aggregate_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_time TEXT NOT NULL,
                idempotency_key TEXT,
                payload_json TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL UNIQUE
            )
        """)
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_shadow_aggregate ON shadow_events(aggregate_type, aggregate_id, seq)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_shadow_idempotency ON shadow_events(idempotency_key, seq)")
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _last_hash(self) -> str:
        row = self.connection.execute("SELECT event_hash FROM shadow_events ORDER BY seq DESC LIMIT 1").fetchone()
        return GENESIS_HASH if row is None else str(row["event_hash"])

    def append(
        self,
        *,
        event_id: str,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict,
        event_time: str,
        idempotency_key: str | None = None,
    ) -> bool:
        existing = self.connection.execute("SELECT 1 FROM shadow_events WHERE event_id=?", (event_id,)).fetchone()
        if existing:
            return False
        payload_json = _canonical(payload)
        prev_hash = self._last_hash()
        event_hash = _event_hash(prev_hash, event_id, event_type, aggregate_id, event_time, payload_json)
        try:
            self.connection.execute(
                """INSERT INTO shadow_events(
                    event_id,aggregate_type,aggregate_id,event_type,event_time,idempotency_key,payload_json,prev_hash,event_hash
                ) VALUES(?,?,?,?,?,?,?,?,?)""",
                (event_id, aggregate_type, aggregate_id, event_type, event_time, idempotency_key, payload_json, prev_hash, event_hash),
            )
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            self.connection.rollback()
            return False

    def events(self, *, aggregate_type: str | None = None, aggregate_id: str | None = None) -> tuple[ShadowEventV237, ...]:
        sql = "SELECT * FROM shadow_events"
        params: list[str] = []
        clauses = []
        if aggregate_type is not None:
            clauses.append("aggregate_type=?")
            params.append(aggregate_type)
        if aggregate_id is not None:
            clauses.append("aggregate_id=?")
            params.append(aggregate_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY seq"
        rows = self.connection.execute(sql, params).fetchall()
        return tuple(
            ShadowEventV237(
                int(r["seq"]), str(r["event_id"]), str(r["aggregate_type"]), str(r["aggregate_id"]),
                str(r["event_type"]), str(r["event_time"]), r["idempotency_key"],
                json.loads(r["payload_json"]), str(r["prev_hash"]), str(r["event_hash"])
            )
            for r in rows
        )

    def events_for_idempotency(self, key: str) -> tuple[ShadowEventV237, ...]:
        rows = self.connection.execute("SELECT * FROM shadow_events WHERE idempotency_key=? ORDER BY seq", (key,)).fetchall()
        return tuple(
            ShadowEventV237(
                int(r["seq"]), str(r["event_id"]), str(r["aggregate_type"]), str(r["aggregate_id"]),
                str(r["event_type"]), str(r["event_time"]), r["idempotency_key"],
                json.loads(r["payload_json"]), str(r["prev_hash"]), str(r["event_hash"])
            ) for r in rows
        )

    def verify_hash_chain(self) -> bool:
        prev = GENESIS_HASH
        for event in self.events():
            payload_json = _canonical(event.payload)
            expected = _event_hash(prev, event.event_id, event.event_type, event.aggregate_id, event.event_time, payload_json)
            if event.prev_hash != prev or event.event_hash != expected:
                return False
            prev = event.event_hash
        return True

    def event_count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM shadow_events").fetchone()[0])

__all__ = ["GENESIS_HASH", "ShadowEventV237", "ShadowLedgerV237"]
