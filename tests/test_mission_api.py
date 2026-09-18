"""Integration tests for Mission REST API endpoints, idempotency, and CSRF protection."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.mission import PrimaryExecutor
from backend.services.mission_service import get_mission_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_agy_manager(monkeypatch):
    """Ensure AGY subprocess execution is mocked during API tests."""
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
def mission_payload():
    """Valid CreateMissionRequest payload."""
    return {
        "project_slug": "doh-nut",
        "title": "Automated Doh-Nut Operations",
        "objective": "Execute headless tests for remote ops",
        "primary_executor": "agy",
        "agent_profile": "dohnut-orchestrator",
        "idempotency_key": str(uuid.uuid4()),
    }


def test_create_mission_is_idempotent(authenticated_session, mission_payload):
    """First call creates mission (201), second call with same idempotency key returns 200."""
    headers = authenticated_session["headers"]
    cookies = authenticated_session["cookies"]

    # First call -> 201 Created
    first_resp = client.post("/api/missions", json=mission_payload, headers=headers, cookies=cookies)
    assert first_resp.status_code == 201, first_resp.text
    first_data = first_resp.json()
    assert "mission_id" in first_data
    assert first_data["state"] in ("queued", "starting", "running")
    assert "correlation_id" in first_data
    assert "next_action" in first_data

    # Second call (exact same idempotency key) -> 200 OK
    second_resp = client.post("/api/missions", json=mission_payload, headers=headers, cookies=cookies)
    assert second_resp.status_code == 200, second_resp.text
    second_data = second_resp.json()
    assert second_data["mission_id"] == first_data["mission_id"]
    assert second_data["correlation_id"] == first_data["correlation_id"]


def test_missing_csrf_on_create_mission_returns_403(authenticated_session, mission_payload):
    """POST /api/missions without valid CSRF header must return 403 Forbidden."""
    cookies = authenticated_session["cookies"]
    # Missing CSRF header
    resp = client.post("/api/missions", json=mission_payload, cookies=cookies)
    assert resp.status_code == 403

    # Invalid CSRF header
    resp_bad = client.post(
        "/api/missions",
        json=mission_payload,
        cookies=cookies,
        headers={"X-CSRF-Token": "bad-token"},
    )
    assert resp_bad.status_code == 403


def test_second_turn_returns_202_and_queued_state(authenticated_session, mission_payload):
    """Submitting a turn returns 202 Accepted with state='queued'."""
    headers = authenticated_session["headers"]
    cookies = authenticated_session["cookies"]

    create_resp = client.post("/api/missions", json=mission_payload, headers=headers, cookies=cookies)
    assert create_resp.status_code == 201
    mission_id = create_resp.json()["mission_id"]

    turn_payload = {
        "message": "Proceed with step 1 instructions.",
        "idempotency_key": str(uuid.uuid4()),
    }

    turn_resp = client.post(
        f"/api/missions/{mission_id}/turns",
        json=turn_payload,
        headers=headers,
        cookies=cookies,
    )
    assert turn_resp.status_code == 202, turn_resp.text
    turn_data = turn_resp.json()
    assert turn_data["state"] == "queued"
    assert "turn_id" in turn_data
    assert turn_data["sequence"] >= 1


def test_get_mission_and_list_missions(authenticated_session, mission_payload):
    """GET /api/missions and GET /api/missions/{id} return expected data."""
    headers = authenticated_session["headers"]
    cookies = authenticated_session["cookies"]

    create_resp = client.post("/api/missions", json=mission_payload, headers=headers, cookies=cookies)
    assert create_resp.status_code == 201
    mission_id = create_resp.json()["mission_id"]

    # List missions
    list_resp = client.get("/api/missions", headers=headers, cookies=cookies)
    assert list_resp.status_code == 200
    missions = list_resp.json()
    assert isinstance(missions, list)
    assert any(m["id"] == mission_id or m.get("mission_id") == mission_id for m in missions)

    # Get specific mission
    get_resp = client.get(f"/api/missions/{mission_id}", headers=headers, cookies=cookies)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == mission_id


def test_get_mission_nonexistent_returns_404(authenticated_session):
    """GET /api/missions/{invalid_id} returns 404 Not Found."""
    fake_id = str(uuid.uuid4())
    resp = client.get(
        f"/api/missions/{fake_id}",
        headers=authenticated_session["headers"],
        cookies=authenticated_session["cookies"],
    )
    assert resp.status_code == 404


def test_cancel_mission(authenticated_session, mission_payload):
    """POST /api/missions/{id}/cancel returns status cancelled."""
    headers = authenticated_session["headers"]
    cookies = authenticated_session["cookies"]

    create_resp = client.post("/api/missions", json=mission_payload, headers=headers, cookies=cookies)
    mission_id = create_resp.json()["mission_id"]

    cancel_resp = client.post(
        f"/api/missions/{mission_id}/cancel",
        headers=headers,
        cookies=cookies,
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"


def test_get_capabilities():
    """GET /api/capabilities returns list of capability profiles."""
    resp = client.get("/api/capabilities")
    assert resp.status_code == 200
    caps = resp.json()
    assert isinstance(caps, list)
    assert len(caps) > 0
    cap_names = [c.get("name") for c in caps]
    assert "plan" in cap_names or any("plan" in str(c) for c in caps)
