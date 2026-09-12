import hmac
import hashlib
import urllib.parse
import json
import pytest
from unittest.mock import patch
from fastapi import HTTPException

from backend.auth import verify_telegram_init_data, telegram_auth_guard
from backend.config import config

TEST_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
TEST_USER_DATA = {
    "id": 987654321,
    "first_name": "Test",
    "last_name": "User",
    "username": "testuser",
    "language_code": "en"
}

def generate_init_data(params: dict, bot_token: str) -> str:
    """Helper function to create a signed Telegram initData query string."""
    # Convert dict values to strings
    raw_params = {}
    for k, v in params.items():
        if isinstance(v, (dict, list)):
            raw_params[k] = json.dumps(v, separators=(',', ':'))
        else:
            raw_params[k] = str(v)

    # Sort keys alphabetically and build data check string
    sorted_items = sorted(raw_params.items(), key=lambda item: item[0])
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_items)

    # Calculate HMAC-SHA256
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    hash_val = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    # Build URL query string
    raw_params["hash"] = hash_val
    return urllib.parse.urlencode(raw_params)

def test_verify_telegram_init_data_valid_signature():
    params = {
        "query_id": "AAHXXXXX",
        "user": TEST_USER_DATA,
        "auth_date": "1700000000"
    }
    init_data = generate_init_data(params, TEST_BOT_TOKEN)
    
    result = verify_telegram_init_data(init_data, TEST_BOT_TOKEN)
    assert result["id"] == TEST_USER_DATA["id"]
    assert result["username"] == TEST_USER_DATA["username"]
    assert result["first_name"] == TEST_USER_DATA["first_name"]

def test_verify_telegram_init_data_invalid_bot_token():
    params = {
        "query_id": "AAHXXXXX",
        "user": TEST_USER_DATA,
        "auth_date": "1700000000"
    }
    init_data = generate_init_data(params, TEST_BOT_TOKEN)
    
    with pytest.raises(HTTPException) as exc_info:
        verify_telegram_init_data(init_data, "999999999:WRONG_TOKEN")
    assert exc_info.value.status_code == 401
    assert "Invalid Telegram WebApp signature" in exc_info.value.detail

def test_verify_telegram_init_data_tampered_payload():
    params = {
        "query_id": "AAHXXXXX",
        "user": TEST_USER_DATA,
        "auth_date": "1700000000"
    }
    init_data = generate_init_data(params, TEST_BOT_TOKEN)
    
    # Tamper with the query string: change auth_date from 1700000000 to 1700000001
    tampered_init_data = init_data.replace("auth_date=1700000000", "auth_date=1700000001")
    
    with pytest.raises(HTTPException) as exc_info:
        verify_telegram_init_data(tampered_init_data, TEST_BOT_TOKEN)
    assert exc_info.value.status_code == 401
    assert "Invalid Telegram WebApp signature" in exc_info.value.detail

def test_verify_telegram_init_data_missing_hash():
    init_data = "query_id=AAHXXXXX&auth_date=1700000000"
    with pytest.raises(HTTPException) as exc_info:
        verify_telegram_init_data(init_data, TEST_BOT_TOKEN)
    assert exc_info.value.status_code == 401
    assert "missing hash parameter" in exc_info.value.detail

def test_verify_telegram_init_data_empty_payload():
    with pytest.raises(HTTPException) as exc_info:
        verify_telegram_init_data("", TEST_BOT_TOKEN)
    assert exc_info.value.status_code == 401
    assert "missing or empty" in exc_info.value.detail

def test_verify_telegram_init_data_no_user_param():
    params = {
        "query_id": "AAHXXXXX",
        "auth_date": "1700000000"
    }
    init_data = generate_init_data(params, TEST_BOT_TOKEN)
    result = verify_telegram_init_data(init_data, TEST_BOT_TOKEN)
    assert result["query_id"] == "AAHXXXXX"
    assert result["auth_date"] == "1700000000"

def test_telegram_auth_guard_with_valid_token():
    params = {
        "query_id": "AAHXXXXX",
        "user": TEST_USER_DATA,
        "auth_date": "1700000000"
    }
    init_data = generate_init_data(params, TEST_BOT_TOKEN)
    
    with patch.object(config, "TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN):
        result = telegram_auth_guard(init_data=init_data)
        assert result["id"] == TEST_USER_DATA["id"]

def test_telegram_auth_guard_missing_header_when_token_configured():
    with patch.object(config, "TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN):
        with pytest.raises(HTTPException) as exc_info:
            telegram_auth_guard(init_data=None)
        assert exc_info.value.status_code == 401
        assert "X-Telegram-Init-Data header missing" in exc_info.value.detail

def test_telegram_auth_guard_dev_mode_bypass(caplog):
    with patch.object(config, "TELEGRAM_BOT_TOKEN", ""):
        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": ""}):
            result = telegram_auth_guard(init_data=None)
            assert result.get("dev_mode") is True
            assert result.get("id") == 0
            # Verify warning was logged
            assert any("TELEGRAM_BOT_TOKEN is not set" in record.message for record in caplog.records)
