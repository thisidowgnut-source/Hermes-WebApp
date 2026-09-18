"""Unit and integration tests for SQLite WAL durable scheduler and crash recovery."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services.durable_scheduler import (
    DurableSchedulerService,
    ScheduledJob,
    get_durable_scheduler,
    set_durable_scheduler,
)
from backend.services.social_delivery import DeliveryResult, SocialDeliveryRegistry


@pytest.fixture
def scheduler(tmp_path: Path):
    """Provide an isolated DurableSchedulerService instance using a temp database."""
    db_file = tmp_path / "test_scheduled_jobs.db"
    service = DurableSchedulerService(db_path=db_file)
    service.initialize_table()
    return service


def test_table_initialization(tmp_path: Path):
    """Test table initialization creates scheduled_jobs table and WAL mode indices."""
    db_file = tmp_path / "init_test.db"
    service = DurableSchedulerService(db_path=db_file)
    service.initialize_table()

    conn = service._get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scheduled_jobs'")
        assert cursor.fetchone() is not None, "scheduled_jobs table must exist"

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_scheduled_jobs_dispatch'")
        assert cursor.fetchone() is not None, "idx_scheduled_jobs_dispatch index must exist"
    finally:
        conn.close()


def test_schedule_job_persists_with_pending_state(scheduler: DurableSchedulerService):
    """Test schedule_job inserts job with pending status and valid timestamps."""
    execute_at = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {"caption": "Doh-Nut viral recipe", "hashtags": ["#dohnut", "#viral"]}
    campaign_id = uuid.uuid4()

    job = scheduler.schedule_job(
        project_slug="doh-nut",
        platform="tiktok",
        action="submit",
        payload=payload,
        execute_at=execute_at,
        campaign_id=campaign_id,
    )

    assert isinstance(job, ScheduledJob)
    assert job.status == "pending"
    assert job.attempts == 0
    assert job.max_attempts == 3
    assert job.campaign_id == campaign_id
    assert job.project_slug == "doh-nut"
    assert job.platform == "tiktok"
    assert job.action == "submit"
    assert job.payload == payload
    assert job.last_error is None
    assert job.receipt is None

    # Verify persisted in database
    retrieved = scheduler.get_job(job.id)
    assert retrieved is not None
    assert retrieved.id == job.id
    assert retrieved.status == "pending"
    assert retrieved.payload == payload
    assert retrieved.campaign_id == campaign_id


def test_cancel_job_updates_state_to_cancelled(scheduler: DurableSchedulerService):
    """Test cancel_job marks an existing job as cancelled and returns True."""
    execute_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    job = scheduler.schedule_job(
        project_slug="doh-nut",
        platform="instagram",
        action="publish",
        payload={"text": "Fresh Glaze Dropping at 3PM!"},
        execute_at=execute_at,
    )

    success = scheduler.cancel_job(job.id)
    assert success is True

    updated = scheduler.get_job(job.id)
    assert updated is not None
    assert updated.status == "cancelled"

    # Cancelling a non-existent job returns False
    assert scheduler.cancel_job(uuid.uuid4()) is False


@pytest.mark.asyncio
async def test_poll_and_execute_due_jobs_executes_and_completes(scheduler: DurableSchedulerService):
    """Test poll_and_execute_due_jobs processes jobs where execute_at <= now and marks them completed."""
    mock_registry = MagicMock(spec=SocialDeliveryRegistry)
    mock_adapter = MagicMock()
    mock_adapter.submit.return_value = DeliveryResult(
        attempt_id=uuid.uuid4(),
        state="published",
        remote_post_id="tiktok_post_12345",
        receipt={"post_id": "tiktok_post_12345", "status": "success"},
        message="Delivered successfully",
    )
    mock_registry.adapter_for.return_value = mock_adapter
    scheduler.delivery_registry = mock_registry

    # Schedule a job in the past (due immediately)
    past_due = datetime.now(timezone.utc) - timedelta(seconds=10)
    job = scheduler.schedule_job(
        project_slug="doh-nut",
        platform="tiktok",
        action="submit",
        payload={"video_url": "https://cdn.dohnut.my/video1.mp4"},
        execute_at=past_due,
    )

    count = await scheduler.poll_and_execute_due_jobs()
    assert count == 1

    executed_job = scheduler.get_job(job.id)
    assert executed_job is not None
    assert executed_job.status == "completed"
    assert executed_job.attempts == 1
    assert executed_job.receipt is not None
    assert executed_job.receipt.get("post_id") == "tiktok_post_12345"


@pytest.mark.asyncio
async def test_jobs_with_execute_at_in_future_are_not_executed(scheduler: DurableSchedulerService):
    """Test that jobs with execute_at in the future are ignored during polling."""
    mock_registry = MagicMock(spec=SocialDeliveryRegistry)
    scheduler.delivery_registry = mock_registry

    # Schedule a future job
    future_time = datetime.now(timezone.utc) + timedelta(minutes=15)
    job = scheduler.schedule_job(
        project_slug="doh-nut",
        platform="x",
        action="submit",
        payload={"tweet": "Coming soon in 15 mins!"},
        execute_at=future_time,
    )

    count = await scheduler.poll_and_execute_due_jobs()
    assert count == 0

    unexecuted = scheduler.get_job(job.id)
    assert unexecuted is not None
    assert unexecuted.status == "pending"
    assert unexecuted.attempts == 0
    mock_registry.adapter_for.assert_not_called()


def test_startup_reconciliation_resets_interrupted_running_jobs(scheduler: DurableSchedulerService):
    """Test startup reconciliation recovers running jobs to pending if attempts < max_attempts."""
    execute_at = datetime.now(timezone.utc)
    job1 = scheduler.schedule_job(
        project_slug="doh-nut",
        platform="instagram",
        action="publish",
        payload={"caption": "Running job 1"},
        execute_at=execute_at,
    )
    job2 = scheduler.schedule_job(
        project_slug="doh-nut",
        platform="threads",
        action="publish",
        payload={"caption": "Running job 2 exceeding max"},
        execute_at=execute_at,
    )

    # Manually simulate server crash during execution
    with scheduler._transaction() as conn:
        conn.execute(
            "UPDATE scheduled_jobs SET status = 'running', attempts = 1, max_attempts = 3 WHERE id = ?",
            (str(job1.id),),
        )
        conn.execute(
            "UPDATE scheduled_jobs SET status = 'running', attempts = 3, max_attempts = 3 WHERE id = ?",
            (str(job2.id),),
        )

    reconciled_count = scheduler.reconcile_startup()
    assert reconciled_count == 2

    # job1 has attempts=1 < max_attempts=3 -> should be pending
    rec_job1 = scheduler.get_job(job1.id)
    assert rec_job1.status == "pending"

    # job2 has attempts=3 >= max_attempts=3 -> should be interrupted
    rec_job2 = scheduler.get_job(job2.id)
    assert rec_job2.status == "interrupted"


@pytest.mark.asyncio
async def test_execution_failure_retries_then_fails(scheduler: DurableSchedulerService):
    """Test that failed execution increments attempts and marks failed after max_attempts."""
    mock_registry = MagicMock(spec=SocialDeliveryRegistry)
    mock_adapter = MagicMock()
    mock_adapter.submit.side_effect = RuntimeError("Network timeout to social provider")
    mock_registry.adapter_for.return_value = mock_adapter
    scheduler.delivery_registry = mock_registry

    past_due = datetime.now(timezone.utc) - timedelta(seconds=5)
    job = scheduler.schedule_job(
        project_slug="doh-nut",
        platform="tiktok",
        action="submit",
        payload={"video": "fail.mp4"},
        execute_at=past_due,
    )

    # Attempt 1 -> fails, status resets to pending
    await scheduler.poll_and_execute_due_jobs()
    j1 = scheduler.get_job(job.id)
    assert j1.status == "pending"
    assert j1.attempts == 1
    assert "Network timeout" in str(j1.last_error)

    # Attempt 2 -> fails, status resets to pending
    await scheduler.poll_and_execute_due_jobs()
    j2 = scheduler.get_job(job.id)
    assert j2.status == "pending"
    assert j2.attempts == 2

    # Attempt 3 -> reaches max_attempts (3), status marks failed
    await scheduler.poll_and_execute_due_jobs()
    j3 = scheduler.get_job(job.id)
    assert j3.status == "failed"
    assert j3.attempts == 3


def test_list_jobs_filtering(scheduler: DurableSchedulerService):
    """Test list_jobs filters by status and platform correctly."""
    t_now = datetime.now(timezone.utc)
    j_tiktok = scheduler.schedule_job("doh-nut", "tiktok", "submit", {}, t_now)
    j_ig = scheduler.schedule_job("doh-nut", "instagram", "submit", {}, t_now + timedelta(minutes=5))
    j_x = scheduler.schedule_job("doh-nut", "x", "submit", {}, t_now + timedelta(minutes=10))

    scheduler.cancel_job(j_x.id)

    # Filter by platform
    tiktok_jobs = scheduler.list_jobs(platform="tiktok")
    assert len(tiktok_jobs) == 1
    assert tiktok_jobs[0].id == j_tiktok.id

    # Filter by status
    pending_jobs = scheduler.list_jobs(status="pending")
    assert len(pending_jobs) == 2

    cancelled_jobs = scheduler.list_jobs(status="cancelled")
    assert len(cancelled_jobs) == 1
    assert cancelled_jobs[0].id == j_x.id


def test_singleton_get_and_set():
    """Test get_durable_scheduler and set_durable_scheduler singleton management."""
    custom_service = DurableSchedulerService(db_path=":memory:")
    set_durable_scheduler(custom_service)

    assert get_durable_scheduler() is custom_service

    # Reset
    set_durable_scheduler(None)
    new_service = get_durable_scheduler()
    assert new_service is not None
    assert new_service is not custom_service
    set_durable_scheduler(None)
