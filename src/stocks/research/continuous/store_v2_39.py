from __future__ import annotations
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .contracts_v2_39 import EntityV239, EvidenceRecordV239, JobStatus

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)

def stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(x) for x in parts)
    return f"{prefix}_{hashlib.sha256(raw.encode()).hexdigest()[:24]}"

class ResearchStoreV239:
    """Persistent SQLite state for the continuous research control plane."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
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
            conn.rollback(); raise
        finally:
            conn.close()

    def _init_schema(self):
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS entities(
              entity_id TEXT PRIMARY KEY, entity_type TEXT NOT NULL, family TEXT NOT NULL,
              source TEXT NOT NULL, version TEXT NOT NULL DEFAULT '', role TEXT NOT NULL,
              health TEXT NOT NULL, metadata_json TEXT NOT NULL DEFAULT '{}', is_active INTEGER NOT NULL DEFAULT 1,
              manual_role_locked INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL, last_evaluated_at TEXT, next_due_at TEXT, retired_at TEXT
            );
            CREATE TABLE IF NOT EXISTS evidence(
              evidence_id TEXT PRIMARY KEY, entity_id TEXT NOT NULL REFERENCES entities(entity_id),
              evidence_type TEXT NOT NULL, as_of TEXT NOT NULL, sample_count INTEGER NOT NULL DEFAULT 0,
              metrics_json TEXT NOT NULL, source TEXT NOT NULL, source_ref TEXT NOT NULL,
              observed_at TEXT NOT NULL, UNIQUE(entity_id,evidence_type,source_ref)
            );
            CREATE INDEX IF NOT EXISTS ix_evidence_entity_asof ON evidence(entity_id,as_of DESC);
            CREATE TABLE IF NOT EXISTS jobs(
              job_id TEXT PRIMARY KEY, job_type TEXT NOT NULL, entity_id TEXT REFERENCES entities(entity_id),
              status TEXT NOT NULL, priority INTEGER NOT NULL, payload_json TEXT NOT NULL,
              run_after TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL,
              lease_until TEXT, worker_id TEXT, last_error TEXT, dedupe_key TEXT NOT NULL UNIQUE,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_jobs_ready ON jobs(status,run_after,priority DESC);
            CREATE TABLE IF NOT EXISTS job_attempts(
              attempt_id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(job_id), attempt INTEGER NOT NULL,
              started_at TEXT NOT NULL, finished_at TEXT, returncode INTEGER, stdout_tail TEXT, stderr_tail TEXT
            );
            CREATE TABLE IF NOT EXISTS recommendations(
              recommendation_id TEXT PRIMARY KEY, entity_id TEXT NOT NULL REFERENCES entities(entity_id),
              action TEXT NOT NULL, score REAL NOT NULL, reasons_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_recommendations_entity ON recommendations(entity_id,created_at DESC);
            CREATE TABLE IF NOT EXISTS cycles(
              cycle_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL,
              summary_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS manual_actions(
              action_id TEXT PRIMARY KEY, entity_id TEXT NOT NULL REFERENCES entities(entity_id), action TEXT NOT NULL,
              reason TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS experiments(
              experiment_id TEXT PRIMARY KEY, entity_id TEXT REFERENCES entities(entity_id), experiment_type TEXT NOT NULL,
              status TEXT NOT NULL, hypothesis TEXT NOT NULL, config_json TEXT NOT NULL, parent_experiment_id TEXT,
              result_ref TEXT, created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT
            );
            CREATE INDEX IF NOT EXISTS ix_experiments_entity ON experiments(entity_id,created_at DESC);
            """)

    def upsert_entity(self, entity: EntityV239, *, active: bool = True) -> None:
        now=utc_now(); meta=canonical_json(entity.metadata or {})
        with self.transaction() as c:
            row=c.execute("SELECT manual_role_locked,role,created_at FROM entities WHERE entity_id=?",(entity.entity_id,)).fetchone()
            role = row['role'] if row and row['manual_role_locked'] else entity.role
            created = row['created_at'] if row else now
            c.execute("""INSERT INTO entities(entity_id,entity_type,family,source,version,role,health,metadata_json,is_active,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(entity_id) DO UPDATE SET entity_type=excluded.entity_type,family=excluded.family,source=excluded.source,
              version=excluded.version,role=?,metadata_json=excluded.metadata_json,is_active=excluded.is_active,updated_at=excluded.updated_at""",
              (entity.entity_id,entity.entity_type,entity.family,entity.source,entity.version,role,entity.health,meta,int(active),created,now,role))

    def register_manual(self, entity_id: str, entity_type: str, family: str="UNKNOWN", source: str="MANUAL"):
        self.upsert_entity(EntityV239(entity_id,entity_type,family,source))

    def get_entity(self, entity_id: str) -> dict | None:
        with self.connect() as c:
            r=c.execute("SELECT * FROM entities WHERE entity_id=?",(entity_id,)).fetchone()
        if not r: return None
        d=dict(r); d['metadata']=json.loads(d.pop('metadata_json')); return d

    def list_entities(self, *, active_only: bool=False) -> list[dict]:
        q="SELECT * FROM entities" + (" WHERE is_active=1" if active_only else "") + " ORDER BY role,health,entity_id"
        with self.connect() as c: rows=c.execute(q).fetchall()
        out=[]
        for r in rows:
            d=dict(r); d['metadata']=json.loads(d.pop('metadata_json')); out.append(d)
        return out

    def mark_registry_entities_inactive(self, source: str="CANDIDATE_REGISTRY"):
        with self.transaction() as c:
            c.execute("UPDATE entities SET is_active=0,updated_at=? WHERE source=?",(utc_now(),source))

    def set_entity_health(self, entity_id: str, health: str, *, next_due_at: str | None=None, evaluated: bool=True):
        now=utc_now()
        with self.transaction() as c:
            c.execute("UPDATE entities SET health=?,last_evaluated_at=COALESCE(?,last_evaluated_at),next_due_at=?,updated_at=? WHERE entity_id=?",
                      (health, now if evaluated else None, next_due_at, now, entity_id))

    def set_role_manual(self, entity_id: str, role: str, reason: str):
        now=utc_now(); aid=stable_id("act",entity_id,role,reason,now)
        with self.transaction() as c:
            if not c.execute("SELECT 1 FROM entities WHERE entity_id=?",(entity_id,)).fetchone(): raise KeyError(entity_id)
            c.execute("UPDATE entities SET role=?,manual_role_locked=1,updated_at=?,retired_at=? WHERE entity_id=?",
                      (role,now,now if role=="RETIRED" else None,entity_id))
            c.execute("INSERT INTO manual_actions VALUES(?,?,?,?,?)",(aid,entity_id,"SET_ROLE:"+role,reason,now))

    def add_evidence(self, evidence: EvidenceRecordV239) -> bool:
        eid=stable_id("ev", evidence.entity_id,evidence.evidence_type,evidence.source_ref)
        with self.transaction() as c:
            cur=c.execute("""INSERT OR IGNORE INTO evidence(evidence_id,entity_id,evidence_type,as_of,sample_count,metrics_json,source,source_ref,observed_at)
              VALUES(?,?,?,?,?,?,?,?,?)""",(eid,evidence.entity_id,evidence.evidence_type,evidence.as_of,int(evidence.sample_count),canonical_json(evidence.metrics),evidence.source,evidence.source_ref,utc_now()))
        return cur.rowcount > 0

    def evidence_for(self, entity_id: str) -> list[dict]:
        with self.connect() as c: rows=c.execute("SELECT * FROM evidence WHERE entity_id=? ORDER BY as_of,observed_at",(entity_id,)).fetchall()
        out=[]
        for r in rows:
            d=dict(r); d['metrics']=json.loads(d.pop('metrics_json')); out.append(d)
        return out

    def latest_evidence_time(self, entity_id: str) -> str | None:
        with self.connect() as c: r=c.execute("SELECT MAX(as_of) x FROM evidence WHERE entity_id=?",(entity_id,)).fetchone()
        return r['x'] if r else None

    def enqueue(self, job_type: str, *, entity_id: str | None=None, priority: int=50, payload: dict | None=None,
                run_after: str | None=None, max_attempts: int=3, dedupe_key: str | None=None) -> str:
        run_after=run_after or utc_now(); payload=payload or {}
        dedupe_key=dedupe_key or f"{job_type}:{entity_id or 'GLOBAL'}:{run_after[:13]}"
        jid=stable_id("job",dedupe_key)
        now=utc_now()
        with self.transaction() as c:
            c.execute("""INSERT OR IGNORE INTO jobs(job_id,job_type,entity_id,status,priority,payload_json,run_after,attempts,max_attempts,dedupe_key,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(jid,job_type,entity_id,JobStatus.QUEUED.value,int(priority),canonical_json(payload),run_after,0,int(max_attempts),dedupe_key,now,now))
        return jid

    def reset_stale_leases(self) -> int:
        now=utc_now()
        with self.transaction() as c:
            cur=c.execute("UPDATE jobs SET status='QUEUED',lease_until=NULL,worker_id=NULL,updated_at=? WHERE status='RUNNING' AND lease_until<?",(now,now))
        return cur.rowcount

    def claim_ready(self, *, limit: int, worker_id: str, lease_seconds: int=900) -> list[dict]:
        now=utc_now(); lease=(datetime.now(timezone.utc)+timedelta(seconds=lease_seconds)).isoformat(timespec="seconds")
        claimed=[]
        with self.transaction() as c:
            rows=c.execute("SELECT * FROM jobs WHERE status='QUEUED' AND run_after<=? ORDER BY priority DESC,created_at LIMIT ?",(now,int(limit))).fetchall()
            for r in rows:
                c.execute("UPDATE jobs SET status='RUNNING',attempts=attempts+1,lease_until=?,worker_id=?,updated_at=? WHERE job_id=? AND status='QUEUED'",(lease,worker_id,now,r['job_id']))
                nr=c.execute("SELECT * FROM jobs WHERE job_id=?",(r['job_id'],)).fetchone()
                d=dict(nr); d['payload']=json.loads(d.pop('payload_json')); claimed.append(d)
        return claimed

    def record_attempt_start(self, job: dict) -> str:
        aid=stable_id("attempt",job['job_id'],job['attempts']); now=utc_now()
        with self.transaction() as c: c.execute("INSERT OR REPLACE INTO job_attempts(attempt_id,job_id,attempt,started_at) VALUES(?,?,?,?)",(aid,job['job_id'],job['attempts'],now))
        return aid

    def finish_job(self, job: dict, *, success: bool, attempt_id: str, returncode: int=0, stdout: str="", stderr: str="", retry_base_seconds: int=60):
        now=utc_now(); attempts=int(job['attempts']); max_attempts=int(job['max_attempts'])
        if success: status='SUCCEEDED'; run_after=job['run_after']; err=None
        elif attempts < max_attempts:
            status='QUEUED'; run_after=(datetime.now(timezone.utc)+timedelta(seconds=retry_base_seconds*(2**max(0,attempts-1)))).isoformat(timespec='seconds'); err=(stderr or stdout)[-4000:]
        else: status='DEADLETTER'; run_after=job['run_after']; err=(stderr or stdout)[-4000:]
        with self.transaction() as c:
            c.execute("UPDATE jobs SET status=?,run_after=?,lease_until=NULL,worker_id=NULL,last_error=?,updated_at=? WHERE job_id=?",(status,run_after,err,now,job['job_id']))
            c.execute("UPDATE job_attempts SET finished_at=?,returncode=?,stdout_tail=?,stderr_tail=? WHERE attempt_id=?",(now,int(returncode),stdout[-8000:],stderr[-8000:],attempt_id))

    def jobs(self) -> list[dict]:
        with self.connect() as c: rows=c.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        out=[]
        for r in rows:
            d=dict(r); d['payload']=json.loads(d.pop('payload_json')); out.append(d)
        return out

    def latest_success_time(self, job_type: str) -> str | None:
        with self.connect() as c: r=c.execute("SELECT MAX(updated_at) x FROM jobs WHERE job_type=? AND status='SUCCEEDED'",(job_type,)).fetchone()
        return r['x'] if r else None

    def add_recommendation(self, entity_id: str, action: str, score: float, reasons: Iterable[str]):
        now=utc_now(); rid=stable_id("rec",entity_id,action,now)
        with self.transaction() as c:
            c.execute("INSERT INTO recommendations VALUES(?,?,?,?,?,?)",(rid,entity_id,action,float(score),canonical_json(list(reasons)),now))
        return rid

    def latest_recommendations(self) -> list[dict]:
        with self.connect() as c:
            rows=c.execute("""SELECT r.* FROM recommendations r JOIN (SELECT entity_id,MAX(created_at) m FROM recommendations GROUP BY entity_id) x
              ON x.entity_id=r.entity_id AND x.m=r.created_at ORDER BY r.score DESC""").fetchall()
        out=[]
        for r in rows:
            d=dict(r); d['reasons']=json.loads(d.pop('reasons_json')); out.append(d)
        return out

    def begin_cycle(self) -> str:
        now=utc_now(); cid=stable_id("cycle",now)
        with self.transaction() as c: c.execute("INSERT INTO cycles(cycle_id,started_at,status) VALUES(?,?,?)",(cid,now,'RUNNING'))
        return cid

    def finish_cycle(self, cycle_id: str, *, status: str, summary: dict):
        with self.transaction() as c: c.execute("UPDATE cycles SET finished_at=?,status=?,summary_json=? WHERE cycle_id=?",(utc_now(),status,canonical_json(summary),cycle_id))

    def register_experiment(self, *, entity_id: str | None, experiment_type: str, hypothesis: str, config: dict | None=None, parent_experiment_id: str | None=None) -> str:
        now=utc_now(); xid=stable_id("exp",entity_id or "GLOBAL",experiment_type,hypothesis,now)
        with self.transaction() as c:
            c.execute("INSERT INTO experiments(experiment_id,entity_id,experiment_type,status,hypothesis,config_json,parent_experiment_id,created_at) VALUES(?,?,?,?,?,?,?,?)",
                      (xid,entity_id,experiment_type,"REGISTERED",hypothesis,canonical_json(config or {}),parent_experiment_id,now))
        return xid

    def update_experiment(self, experiment_id: str, *, status: str, result_ref: str | None=None):
        now=utc_now(); started=now if status=="RUNNING" else None; finished=now if status in {"SUCCEEDED","FAILED","REJECTED"} else None
        with self.transaction() as c:
            if not c.execute("SELECT 1 FROM experiments WHERE experiment_id=?",(experiment_id,)).fetchone(): raise KeyError(experiment_id)
            c.execute("UPDATE experiments SET status=?,result_ref=COALESCE(?,result_ref),started_at=COALESCE(started_at,?),finished_at=COALESCE(?,finished_at) WHERE experiment_id=?",
                      (status,result_ref,started,finished,experiment_id))

    def experiments(self) -> list[dict]:
        with self.connect() as c: rows=c.execute("SELECT * FROM experiments ORDER BY created_at DESC").fetchall()
        out=[]
        for r in rows:
            d=dict(r); d['config']=json.loads(d.pop('config_json')); out.append(d)
        return out

    def job_attempts(self) -> list[dict]:
        with self.connect() as c: return [dict(x) for x in c.execute("SELECT * FROM job_attempts ORDER BY started_at DESC").fetchall()]

    def latest_evidence_rows(self) -> list[dict]:
        with self.connect() as c:
            rows=c.execute("""SELECT e.* FROM evidence e JOIN (SELECT entity_id,evidence_type,MAX(as_of) m FROM evidence GROUP BY entity_id,evidence_type) x
              ON x.entity_id=e.entity_id AND x.evidence_type=e.evidence_type AND x.m=e.as_of ORDER BY e.entity_id,e.evidence_type""").fetchall()
        out=[]
        for r in rows:
            d=dict(r); d['metrics']=json.loads(d.pop('metrics_json')); out.append(d)
        return out

    def counts(self) -> dict:
        with self.connect() as c:
            entities=c.execute("SELECT role,health,COUNT(*) n FROM entities WHERE is_active=1 GROUP BY role,health").fetchall()
            jobs=c.execute("SELECT status,COUNT(*) n FROM jobs GROUP BY status").fetchall()
            ev=c.execute("SELECT COUNT(*) n FROM evidence").fetchone()['n']
        return {"entities":[dict(x) for x in entities],"jobs":[dict(x) for x in jobs],"evidence":int(ev)}

__all__=["ResearchStoreV239","canonical_json","parse_utc","stable_id","utc_now"]
