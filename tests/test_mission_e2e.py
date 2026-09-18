"""End-to-End Acceptance Tests for Hermes-WebApp AGY Remote Operations (Task 13)."""
from __future__ import annotations

import uuid
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.mission import (
    CreateMissionRequest,
    CreateTurnRequest,
    MissionState,
    OperatorContext,
    PrimaryExecutor,
)
from backend.services.session_auth import session_auth_service
from backend.services.mission_service import get_mission_service
from backend.services.social_campaign_service import (
    Campaign,
    PublicationAttempt,
    PublicationState,
    SocialCampaignService,
)
from backend.services.social_delivery import (
    ManualConfirmationAdapter,
    MissingPublicationReceipt,
    SocialDeliveryRegistry,
)


from unittest.mock import AsyncMock

@pytest.fixture(autouse=True)
def mock_agy_manager(monkeypatch):
    """Ensure AGY subprocess execution is mocked during E2E API tests."""
    service = get_mission_service()
    mock_start = AsyncMock()
    mock_enqueue = AsyncMock()
    mock_cancel = AsyncMock()
    monkeypatch.setattr(service.agy_manager, "start_run", mock_start)
    monkeypatch.setattr(service.agy_manager, "enqueue_turn", mock_enqueue)
    monkeypatch.setattr(service.agy_manager, "cancel_run", mock_cancel)
    return {
        "start_run": mock_start,
        "enqueue_turn": mock_enqueue,
        "cancel_run": mock_cancel,
    }


@pytest.fixture
def auth_headers(authenticated_session):
    return {
        "X-CSRF-Token": authenticated_session["csrf_token"],
        "Cookie": f"hermes_session={authenticated_session['session_token']}",
    }


def test_operator_can_create_resume_and_replay_a_doh_nut_agy_mission(client, auth_headers):
    """E2E flow: An operator creates a mission, replays it idempotently, posts a turn, and verifies event cursors."""
    service = get_mission_service()
    idempotency_key = uuid4()

    payload = {
        "project_slug": "doh-nut",
        "agent_profile": "dohnut-social-autopilot",
        "title": "E2E Autopilot Test Mission",
        "objective": "Prepare viral marketing campaign without auto-publishing",
        "primary_executor": "agy",
        "idempotency_key": str(idempotency_key),
    }

    # 1. Create Mission (201 Created)
    res = client.post("/api/missions", json=payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    mission_id = data["mission_id"]
    assert data["state"] == "queued"
    assert data["project_slug"] == "doh-nut"

    # 2. Idempotent Replay (200 OK with same mission_id)
    replay_res = client.post("/api/missions", json=payload, headers=auth_headers)
    assert replay_res.status_code == 200
    replay_data = replay_res.json()
    assert replay_data["mission_id"] == mission_id

    # 3. Post a second turn (202 Accepted)
    turn_payload = {
        "message": "Step 2: Generate TikTok and Threads draft copy only.",
        "idempotency_key": str(uuid4()),
    }
    turn_res = client.post(f"/api/missions/{mission_id}/turns", json=turn_payload, headers=auth_headers)
    assert turn_res.status_code == 202
    turn_data = turn_res.json()
    assert turn_data["state"] == "queued"

    # 4. Fetch durable events with monotonic sequence cursor
    events_res = client.get(f"/api/missions/{mission_id}/events?after_sequence=0", headers=auth_headers)
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 2

    # Check monotonic sequences
    sequences = [e["sequence"] for e in events]
    assert sequences == sorted(sequences)

    # Check cursor replay
    last_seq = sequences[-1]
    filtered_events = client.get(f"/api/missions/{mission_id}/events?after_sequence={last_seq}", headers=auth_headers).json()
    assert len(filtered_events) == 0


def test_social_action_requires_approval_receipt_and_reconciliation(client, auth_headers):
    """E2E flow: Social publication attempts require approval, strict receipts, and reconciliation."""
    from datetime import datetime, timezone
    registry = SocialDeliveryRegistry(default_adapter_type="manual")
    adapter = registry.adapter_for("tiktok")
    assert adapter.capabilities().requires_human_confirmation is True

    attempt_id = uuid4()
    campaign_id = uuid4()
    approval_id = uuid4()
    attempt = PublicationAttempt(
        id=attempt_id,
        campaign_id=campaign_id,
        approval_id=approval_id,
        platform="tiktok",
        state="prepared",
        created_at=datetime.now(timezone.utc),
    )

    # 1. Prepare
    prep_res = adapter.prepare(attempt)
    assert prep_res.state == "prepared"
    assert prep_res.remote_post_id is None

    # 2. Submit awaiting confirmation
    sub_res = adapter.submit(attempt)
    assert sub_res.state == "submitted"
    assert sub_res.remote_post_id is None

    # 3. Cannot mark published without receipt
    with pytest.raises(MissingPublicationReceipt):
        adapter.mark_published(attempt_id, receipt=None)

    with pytest.raises(MissingPublicationReceipt):
        adapter.mark_published(attempt_id, receipt={})

    # 4. Mark published with valid receipt
    pub_res = adapter.mark_published(attempt_id, receipt={"remote_post_id": "tt_123456", "views": 0})
    assert pub_res.state == "published"
    assert pub_res.remote_post_id == "tt_123456"

    # 5. Unknown attempt reconciliation
    reconciled_pub = adapter.reconcile(attempt_id, resolved_status="published")
    assert reconciled_pub.state == "published"

    reconciled_fail = adapter.reconcile(attempt_id, resolved_status="failed")
    assert reconciled_fail.state == "failed"


def test_unauthenticated_requests_strictly_rejected(client):
    """Any attempt to access mission operations without session or CSRF is strictly rejected."""
    # Missing session
    res = client.post("/api/missions", json={"title": "Hacker Mission"})
    assert res.status_code in (401, 403)

    # Missing session on turns
    res2 = client.post(f"/api/missions/{uuid4()}/turns", json={"message": "Hacker Turn"})
    assert res2.status_code in (401, 403)
