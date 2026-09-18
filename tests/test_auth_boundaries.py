"""Security boundary tests: Telegram freshness checks, allowlists, CSRF enforcement, ticket boundaries, and rate limiting."""
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import pytest
from fastapi import HTTPException

from backend.config import config
from backend.services.session_auth import (
    session_auth_service,
    rate_limiter,
    validate_telegram_init_data,
    RateLimiter,
)


def test_expired_telegram_auth_date_is_rejected(client, signed_init_data):
    # Expired 90,000 seconds ago (max_age is 86,400)
    expired_ts = int(time.time()) - 90000
    expired_data = signed_init_data(auth_date=expired_ts)

    response = client.post(
        "/api/auth/telegram-session",
        headers={"X-Telegram-Init-Data": expired_data}
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_future_telegram_auth_date_is_rejected(client, signed_init_data):
    # 1 hour into the future
    future_ts = int(time.time()) + 3600
    future_data = signed_init_data(auth_date=future_ts)

    response = client.post(
        "/api/auth/telegram-session",
        headers={"X-Telegram-Init-Data": future_data}
    )
    assert response.status_code == 401
    assert "future" in response.json()["detail"].lower()


def test_missing_or_empty_telegram_header_is_rejected(client):
    response = client.post("/api/auth/telegram-session")
    assert response.status_code == 401


def test_tampered_telegram_hash_is_rejected(client, signed_init_data):
    tampered_data = signed_init_data(tamper=True)
    response = client.post(
        "/api/auth/telegram-session",
        headers={"X-Telegram-Init-Data": tampered_data}
    )
    assert response.status_code == 401
    assert "signature" in response.json()["detail"].lower()


def test_unallowlisted_operator_is_rejected(client, signed_init_data):
    # 999999 is not in OPERATOR_ALLOWLIST
    unauthorized_data = signed_init_data(user_id=999999)
    response = client.post(
        "/api/auth/telegram-session",
        headers={"X-Telegram-Init-Data": unauthorized_data}
    )
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


def test_ticket_issue_requires_session_and_csrf(client, authenticated_session):
    # Missing CSRF header entirely -> 403
    resp_no_csrf = client.post(
        "/api/auth/websocket-ticket",
        cookies=authenticated_session["cookies"]
    )
    assert resp_no_csrf.status_code == 403
    assert "csrf" in resp_no_csrf.json()["detail"].lower()

    # Invalid CSRF header -> 403
    resp_bad_csrf = client.post(
        "/api/auth/websocket-ticket",
        cookies=authenticated_session["cookies"],
        headers={"X-CSRF-Token": "bad_token_value"}
    )
    assert resp_bad_csrf.status_code == 403
    assert "csrf" in resp_bad_csrf.json()["detail"].lower()

    # Missing session cookie -> 401
    resp_no_session = client.post(
        "/api/auth/websocket-ticket",
        headers={"X-CSRF-Token": authenticated_session["csrf_token"]}
    )
    assert resp_no_session.status_code == 401


def test_state_changing_endpoint_requires_csrf(client, authenticated_session):
    # Test verify-csrf route with missing CSRF token
    resp1 = client.post(
        "/api/auth/verify-csrf",
        cookies=authenticated_session["cookies"]
    )
    assert resp1.status_code == 403

    # Test verify-csrf route with invalid CSRF token
    resp2 = client.post(
        "/api/auth/verify-csrf",
        cookies=authenticated_session["cookies"],
        headers={"X-CSRF-Token": "forged_csrf"}
    )
    assert resp2.status_code == 403

    # Test verify-csrf route with valid CSRF token
    resp3 = client.post(
        "/api/auth/verify-csrf",
        cookies=authenticated_session["cookies"],
        headers={"X-CSRF-Token": authenticated_session["csrf_token"]}
    )
    assert resp3.status_code == 200
    assert resp3.json()["ok"] is True


def test_expired_websocket_ticket_is_rejected(authenticated_session):
    ticket = session_auth_service.issue_websocket_ticket(authenticated_session["operator"])

    # Simulate ticket expiry by backdating its expires_at
    import hashlib
    ticket_hash = hashlib.sha256(ticket.encode("utf-8")).hexdigest()
    record = session_auth_service._tickets_by_hash[ticket_hash]
    record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)

    with pytest.raises(HTTPException) as exc_info:
        session_auth_service.consume_websocket_ticket(ticket)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_rate_limiter_triggers_429():
    limiter = RateLimiter()
    # Allow 3 requests per 60s
    for _ in range(3):
        limiter.check("test_scope", operator_id=42, max_requests=3, window_seconds=60)

    # 4th request must raise 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("test_scope", operator_id=42, max_requests=3, window_seconds=60)
    assert exc_info.value.status_code == 429
    assert "rate limit exceeded" in exc_info.value.detail.lower()

    # Different operator_id should not be blocked
    limiter.check("test_scope", operator_id=43, max_requests=3, window_seconds=60)


def test_rate_limiter_resets_after_window():
    limiter = RateLimiter()
    limiter.check("test_scope", operator_id=99, max_requests=1, window_seconds=1)

    # Immediate second call fails
    with pytest.raises(HTTPException):
        limiter.check("test_scope", operator_id=99, max_requests=1, window_seconds=1)

    # Wait for sliding window to expire
    time.sleep(1.1)
    # Next call succeeds
    limiter.check("test_scope", operator_id=99, max_requests=1, window_seconds=1)
