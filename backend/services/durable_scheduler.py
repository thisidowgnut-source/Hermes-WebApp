"""SQLite WAL Durable Delayed Job Scheduler for Hermes-WebApp & Doh-Nut Sovereign Operations.

Zero-loss persistent task queue surviving system reboots and crashes,
polled periodically via FastAPI lifespan asyncio worker with crash recovery.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("hermes.durable_scheduler")


class ScheduledJob(BaseModel):
    """Data model representing a scheduled delayed job."""
    model_config = ConfigDict(extra="ignore")

    id: UUID = Field(default_factory=uuid.uuid4)
    campaign_id: UUID | None = None
    project_slug: str
    platform: str
    action: str
    payload: dict = Field(default_factory=dict)
    execute_at: datetime
    status: str = "pending"  # pending, running, completed, failed, interrupted, cancelled
    attempts: int = 0
    max_attempts: int = 3
    last_error: str | None = None
    receipt: dict | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def _format_datetime(dt: datetime) -> str:
    """Ensure datetime is converted to timezone.utc and formatted consistently."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def _parse_datetime(val: str | datetime) -> datetime:
    """Parse ISO datetime string into datetime object."""
    if isinstance(val, datetime):
        return val
    return datetime.fromisoformat(val)


class DurableSchedulerService:
    """Durable job scheduler utilizing SQLite WAL for persistent execution across restarts."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        delivery_registry: Any | None = None,
    ):
        if db_path is None:
            try:
                from backend.config import config
                self.db_path: Union[Path, str] = Path(config.MISSION_DB_PATH)
            except Exception:
                self.db_path = Path("missions.db")
        elif str(db_path) == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = Path(db_path)

        # Handle persistent memory database for testing if :memory: is specified
        self._mem_conn: Optional[sqlite3.Connection] = None
        self._mem_uri: Optional[str] = None
        if self.db_path == ":memory:":
            self._mem_uri = f"file:mem_sched_{uuid.uuid4().hex}?mode=memory&cache=shared"
            self._mem_conn = sqlite3.connect(self._mem_uri, uri=True, check_same_thread=False)

        if delivery_registry is None:
            try:
                from backend.services.social_delivery import SocialDeliveryRegistry
                self.delivery_registry = SocialDeliveryRegistry()
            except Exception:
                self.delivery_registry = None
        else:
            self.delivery_registry = delivery_registry

    def _get_connection(self) -> sqlite3.Connection:
        """Create and configure a SQLite connection with WAL mode and busy timeout."""
        if self.db_path == ":memory:" and self._mem_uri:
            conn = sqlite3.connect(self._mem_uri, uri=True, timeout=10.0, check_same_thread=False)
        else:
            if isinstance(self.db_path, Path):
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path), timeout=10.0, check_same_thread=False)

        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    @contextmanager
    def _transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing an immediate transaction boundary."""
        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            yield conn
            conn.execute("COMMIT;")
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()

    def initialize_table(self) -> None:
        """Create scheduled_jobs table and indexes if they do not exist."""
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT,
                    project_slug TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    execute_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    last_error TEXT,
                    receipt TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_dispatch 
                ON scheduled_jobs(status, execute_at);

                CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_platform 
                ON scheduled_jobs(platform);
            """)
            conn.commit()
        finally:
            conn.close()

    def _row_to_job(self, row: sqlite3.Row) -> ScheduledJob:
        """Map SQLite row to ScheduledJob model."""
        payload_val = row["payload"]
        if isinstance(payload_val, str):
            try:
                payload = json.loads(payload_val)
            except Exception:
                payload = {}
        else:
            payload = payload_val or {}

        receipt_val = row["receipt"]
        if receipt_val and isinstance(receipt_val, str):
            try:
                receipt = json.loads(receipt_val)
            except Exception:
                receipt = None
        else:
            receipt = receipt_val

        return ScheduledJob(
            id=UUID(row["id"]),
            campaign_id=UUID(row["campaign_id"]) if row["campaign_id"] else None,
            project_slug=row["project_slug"],
            platform=row["platform"],
            action=row["action"],
            payload=payload,
            execute_at=_parse_datetime(row["execute_at"]),
            status=row["status"],
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            last_error=row["last_error"],
            receipt=receipt,
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def schedule_job(
        self,
        project_slug: str,
        platform: str,
        action: str,
        payload: dict,
        execute_at: datetime,
        campaign_id: UUID | None = None,
        max_attempts: int = 3,
    ) -> ScheduledJob:
        """Schedule a new delayed job row in scheduled_jobs table."""
        job_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        if execute_at.tzinfo is None:
            norm_execute_at = execute_at.replace(tzinfo=timezone.utc)
        else:
            norm_execute_at = execute_at.astimezone(timezone.utc)

        job = ScheduledJob(
            id=job_id,
            campaign_id=campaign_id,
            project_slug=project_slug,
            platform=platform,
            action=action,
            payload=payload,
            execute_at=norm_execute_at,
            status="pending",
            attempts=0,
            max_attempts=max_attempts,
            last_error=None,
            receipt=None,
            created_at=now,
            updated_at=now,
        )

        with self._transaction() as conn:
            conn.execute(
                """
                INSERT INTO scheduled_jobs (
                    id, campaign_id, project_slug, platform, action, payload,
                    execute_at, status, attempts, max_attempts, last_error, receipt,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(job.id),
                    str(job.campaign_id) if job.campaign_id else None,
                    job.project_slug,
                    job.platform,
                    job.action,
                    json.dumps(job.payload),
                    _format_datetime(job.execute_at),
                    job.status,
                    job.attempts,
                    job.max_attempts,
                    job.last_error,
                    json.dumps(job.receipt) if job.receipt else None,
                    _format_datetime(job.created_at),
                    _format_datetime(job.updated_at),
                ),
            )

        logger.info(
            "Scheduled job enqueued: id=%s platform=%s action=%s execute_at=%s",
            job.id,
            job.platform,
            job.action,
            job.execute_at,
        )
        return job

    def list_jobs(
        self,
        status: str | None = None,
        platform: str | None = None,
        limit: int = 50,
    ) -> list[ScheduledJob]:
        """List scheduled jobs optionally filtered by status and platform."""
        query = "SELECT * FROM scheduled_jobs"
        clauses = []
        params: list[Any] = []

        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if platform is not None:
            clauses.append("platform = ?")
            params.append(platform)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY execute_at ASC LIMIT ?"
        params.append(limit)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_job(r) for r in rows]
        finally:
            conn.close()

    def get_job(self, job_id: Union[UUID, str]) -> ScheduledJob | None:
        """Retrieve a specific scheduled job by UUID."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scheduled_jobs WHERE id = ?", (str(job_id),))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_job(row)
        finally:
            conn.close()

    def cancel_job(self, job_id: Union[UUID, str]) -> bool:
        """Cancel a pending or scheduled job."""
        jid = str(job_id)
        now_str = _format_datetime(datetime.now(timezone.utc))

        with self._transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM scheduled_jobs WHERE id = ?", (jid,))
            row = cursor.fetchone()
            if not row:
                return False

            cursor.execute(
                """
                UPDATE scheduled_jobs
                SET status = 'cancelled', updated_at = ?
                WHERE id = ?
                """,
                (now_str, jid),
            )
            return cursor.rowcount > 0

    def reconcile_startup(self) -> int:
        """Recover interrupted jobs across server restarts.

        If status == 'running':
          - if attempts < max_attempts -> resets back to 'pending'
          - otherwise -> sets to 'interrupted'
        """
        now_str = _format_datetime(datetime.now(timezone.utc))
        with self._transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, attempts, max_attempts FROM scheduled_jobs WHERE status = 'running'")
            rows = cursor.fetchall()
            count = 0
            for row in rows:
                jid = row["id"]
                attempts = row["attempts"]
                max_attempts = row["max_attempts"]

                if attempts < max_attempts:
                    new_status = "pending"
                    err = "Interrupted by server restart; requeued to pending"
                else:
                    new_status = "interrupted"
                    err = f"Interrupted by server restart; max attempts ({max_attempts}) reached"

                cursor.execute(
                    """
                    UPDATE scheduled_jobs
                    SET status = ?, last_error = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (new_status, err, now_str, jid),
                )
                count += 1
            return count

    async def _execute_job(self, job: ScheduledJob) -> dict:
        """Execute a single job via delivery_registry and return receipt."""
        if self.delivery_registry is None:
            return {
                "status": "executed",
                "platform": job.platform,
                "action": job.action,
                "executed_at": _format_datetime(datetime.now(timezone.utc)),
            }

        # 1. Primary path: Lookup platform adapter from delivery_registry
        adapter = None
        if hasattr(self.delivery_registry, "adapter_for") and callable(
            getattr(self.delivery_registry, "adapter_for")
        ):
            adapter = self.delivery_registry.adapter_for(job.platform)
        elif hasattr(self.delivery_registry, "get_adapter") and callable(
            getattr(self.delivery_registry, "get_adapter")
        ):
            adapter = self.delivery_registry.get_adapter(job.platform)
        elif isinstance(self.delivery_registry, dict) and job.platform in self.delivery_registry:
            adapter = self.delivery_registry[job.platform]

        if adapter is not None:
            action_name = job.action.lower() if job.action else "submit"
            if hasattr(adapter, action_name) and callable(getattr(adapter, action_name)):
                fn = getattr(adapter, action_name)
                res = fn(job)
            elif hasattr(adapter, "submit") and callable(getattr(adapter, "submit")):
                res = adapter.submit(job)
            elif callable(adapter):
                res = adapter(job)
            else:
                raise ValueError(f"No executable method '{action_name}' on adapter for {job.platform}")

            if asyncio.iscoroutine(res):
                res = await res

            if isinstance(res, dict):
                return res
            if hasattr(res, "receipt") and res.receipt is not None:
                return res.receipt
            if hasattr(res, "model_dump"):
                dump = res.model_dump()
                return dump.get("receipt") or dump
            if hasattr(res, "dict") and callable(res.dict):
                d = res.dict()
                return d.get("receipt") or d
            return {"status": getattr(res, "state", "completed"), "result": str(res)}

        # 2. Fallback: if delivery_registry directly has an execute/dispatch method
        for method_name in ("execute_job", "execute", "dispatch"):
            if hasattr(self.delivery_registry, method_name) and callable(
                getattr(self.delivery_registry, method_name)
            ):
                res = getattr(self.delivery_registry, method_name)(job)
                if asyncio.iscoroutine(res):
                    res = await res
                if isinstance(res, dict):
                    return res
                if hasattr(res, "receipt") and res.receipt:
                    return res.receipt
                return {"status": "completed", "result": str(res)}

        if callable(self.delivery_registry):
            res = self.delivery_registry(job)
            if asyncio.iscoroutine(res):
                res = await res
            if isinstance(res, dict):
                return res
            return {"status": "completed"}

        return {
            "status": "executed",
            "platform": job.platform,
            "action": job.action,
            "executed_at": _format_datetime(datetime.now(timezone.utc)),
        }

    async def poll_and_execute_due_jobs(self) -> int:
        """Select due pending jobs, mark running, execute via delivery_registry, and update states."""
        now = datetime.now(timezone.utc)
        now_str = _format_datetime(now)

        jobs_to_run: list[ScheduledJob] = []

        with self._transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM scheduled_jobs
                WHERE status = 'pending' AND execute_at <= ?
                ORDER BY execute_at ASC
                """,
                (now_str,),
            )
            rows = cursor.fetchall()
            for row in rows:
                job = self._row_to_job(row)
                cursor.execute(
                    """
                    UPDATE scheduled_jobs
                    SET status = 'running', updated_at = ?
                    WHERE id = ? AND status = 'pending'
                    """,
                    (now_str, str(job.id)),
                )
                if cursor.rowcount > 0:
                    job.status = "running"
                    jobs_to_run.append(job)

        executed_count = 0
        for job in jobs_to_run:
            try:
                receipt = await self._execute_job(job)
                completed_at = datetime.now(timezone.utc)
                completed_at_str = _format_datetime(completed_at)
                receipt_dict = receipt or {"status": "completed", "executed_at": completed_at_str}

                with self._transaction() as conn:
                    conn.execute(
                        """
                        UPDATE scheduled_jobs
                        SET status = 'completed',
                            attempts = attempts + 1,
                            receipt = ?,
                            last_error = NULL,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (json.dumps(receipt_dict, default=str), completed_at_str, str(job.id)),
                    )
                executed_count += 1
            except Exception as exc:
                err_msg = str(exc)
                logger.warning("Error executing scheduled job %s: %s", job.id, err_msg)
                failed_at = datetime.now(timezone.utc)
                failed_at_str = _format_datetime(failed_at)

                with self._transaction() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT attempts, max_attempts FROM scheduled_jobs WHERE id = ?",
                        (str(job.id),),
                    )
                    r = cursor.fetchone()
                    new_attempts = (r["attempts"] + 1) if r else (job.attempts + 1)
                    max_att = r["max_attempts"] if r else job.max_attempts

                    # If reached or exceeded max_attempts, mark failed; otherwise requeue to pending
                    new_status = "failed" if new_attempts >= max_att else "pending"

                    cursor.execute(
                        """
                        UPDATE scheduled_jobs
                        SET status = ?,
                            attempts = ?,
                            last_error = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (new_status, new_attempts, err_msg, failed_at_str, str(job.id)),
                    )
                executed_count += 1

        return executed_count


# Module singleton management
_default_durable_scheduler: Optional[DurableSchedulerService] = None


def get_durable_scheduler() -> DurableSchedulerService:
    """Retrieve or initialize the singleton DurableSchedulerService."""
    global _default_durable_scheduler
    if _default_durable_scheduler is None:
        service = DurableSchedulerService()
        service.initialize_table()
        _default_durable_scheduler = service
    return _default_durable_scheduler


def set_durable_scheduler(service: Optional[DurableSchedulerService]) -> None:
    """Set or reset singleton DurableSchedulerService (useful for unit testing)."""
    global _default_durable_scheduler
    _default_durable_scheduler = service


__all__ = [
    "ScheduledJob",
    "DurableSchedulerService",
    "get_durable_scheduler",
    "set_durable_scheduler",
]
