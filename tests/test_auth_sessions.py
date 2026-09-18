"""Tests for operator session lifecycle, local dev sessions, and WebSocket ticket consumption."""
import time
from unittest.mock import patch
import pytest
from fastapi import HTTPException

from backend.config import config
from backend.services.session_auth import session_auth_service, SessionAuthService
from backend.models.mission import OperatorContext


def test_create_session_and_validate():
    service = SessionAuthService(session_ttl_seconds=3600)
    session_token, csrf_token = service.create_session(
        operator_id=123456789,
        username="john_doe",
        is_local=False,
    )
    assert isinstance(session_token, str) and len(session_token) > 20
    assert isinstance(csrf_token, str) and len(csrf_token) > 20

    operator = service.validate_session(session_token)
    assert isinstance(operator, OperatorContext)
    assert operator.operator_id == 123456789
    assert operator.username == "john_doe"
    assert operator.is_local_development is False

    # CSRF validation
    assert service.validate_csrf(session_token, csrf_token) is True
    assert service.validate_csrf(session_token, "wrong_csrf_token") is False
    assert service.validate_csrf("invalid_session_token", csrf_token) is False


def test_telegram_session_flow_success(client, signed_init_data):
    init_data = signed_init_data(user_id=123456789, username="telegram_op")
    response = client.post(
        "/api/auth/telegram-session",
        headers={"X-Telegram-Init-Data": init_data}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "session_token" in data
    assert "csrf_token" in data
    assert "operator" in data
    assert data["operator"]["operator_id"] == 123456789
    assert data["operator"]["username"] == "telegram_op"
    assert data["operator"]["is_local_development"] is False

    # Check cookies
    cookies = response.cookies
    assert "hermes_session" in cookies or "session_id" in cookies
    token = cookies.get("hermes_session") or cookies.get("session_id")

    # Validate session via service
    operator = session_auth_service.validate_session(token)
    assert operator is not None
    assert operator.operator_id == 123456789


def test_local_dev_session_flow(client):
    with patch.object(config, "ALLOW_LOCAL_DEVELOPMENT", True):
        response = client.post("/api/auth/session")
        assert response.status_code == 200
        data = response.json()
        assert data["operator"]["operator_id"] == 0
        assert data["operator"]["username"] == "local_admin"
        assert data["operator"]["is_local_development"] is True
        assert "csrf_token" in data


def test_local_dev_session_disabled(client):
    with patch.object(config, "ALLOW_LOCAL_DEVELOPMENT", False):
        response = client.post("/api/auth/session")
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()


def test_websocket_ticket_mint_and_consume(client, authenticated_session):
    # Mint ticket via authenticated endpoint
    response = client.post(
        "/api/auth/websocket-ticket",
        cookies=authenticated_session["cookies"],
        headers={"X-CSRF-Token": authenticated_session["csrf_token"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "ticket" in data
    assert data["expires_in"] == 60
    ticket = data["ticket"]

    # Consume ticket
    operator = session_auth_service.consume_websocket_ticket(ticket)
    assert isinstance(operator, OperatorContext)
    assert operator.operator_id == authenticated_session["operator"].operator_id


def test_websocket_ticket_single_use(authenticated_session):
    ticket = session_auth_service.issue_websocket_ticket(authenticated_session["operator"])

    # First consumption succeeds
    first = session_auth_service.consume_websocket_ticket(ticket)
    assert first.operator_id == authenticated_session["operator"].operator_id

    # Second consumption fails
    with pytest.raises(HTTPException) as exc_info:
        session_auth_service.consume_websocket_ticket(ticket)
    assert exc_info.value.status_code == 401
    assert "already consumed" in exc_info.value.detail.lower()


def test_get_current_session_authenticated(client, authenticated_session):
    response = client.get(
        "/api/auth/session",
        cookies=authenticated_session["cookies"],
    )
    assert response.status_code == 200
    assert response.json()["operator"]["operator_id"] == authenticated_session["operator"].operator_id


def test_get_current_session_unauthenticated(client):
    response = client.get("/api/auth/session")
    assert response.status_code == 401
