"""Tests for durable event cursor filtering, WebSocket ticket authentication, and event fan-out."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock
import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.mission_service import get_mission_service
from backend.services.session_auth import session_auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_agy_manager(monkeypatch):
    """Mock AGY manager subprocess execution."""
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
def test_mission(authenticated_session):
    """Creates a fresh mission in store and returns its snapshot dict."""
    service = get_mission_service()
    payload = {
        "project_slug": "doh-nut",
        "title": "Events Test Mission",
        "objective": "Verify cursor and replay behavior",
        "primary_executor": "agy",
        "agent_profile": "dohnut-orchestrator",
        "idempotency_key": str(uuid.uuid4()),
    }
    resp = client.post(
        "/api/missions",
        json=payload,
        headers=authenticated_session["headers"],
        cookies=authenticated_session["cookies"],
    )
    assert resp.status_code == 201
    return resp.json()


def test_event_cursor_replays_only_new_events(authenticated_session, test_mission):
    """REST event cursor: query after_sequence=0 returns initial events; query after last sequence returns empty."""
    headers = authenticated_session["headers"]
    cookies = authenticated_session["cookies"]
    m_id = test_mission["mission_id"]

    # Initial events query
    first_resp = client.get(f"/api/missions/{m_id}/events?after_sequence=0", headers=headers, cookies=cookies)
    assert first_resp.status_code == 200
    first_events = first_resp.json()
    assert len(first_events) >= 1
    last_seq = first_events[-1]["sequence"]

    # Query with after_sequence = last_seq -> empty list
    second_resp = client.get(f"/api/missions/{m_id}/events?after_sequence={last_seq}", headers=headers, cookies=cookies)
    assert second_resp.status_code == 200
    second_events = second_resp.json()
    assert len(second_events) == 0

    # Add another turn -> triggers new event
    turn_resp = client.post(
        f"/api/missions/{m_id}/turns",
        json={"message": "Step 2 message", "idempotency_key": str(uuid.uuid4())},
        headers=headers,
        cookies=cookies,
    )
    assert turn_resp.status_code == 202

    # Query with after_sequence = last_seq again -> only the new event
    third_resp = client.get(f"/api/missions/{m_id}/events?after_sequence={last_seq}", headers=headers, cookies=cookies)
    assert third_resp.status_code == 200
    third_events = third_resp.json()
    assert len(third_events) == 1
    assert third_events[0]["sequence"] > last_seq
    assert third_events[0]["event_type"] == "turn.enqueued"


def test_websocket_ticket_authentication_invalid_closes_4401(test_mission):
    """Connecting with an invalid ticket closes with code 4401."""
    m_id = test_mission["mission_id"]

    with client.websocket_connect(f"/ws/missions/{m_id}") as ws:
        ws.send_json({"ticket": "invalid_ticket_xyz", "after_sequence": 0})
        with pytest.raises(WebSocketDisconnect) as exc_info:
            ws.receive_json()
        assert exc_info.value.code == 4401


def test_websocket_ticket_replay_and_live_stream(authenticated_session, test_mission):
    """Valid ticket replays past events from cursor and streams new live events."""
    headers = authenticated_session["headers"]
    cookies = authenticated_session["cookies"]
    m_id = test_mission["mission_id"]

    # 1. Mint ticket
    ticket_resp = client.post(
        "/api/auth/websocket-ticket",
        headers={"X-CSRF-Token": authenticated_session["csrf_token"]},
        cookies=cookies,
    )
    assert ticket_resp.status_code == 200
    ticket = ticket_resp.json()["ticket"]

    # 2. Connect via WebSocket and request events after_sequence=0
    with client.websocket_connect(f"/ws/missions/{m_id}") as ws:
        ws.send_json({"ticket": ticket, "after_sequence": 0})

        # Receive at least the initial event
        ev1 = ws.receive_json()
        assert "event_type" in ev1
        assert ev1["sequence"] >= 1
        last_seq = ev1["sequence"]

        # Read any remaining backlog events
        while True:
            events = client.get(f"/api/missions/{m_id}/events?after_sequence={last_seq}", headers=headers, cookies=cookies).json()
            if not events:
                break
            ev = ws.receive_json()
            last_seq = ev["sequence"]

        # 3. Submit a new turn through REST API
        turn_resp = client.post(
            f"/api/missions/{m_id}/turns",
            json={"message": "Live streamed turn", "idempotency_key": str(uuid.uuid4())},
            headers=headers,
            cookies=cookies,
        )
        assert turn_resp.status_code == 202

        # 4. Receive live streamed event over WebSocket
        live_ev = ws.receive_json()
        assert live_ev["event_type"] == "turn.enqueued"
        assert live_ev["payload"]["message"] == "Live streamed turn"
        assert live_ev["sequence"] > last_seq


def test_websocket_cursor_replay_filters_past_events(authenticated_session, test_mission):
    """Connecting with after_sequence > 0 skips events with sequence <= cursor."""
    headers = authenticated_session["headers"]
    cookies = authenticated_session["cookies"]
    m_id = test_mission["mission_id"]

    # Append another turn so we have multiple events
    client.post(
        f"/api/missions/{m_id}/turns",
        json={"message": "Turn 1", "idempotency_key": str(uuid.uuid4())},
        headers=headers,
        cookies=cookies,
    )

    all_events = client.get(f"/api/missions/{m_id}/events?after_sequence=0", headers=headers, cookies=cookies).json()
    assert len(all_events) >= 2
    cutoff_seq = all_events[0]["sequence"]

    # Mint ticket
    ticket_resp = client.post(
        "/api/auth/websocket-ticket",
        headers={"X-CSRF-Token": authenticated_session["csrf_token"]},
        cookies=cookies,
    )
    ticket = ticket_resp.json()["ticket"]

    with client.websocket_connect(f"/ws/missions/{m_id}") as ws:
        ws.send_json({"ticket": ticket, "after_sequence": cutoff_seq})
        first_received = ws.receive_json()
        assert first_received["sequence"] > cutoff_seq


def test_websocket_disconnect_preserves_mission_state(authenticated_session, test_mission):
    """Client disconnect does not corrupt or cancel the underlying mission in store."""
    cookies = authenticated_session["cookies"]
    m_id = test_mission["mission_id"]

    ticket_resp = client.post(
        "/api/auth/websocket-ticket",
        headers={"X-CSRF-Token": authenticated_session["csrf_token"]},
        cookies=cookies,
    )
    ticket = ticket_resp.json()["ticket"]

    # Connect and disconnect immediately
    with client.websocket_connect(f"/ws/missions/{m_id}") as ws:
        ws.send_json({"ticket": ticket, "after_sequence": 0})
        ws.receive_json()
        # Exiting context closes the WebSocket

    # Verify mission is still accessible and not corrupted
    get_resp = client.get(
        f"/api/missions/{m_id}",
        headers=authenticated_session["headers"],
        cookies=cookies,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == m_id
