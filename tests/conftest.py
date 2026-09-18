"""Global test fixtures for Hermes-WebApp test suite."""
import json
import time
import hmac
import hashlib
import urllib.parse
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.auth import telegram_auth_guard
from backend.config import config
from backend.services.session_auth import session_auth_service, rate_limiter


@pytest.fixture(autouse=True)
def bypass_auth_for_tests():
    """Override the global Telegram auth guard so test clients can call endpoints directly.

    The production app enforces X-Telegram-Init-Data auth (P0 hardening, 2026-09-12).
    Tests target endpoint logic, not the HMAC handshake (covered in test_auth.py),
    so we swap the guard for a stub identity for the duration of each test.
    """
    app.dependency_overrides[telegram_auth_guard] = lambda: {
        "id": 0,
        "first_name": "TestUser",
        "username": "test_user",
    }
    yield
    app.dependency_overrides.pop(telegram_auth_guard, None)


@pytest.fixture
def client():
    """TestClient instance bound to the FastAPI application."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_auth_state_each_test():
    """Ensure in-memory sessions and rate limiter windows are clean for each test."""
    session_auth_service.clear()
    rate_limiter.reset()
    yield
    session_auth_service.clear()
    rate_limiter.reset()


@pytest.fixture
def signed_init_data():
    """Factory helper to build cryptographically valid Telegram WebApp initData query strings."""
    def _create(
        user_id: int = 123456789,
        username: str = "test_operator",
        auth_date: int | None = None,
        bot_token: str | None = None,
        tamper: bool = False,
    ) -> str:
        token = bot_token or config.TELEGRAM_BOT_TOKEN or "test_bot_token:ABCDEF"
        if auth_date is None:
            auth_date = int(time.time())

        user_dict = {
            "id": user_id,
            "first_name": "Test",
            "last_name": "Operator",
            "username": username,
        }
        params = {
            "query_id": "AAHXXXXX",
            "user": json.dumps(user_dict, separators=(",", ":")),
            "auth_date": str(auth_date),
        }
        sorted_items = sorted(params.items(), key=lambda item: item[0])
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_items)

        secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if tamper:
            calculated_hash = "0" * 64

        params["hash"] = calculated_hash
        return urllib.parse.urlencode(params)

    return _create


@pytest.fixture
def authenticated_session():
    """Establishes an authenticated operator session and returns tokens and auth headers."""
    session_token, csrf_token = session_auth_service.create_session(
        operator_id=123456789,
        username="test_operator",
        is_local=False,
    )
    operator = session_auth_service.validate_session(session_token)
    return {
        "session_token": session_token,
        "csrf_token": csrf_token,
        "operator": operator,
        "cookies": {
            "hermes_session": session_token,
            "session_id": session_token,
        },
        "headers": {
            "X-CSRF-Token": csrf_token,
            "X-Session-Token": session_token,
        },
    }
