"""SQLite repository. The only module that knows SQL (swap for Postgres here)."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS plans (
    id          TEXT PRIMARY KEY,
    event_id    TEXT NOT NULL,
    channel_id  TEXT NOT NULL,
    thread_ts   TEXT,
    requester   TEXT NOT NULL,
    intent      TEXT NOT NULL,
    raw_input   TEXT NOT NULL,
    plan_json   TEXT,
    state       TEXT NOT NULL DEFAULT 'pending'
        CHECK (state IN ('pending','approved','rejected','executed','failed','ignored')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at  TEXT,
    decided_by  TEXT
);
-- Idempotency: one plan per Slack event_id, enforced by the database.
CREATE UNIQUE INDEX IF NOT EXISTS ux_plans_event_id ON plans(event_id);

CREATE TABLE IF NOT EXISTS audit_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id      TEXT REFERENCES plans(id),
    stage        TEXT NOT NULL
        CHECK (stage IN ('event_received','plan_generated','approval_received','executed','failed')),
    actor        TEXT,
    detail       TEXT,
    payload_hash TEXT,
    ts           TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_audit_plan ON audit_log(plan_id);

-- Append-only, enforced by the database rather than by convention.
CREATE TRIGGER IF NOT EXISTS audit_log_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_log_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
"""


def payload_hash(payload: Any) -> str | None:
    """SHA-256 of a payload (never the payload itself)."""
    if payload is None:
        return None
    if not isinstance(payload, (str, bytes)):
        payload = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    if isinstance(payload, str):
        payload = payload.encode()
    return hashlib.sha256(payload).hexdigest()


class PlanRepository:
    """Synchronous sqlite3 on the event-loop thread.

    Statements are single-row and sub-millisecond, so this is fine for one process.
    If it ever matters, wrap calls in asyncio.to_thread.
    """

    def __init__(self, path: str = "switch_planner.db") -> None:
        self._db = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        if path != ":memory:":
            self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        self._db.close()

    # ---- plans -----------------------------------------------------------
    def claim_event(
        self, event_id: str, channel_id: str, thread_ts: str | None, requester: str, raw_input: str
    ) -> str | None:
        """Insert a plan row for this event. Returns plan_id, or None if already seen."""
        plan_id = str(uuid.uuid4())
        cur = self._db.execute(
            "INSERT OR IGNORE INTO plans (id, event_id, channel_id, thread_ts, requester, intent, raw_input)"
            " VALUES (?,?,?,?,?,?,?)",
            (plan_id, event_id, channel_id, thread_ts, requester, "unrouted", raw_input),
        )
        return plan_id if cur.rowcount == 1 else None

    def set_intent(self, plan_id: str, intent: str) -> None:
        self._db.execute("UPDATE plans SET intent=? WHERE id=?", (intent, plan_id))

    def set_thread(self, plan_id: str, thread_ts: str) -> None:
        self._db.execute("UPDATE plans SET thread_ts=? WHERE id=?", (thread_ts, plan_id))

    def save_plan(self, plan_id: str, plan_json: str) -> None:
        self._db.execute("UPDATE plans SET plan_json=? WHERE id=?", (plan_json, plan_id))

    def decide(self, plan_id: str, new_state: str, decided_by: str) -> bool:
        """Atomic compare-and-set: only the first decision on a generated plan wins."""
        assert new_state in ("approved", "rejected")
        cur = self._db.execute(
            "UPDATE plans SET state=?, decided_at=datetime('now'), decided_by=?"
            " WHERE id=? AND state='pending' AND plan_json IS NOT NULL",
            (new_state, decided_by, plan_id),
        )
        return cur.rowcount == 1

    def transition(self, plan_id: str, expected: str, new: str) -> bool:
        cur = self._db.execute(
            "UPDATE plans SET state=? WHERE id=? AND state=?", (new, plan_id, expected)
        )
        return cur.rowcount == 1

    def get(self, plan_id: str) -> dict | None:
        row = self._db.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
        return dict(row) if row else None

    def get_by_event(self, event_id: str) -> dict | None:
        row = self._db.execute("SELECT * FROM plans WHERE event_id=?", (event_id,)).fetchone()
        return dict(row) if row else None

    def fail_orphans(self) -> int:
        """Startup sweep: plans stuck mid-flight by a crash are failed, never resumed."""
        rows = self._db.execute(
            "SELECT id, state FROM plans WHERE (state='pending' AND plan_json IS NULL) OR state='approved'"
        ).fetchall()
        for r in rows:
            if self.transition(r["id"], r["state"], "failed"):
                self.audit(r["id"], "failed", "system", f"orphaned in '{r['state']}' at startup")
        return len(rows)

    # ---- audit -----------------------------------------------------------
    def audit(
        self, plan_id: str, stage: str, actor: str | None, detail: str, payload: Any = None
    ) -> None:
        self._db.execute(
            "INSERT INTO audit_log (plan_id, stage, actor, detail, payload_hash) VALUES (?,?,?,?,?)",
            (plan_id, stage, actor, detail, payload_hash(payload)),
        )

    def audit_rows(self, plan_id: str) -> list[dict]:
        rows = self._db.execute(
            "SELECT * FROM audit_log WHERE plan_id=? ORDER BY id", (plan_id,)
        ).fetchall()
        return [dict(r) for r in rows]
