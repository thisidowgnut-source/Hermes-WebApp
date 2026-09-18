"""SQLite WAL mission ledger, transaction boundaries, event sequencing, and idempotency."""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, List, Optional, Union
from uuid import UUID

from backend.config import config
from backend.models.mission import (
    CostRecord,
    CreateMissionRequest,
    CreateTurnRequest,
    MissionEvent,
    MissionSnapshot,
    MissionState,
    OperatorContext,
    RunRecord,
    TurnRecord,
    UsageRecord,
)
from backend.services.mission_policy import assert_transition, redact_payload


class MissionStore:
    """Durable SQLite WAL mission store and state ledger."""

    def __init__(self, db_path: Optional[Union[Path, str]] = None):
        if db_path is None:
            self.db_path: Union[Path, str] = Path(config.MISSION_DB_PATH)
        elif str(db_path) == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = Path(db_path)
        self._event_listeners: list[Any] = []

    def register_event_listener(self, listener: Any) -> None:
        """Register a callback for newly appended events: listener(mission_id, event_dict)."""
        if listener not in self._event_listeners:
            self._event_listeners.append(listener)

    def unregister_event_listener(self, listener: Any) -> None:
        """Unregister an event callback."""
        if listener in self._event_listeners:
            self._event_listeners.remove(listener)


    def _get_connection(self) -> sqlite3.Connection:
        if isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=5.0,
            isolation_level=None,  # Explicit transaction control
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    @contextmanager
    def _transaction(self, immediate: bool = True) -> Generator[sqlite3.Connection, None, None]:
        conn = self._get_connection()
        try:
            if immediate:
                conn.execute("BEGIN IMMEDIATE;")
            else:
                conn.execute("BEGIN;")
            yield conn
            conn.execute("COMMIT;")
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """Create database tables and indexes if they do not exist."""
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY,
                    project_slug TEXT NOT NULL,
                    title TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    primary_executor TEXT NOT NULL,
                    agent_profile TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS mission_runs (
                    id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    executor TEXT NOT NULL,
                    agent_profile TEXT NOT NULL,
                    state TEXT NOT NULL,
                    provider_conversation_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS mission_turns (
                    id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    run_id TEXT,
                    message TEXT NOT NULL,
                    state TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS mission_events (
                    id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    payload JSON NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    project_slug TEXT NOT NULL,
                    source_facts TEXT NOT NULL,
                    drafts TEXT NOT NULL,
                    brand_truth_hash TEXT NOT NULL,
                    content_hashes TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT,
                    mission_id TEXT,
                    platform TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    media_sha256 TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    decided_at TEXT,
                    decided_by TEXT
                );

                CREATE TABLE IF NOT EXISTS publication_attempts (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    approval_id TEXT,
                    platform TEXT NOT NULL,
                    state TEXT NOT NULL,
                    remote_post_id TEXT,
                    published_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cost_records (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS operator_sessions (
                    id TEXT PRIMARY KEY,
                    operator_id INTEGER NOT NULL,
                    token_hash TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS websocket_tickets (
                    id TEXT PRIMARY KEY,
                    operator_id INTEGER NOT NULL,
                    ticket_hash TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    consumed_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    operator_id INTEGER NOT NULL,
                    operation TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (operator_id, operation, idempotency_key)
                );

                CREATE TABLE IF NOT EXISTS migration_manifests (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_mission_events_mission_seq ON mission_events(mission_id, sequence);
                CREATE INDEX IF NOT EXISTS idx_mission_turns_mission_seq ON mission_turns(mission_id, sequence);
            """)

            # Schema evolution checks for existing databases
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(approvals);")
            approval_cols = {row["name"] for row in cursor.fetchall()}
            if approval_cols and "campaign_id" not in approval_cols:
                conn.execute("ALTER TABLE approvals ADD COLUMN campaign_id TEXT;")
            if approval_cols and "media_sha256" not in approval_cols:
                conn.execute("ALTER TABLE approvals ADD COLUMN media_sha256 TEXT NOT NULL DEFAULT '[]';")

            cursor.execute("PRAGMA table_info(publication_attempts);")
            attempt_cols = {row["name"] for row in cursor.fetchall()}
            if attempt_cols and "approval_id" not in attempt_cols:
                conn.execute("ALTER TABLE publication_attempts ADD COLUMN approval_id TEXT;")
        finally:
            conn.close()

    def create_mission(
        self, request: CreateMissionRequest, operator: OperatorContext
    ) -> MissionSnapshot:
        """Idempotently create a mission.

        If exists for operator_id + 'create_mission' + idempotency_key, returns stored snapshot
        without duplicating. Otherwise inserts mission, records idempotency, appends event
        "mission.created", and returns snapshot with mission_id.
        """
        op_id = operator.operator_id
        idem_key = str(request.idempotency_key)
        operation = "create_mission"

        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT response_json FROM idempotency_keys
                WHERE operator_id = ? AND operation = ? AND idempotency_key = ?
                """,
                (op_id, operation, idem_key),
            )
            row = cursor.fetchone()
            if row:
                snap = MissionSnapshot(json.loads(row["response_json"]))
                snap["_is_replay"] = True
                return snap

            mission_id = str(uuid.uuid4())
            now_iso = datetime.now(timezone.utc).isoformat()
            executor_str = (
                request.primary_executor.value
                if hasattr(request.primary_executor, "value")
                else str(request.primary_executor)
            )
            state_str = MissionState.DRAFT.value

            cursor.execute(
                """
                INSERT INTO missions (
                    id, project_slug, title, objective, primary_executor,
                    agent_profile, state, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mission_id,
                    request.project_slug,
                    request.title,
                    request.objective,
                    executor_str,
                    request.agent_profile,
                    state_str,
                    now_iso,
                    now_iso,
                ),
            )

            snapshot_data = {
                "id": mission_id,
                "mission_id": mission_id,
                "project_slug": request.project_slug,
                "title": request.title,
                "objective": request.objective,
                "primary_executor": executor_str,
                "agent_profile": request.agent_profile,
                "state": state_str,
                "created_at": now_iso,
                "updated_at": now_iso,
            }

            cursor.execute(
                """
                INSERT INTO idempotency_keys (
                    operator_id, operation, idempotency_key, response_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (op_id, operation, idem_key, json.dumps(snapshot_data), now_iso),
            )

            # Insert initial event: mission.created (sequence 1)
            event_id = str(uuid.uuid4())
            initial_payload = redact_payload({
                "project_slug": request.project_slug,
                "title": request.title,
                "objective": request.objective,
                "primary_executor": executor_str,
                "agent_profile": request.agent_profile,
                "operator_id": op_id,
            })
            cursor.execute(
                """
                INSERT INTO mission_events (id, mission_id, sequence, event_type, payload, created_at)
                VALUES (?, ?, 1, 'mission.created', ?, ?)
                """,
                (event_id, mission_id, json.dumps(initial_payload), now_iso),
            )

        snap = MissionSnapshot(snapshot_data)
        snap["_is_replay"] = False
        return snap

    def get_mission(self, mission_id: Union[UUID, str]) -> Optional[MissionSnapshot]:
        """Retrieve a mission by its ID."""
        m_id = str(mission_id)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, project_slug, title, objective, primary_executor,
                       agent_profile, state, created_at, updated_at
                FROM missions
                WHERE id = ?
                """,
                (m_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return MissionSnapshot({
                "id": row["id"],
                "mission_id": row["id"],
                "project_slug": row["project_slug"],
                "title": row["title"],
                "objective": row["objective"],
                "primary_executor": row["primary_executor"],
                "agent_profile": row["agent_profile"],
                "state": row["state"],
                "status": row["state"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })
        finally:
            conn.close()

    def list_missions(self, operator: Optional[OperatorContext] = None) -> list[dict]:
        """Fetch all visible missions ordered by creation time descending."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, project_slug, title, objective, primary_executor,
                       agent_profile, state, created_at, updated_at
                FROM missions
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "mission_id": row["id"],
                    "project_slug": row["project_slug"],
                    "title": row["title"],
                    "objective": row["objective"],
                    "primary_executor": row["primary_executor"],
                    "agent_profile": row["agent_profile"],
                    "state": row["state"],
                    "status": row["state"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in rows
            ]
        finally:
            conn.close()

    def check_idempotency(
        self, operator_id: int, operation: str, idempotency_key: Union[UUID, str]
    ) -> Optional[dict]:
        """Check if an idempotency key exists for an operator and operation."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT response_json FROM idempotency_keys
                WHERE operator_id = ? AND operation = ? AND idempotency_key = ?
                """,
                (operator_id, operation, str(idempotency_key)),
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row["response_json"])
            return None
        finally:
            conn.close()

    def get_latest_run_for_mission(self, mission_id: Union[UUID, str]) -> Optional[RunRecord]:
        """Fetch the most recently created run for a mission."""
        m_id = str(mission_id)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, mission_id, executor, agent_profile, state,
                       provider_conversation_id, created_at, updated_at
                FROM mission_runs
                WHERE mission_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (m_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return RunRecord({
                "id": row["id"],
                "run_id": row["id"],
                "mission_id": row["mission_id"],
                "executor": row["executor"],
                "agent_profile": row["agent_profile"],
                "state": MissionState(row["state"]),
                "provider_conversation_id": row["provider_conversation_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })
        finally:
            conn.close()

    def append_event(
        self, mission_id: Union[UUID, str], event_type: str, payload: dict
    ) -> MissionEvent:
        """Allocates monotonic integer sequence (1, 2, 3...) per mission,
        applies redact_payload, inserts and returns event record with sequence.
        """
        m_id = str(mission_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        redacted = redact_payload(payload if isinstance(payload, dict) else dict(payload))
        event_id = str(uuid.uuid4())

        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(MAX(sequence), 0) FROM mission_events WHERE mission_id = ?",
                (m_id,),
            )
            next_seq = cursor.fetchone()[0] + 1
            cursor.execute(
                """
                INSERT INTO mission_events (id, mission_id, sequence, event_type, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, m_id, next_seq, event_type, json.dumps(redacted), now_iso),
            )

        event = MissionEvent({
            "id": event_id,
            "mission_id": m_id,
            "sequence": next_seq,
            "event_type": event_type,
            "payload": redacted,
            "created_at": now_iso,
        })
        for listener in getattr(self, "_event_listeners", []):
            try:
                listener(m_id, dict(event))
            except Exception:
                pass
        return event

    def get_events(
        self, mission_id: Union[UUID, str], after_sequence: int = 0
    ) -> List[MissionEvent]:
        """Fetch all events for a mission with sequence > after_sequence, ordered ascending."""
        m_id = str(mission_id)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, mission_id, sequence, event_type, payload, created_at
                FROM mission_events
                WHERE mission_id = ? AND sequence > ?
                ORDER BY sequence ASC
                """,
                (m_id, after_sequence),
            )
            rows = cursor.fetchall()
            events = []
            for row in rows:
                p = row["payload"]
                if isinstance(p, str):
                    try:
                        p = json.loads(p)
                    except Exception:
                        pass
                events.append(
                    MissionEvent({
                        "id": row["id"],
                        "mission_id": row["mission_id"],
                        "sequence": row["sequence"],
                        "event_type": row["event_type"],
                        "payload": p,
                        "created_at": row["created_at"],
                    })
                )
            return events
        finally:
            conn.close()

    def count_rows(self, table_name: str) -> int:
        """Return the number of rows in the specified table."""
        allowed_tables = {
            "missions",
            "mission_runs",
            "mission_turns",
            "mission_events",
            "artifacts",
            "campaigns",
            "approvals",
            "publication_attempts",
            "cost_records",
            "operator_sessions",
            "websocket_tickets",
            "idempotency_keys",
            "migration_manifests",
        }
        if table_name not in allowed_tables:
            raise ValueError(f"Table name '{table_name}' is not allowed or does not exist.")
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    def update_mission_state(
        self, mission_id: Union[UUID, str], new_state: Union[MissionState, str]
    ) -> None:
        """Update mission state after checking assert_transition.

        Raises:
            ValueError: If the mission does not exist.
            InvalidMissionTransition: If the transition is illegal.
        """
        m_id = str(mission_id)
        mission = self.get_mission(m_id)
        if not mission:
            raise ValueError(f"Mission '{m_id}' not found.")

        current_state = MissionState(mission["state"])
        target_state = MissionState(new_state) if isinstance(new_state, str) else new_state

        assert_transition(current_state, target_state)

        now_iso = datetime.now(timezone.utc).isoformat()
        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE missions SET state = ?, updated_at = ? WHERE id = ?",
                (target_state.value, now_iso, m_id),
            )

        self.append_event(
            mission_id=m_id,
            event_type="mission.state_changed",
            payload={
                "from_state": current_state.value,
                "to_state": target_state.value,
            },
        )

    def enqueue_turn(
        self,
        mission_id: Union[UUID, str],
        request: CreateTurnRequest,
        operator: OperatorContext,
    ) -> TurnRecord:
        """Enqueue a new turn for the mission, allocating sequence and appending event."""
        m_id = str(mission_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        turn_id = str(uuid.uuid4())

        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(MAX(sequence), 0) FROM mission_turns WHERE mission_id = ?",
                (m_id,),
            )
            next_seq = cursor.fetchone()[0] + 1
            cursor.execute(
                """
                INSERT INTO mission_turns (id, mission_id, run_id, message, state, sequence, created_at)
                VALUES (?, ?, NULL, ?, 'queued', ?, ?)
                """,
                (turn_id, m_id, request.message, next_seq, now_iso),
            )

        turn_data = {
            "id": turn_id,
            "turn_id": turn_id,
            "mission_id": m_id,
            "message": request.message,
            "state": "queued",
            "sequence": next_seq,
            "created_at": now_iso,
        }

        self.append_event(
            mission_id=m_id,
            event_type="turn.enqueued",
            payload={
                "turn_id": turn_id,
                "sequence": next_seq,
                "operator_id": operator.operator_id,
                "message": request.message,
            },
        )

        return TurnRecord(turn_data)

    def save_campaign(self, campaign_data: dict) -> None:
        """Persist a campaign record."""
        c_id = str(campaign_data["id"])
        source_facts = campaign_data.get("source_facts", [])
        drafts = campaign_data.get("drafts", {})
        content_hashes = campaign_data.get("content_hashes", {})
        with self._transaction(immediate=True) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO campaigns (
                    id, project_slug, source_facts, drafts, brand_truth_hash, content_hashes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    c_id,
                    campaign_data["project_slug"],
                    json.dumps(source_facts if isinstance(source_facts, (list, dict)) else []),
                    json.dumps(drafts if isinstance(drafts, dict) else {}),
                    campaign_data.get("brand_truth_hash", ""),
                    json.dumps(content_hashes if isinstance(content_hashes, dict) else {}),
                    str(campaign_data["created_at"]),
                ),
            )

    def get_campaign(self, campaign_id: Union[UUID, str]) -> Optional[dict]:
        """Fetch a campaign record by ID."""
        c_id = str(campaign_id)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, project_slug, source_facts, drafts, brand_truth_hash, content_hashes, created_at FROM campaigns WHERE id = ?",
                (c_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "project_slug": row["project_slug"],
                "source_facts": json.loads(row["source_facts"]),
                "drafts": json.loads(row["drafts"]),
                "brand_truth_hash": row["brand_truth_hash"],
                "content_hashes": json.loads(row["content_hashes"]),
                "created_at": row["created_at"],
            }
        finally:
            conn.close()

    def save_approval(self, approval_data: dict) -> None:
        """Persist an approval record."""
        a_id = str(approval_data["id"])
        c_id = str(approval_data.get("campaign_id") or approval_data.get("mission_id") or "")
        m_id = str(approval_data.get("mission_id") or "")
        media_list = approval_data.get("media_sha256", [])
        with self._transaction(immediate=True) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO approvals (
                    id, campaign_id, mission_id, platform, account_id,
                    content_sha256, media_sha256, status, expires_at,
                    created_at, decided_at, decided_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    a_id,
                    c_id,
                    m_id,
                    approval_data["platform"],
                    approval_data["account_id"],
                    approval_data["content_sha256"],
                    json.dumps(media_list if isinstance(media_list, list) else []),
                    approval_data.get("status", "pending"),
                    str(approval_data["expires_at"]),
                    str(approval_data["created_at"]),
                    str(approval_data["decided_at"]) if approval_data.get("decided_at") else None,
                    str(approval_data["decided_by"]) if approval_data.get("decided_by") else None,
                ),
            )

    def get_approval(self, approval_id: Union[UUID, str]) -> Optional[dict]:
        """Fetch an approval record by ID."""
        a_id = str(approval_id)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, campaign_id, mission_id, platform, account_id,
                       content_sha256, media_sha256, status, expires_at,
                       created_at, decided_at, decided_by
                FROM approvals WHERE id = ?
                """,
                (a_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            try:
                media_list = json.loads(row["media_sha256"])
            except Exception:
                media_list = []
            return {
                "id": row["id"],
                "campaign_id": row["campaign_id"] or row["mission_id"],
                "platform": row["platform"],
                "account_id": row["account_id"],
                "content_sha256": row["content_sha256"],
                "media_sha256": media_list,
                "status": row["status"],
                "expires_at": row["expires_at"],
                "created_at": row["created_at"],
                "decided_at": row["decided_at"],
                "decided_by": row["decided_by"],
            }
        finally:
            conn.close()

    def update_approval(self, approval_id: Union[UUID, str], updates: dict) -> None:
        """Update fields of an existing approval record."""
        a_id = str(approval_id)
        set_clauses = []
        values = []
        for key, val in updates.items():
            set_clauses.append(f"{key} = ?")
            if isinstance(val, (dict, list)):
                values.append(json.dumps(val))
            else:
                values.append(str(val) if val is not None else None)
        values.append(a_id)
        with self._transaction(immediate=True) as conn:
            conn.execute(
                f"UPDATE approvals SET {', '.join(set_clauses)} WHERE id = ?",
                values,
            )

    def save_publication_attempt(self, attempt_data: dict) -> None:
        """Persist a publication attempt record."""
        p_id = str(attempt_data["id"])
        c_id = str(attempt_data["campaign_id"])
        app_id = str(attempt_data.get("approval_id") or "")
        with self._transaction(immediate=True) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO publication_attempts (
                    id, campaign_id, approval_id, platform, state,
                    remote_post_id, published_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p_id,
                    c_id,
                    app_id,
                    attempt_data["platform"],
                    attempt_data["state"],
                    attempt_data.get("remote_post_id"),
                    str(attempt_data["published_at"]) if attempt_data.get("published_at") else None,
                    str(attempt_data["created_at"]),
                ),
            )

    def get_publication_attempt(self, attempt_id: Union[UUID, str]) -> Optional[dict]:
        """Fetch a publication attempt record by ID."""
        p_id = str(attempt_id)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, campaign_id, approval_id, platform, state,
                       remote_post_id, published_at, created_at
                FROM publication_attempts WHERE id = ?
                """,
                (p_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "campaign_id": row["campaign_id"],
                "approval_id": row["approval_id"],
                "platform": row["platform"],
                "state": row["state"],
                "remote_post_id": row["remote_post_id"],
                "published_at": row["published_at"],
                "created_at": row["created_at"],
            }
        finally:
            conn.close()

    def update_publication_attempt_state(
        self,
        attempt_id: Union[UUID, str],
        state: str,
        remote_post_id: Optional[str] = None,
        published_at: Optional[str] = None,
    ) -> None:
        """Update the state (and optionally remote_post_id/published_at) of a publication attempt."""
        p_id = str(attempt_id)
        with self._transaction(immediate=True) as conn:
            if remote_post_id is not None and published_at is not None:
                conn.execute(
                    "UPDATE publication_attempts SET state = ?, remote_post_id = ?, published_at = ? WHERE id = ?",
                    (state, remote_post_id, published_at, p_id),
                )
            elif remote_post_id is not None:
                conn.execute(
                    "UPDATE publication_attempts SET state = ?, remote_post_id = ? WHERE id = ?",
                    (state, remote_post_id, p_id),
                )
            else:
                conn.execute(
                    "UPDATE publication_attempts SET state = ? WHERE id = ?",
                    (state, p_id),
                )

    def create_run(
        self,
        mission_id: Union[UUID, str],
        run_id: Union[UUID, str],
        executor: str,
        agent_profile: str,
        state: Union[MissionState, str] = MissionState.STARTING,
    ) -> RunRecord:
        """Create and persist a new mission run record."""
        r_id = str(run_id)
        m_id = str(mission_id)
        state_str = state.value if isinstance(state, MissionState) else str(state)
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()
            # Ensure mission exists to satisfy foreign key constraint in isolated tests
            cursor.execute("SELECT id FROM missions WHERE id = ?", (m_id,))
            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO missions (
                        id, project_slug, title, objective, primary_executor,
                        agent_profile, state, created_at, updated_at
                    )
                    VALUES (?, 'doh-nut', 'Mission for Run', 'Run execution', ?, ?, 'starting', ?, ?)
                    """,
                    (m_id, executor, agent_profile, now_iso, now_iso),
                )

            cursor.execute(
                """
                INSERT OR REPLACE INTO mission_runs (
                    id, mission_id, executor, agent_profile, state,
                    provider_conversation_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (r_id, m_id, executor, agent_profile, state_str, now_iso, now_iso),
            )

        return RunRecord({
            "id": r_id,
            "run_id": r_id,
            "mission_id": m_id,
            "executor": executor,
            "agent_profile": agent_profile,
            "state": MissionState(state_str),
            "provider_conversation_id": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        })

    def get_run(self, run_id: Union[UUID, str]) -> Optional[RunRecord]:
        """Fetch a mission run by its ID."""
        r_id = str(run_id)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, mission_id, executor, agent_profile, state,
                       provider_conversation_id, created_at, updated_at
                FROM mission_runs WHERE id = ?
                """,
                (r_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return RunRecord({
                "id": row["id"],
                "run_id": row["id"],
                "mission_id": row["mission_id"],
                "executor": row["executor"],
                "agent_profile": row["agent_profile"],
                "state": MissionState(row["state"]),
                "provider_conversation_id": row["provider_conversation_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })
        finally:
            conn.close()

    def update_run_state(
        self,
        run_id: Union[UUID, str],
        state: Union[MissionState, str],
        provider_conversation_id: Optional[str] = None,
    ) -> None:
        """Update the state of a mission run."""
        r_id = str(run_id)
        state_str = state.value if isinstance(state, MissionState) else str(state)
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()
            if provider_conversation_id is not None:
                cursor.execute(
                    "UPDATE mission_runs SET state = ?, provider_conversation_id = ?, updated_at = ? WHERE id = ?",
                    (state_str, provider_conversation_id, now_iso, r_id),
                )
            else:
                cursor.execute(
                    "UPDATE mission_runs SET state = ?, updated_at = ? WHERE id = ?",
                    (state_str, now_iso, r_id),
                )

    def set_run_provider_conversation_id(
        self, run_id: Union[UUID, str], conversation_id: str
    ) -> None:
        """Set the provider conversation ID for a run."""
        r_id = str(run_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE mission_runs SET provider_conversation_id = ?, updated_at = ? WHERE id = ?",
                (conversation_id, now_iso, r_id),
            )

    def get_incomplete_runs(self) -> List[RunRecord]:
        """Fetch all runs currently in STARTING or RUNNING state."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, mission_id, executor, agent_profile, state,
                       provider_conversation_id, created_at, updated_at
                FROM mission_runs WHERE state IN ('starting', 'running')
                """
            )
            rows = cursor.fetchall()
            return [
                RunRecord({
                    "id": row["id"],
                    "run_id": row["id"],
                    "mission_id": row["mission_id"],
                    "executor": row["executor"],
                    "agent_profile": row["agent_profile"],
                    "state": MissionState(row["state"]),
                    "provider_conversation_id": row["provider_conversation_id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                })
                for row in rows
            ]
        finally:
            conn.close()

    def create_running_run_without_result(
        self,
        mission_id: Optional[Union[UUID, str]] = None,
        run_id: Optional[Union[UUID, str]] = None,
    ) -> RunRecord:
        """Create a run in RUNNING state without a terminal result, for testing restart recovery."""
        m_id = mission_id or uuid.uuid4()
        r_id = run_id or uuid.uuid4()
        return self.create_run(
            mission_id=m_id,
            run_id=r_id,
            executor="agy",
            agent_profile="dohnut-orchestrator",
            state=MissionState.RUNNING,
        )

    def record_cost(
        self,
        run_id: Union[UUID, str],
        usage: Optional[UsageRecord] = None,
        duration_seconds: Optional[float] = None,
        cost_usd: Optional[float] = None,
    ) -> CostRecord:
        """Persist a token usage and cost record for a run."""
        r_id = str(run_id)
        rec_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        in_tok = usage.input_tokens if usage else 0
        out_tok = usage.output_tokens if usage else 0
        tot_tok = usage.total_tokens if usage else (in_tok + out_tok)

        if cost_usd is None:
            # Candidate rate: $0.15/1M input, $0.60/1M output
            calculated_cost = (in_tok * 0.00000015) + (out_tok * 0.00000060)
        else:
            calculated_cost = float(cost_usd)

        with self._transaction(immediate=True) as conn:
            conn.execute(
                """
                INSERT INTO cost_records (
                    id, run_id, input_tokens, output_tokens, total_tokens, cost_usd, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (rec_id, r_id, in_tok, out_tok, tot_tok, round(calculated_cost, 6), now_iso),
            )

        return CostRecord(
            id=rec_id,
            run_id=r_id,
            input_tokens=in_tok,
            output_tokens=out_tok,
            total_tokens=tot_tok,
            cost_usd=round(calculated_cost, 6),
            duration_seconds=duration_seconds,
            created_at=now_iso,
        )


def record_cost(
    run_id: Union[UUID, str],
    usage: Optional[UsageRecord] = None,
    duration_seconds: Optional[float] = None,
    store: Optional[MissionStore] = None,
) -> CostRecord:
    """Convenience module-level helper to record token cost."""
    if store is None:
        store = MissionStore()
    return store.record_cost(run_id=run_id, usage=usage, duration_seconds=duration_seconds)


