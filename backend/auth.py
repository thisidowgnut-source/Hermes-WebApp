import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import Header, HTTPException, Request
from backend.config import config
from backend.services.session_auth import validate_telegram_init_data

logger = logging.getLogger(__name__)


def verify_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: Optional[int] = None,
    now: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Parse and verify Telegram WebApp initData HMAC-SHA256 signature.
    Delegates to validate_telegram_init_data.
    When max_age_seconds is provided, enforces freshness check.
    """
    effective_max_age = max_age_seconds if max_age_seconds is not None else 0
    return validate_telegram_init_data(
        init_data=init_data,
        bot_token=bot_token,
        max_age_seconds=effective_max_age,
        now=now,
    )


def telegram_auth_guard(
    request: Request = None,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces Telegram WebApp authentication.
    - If TELEGRAM_BOT_TOKEN is not set or empty, bypass in dev mode with a warning log.
    - If accessed from local loopback (127.0.0.1, localhost, ::1) or dev test client, allow access.
    - If init_data is provided, verify Telegram signature.
    """
    bot_token = config.TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")

    if not bot_token:
        if config.HERMES_ENV == "production":
            raise HTTPException(status_code=401, detail="Authentication required: Telegram bot token not configured")
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Bypassing Telegram authentication guard in dev mode.")
        if init_data:
            try:
                import urllib.parse, json
                parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
                if "user" in parsed:
                    return json.loads(parsed["user"])
            except Exception:
                pass
        return {"id": 0, "first_name": "DevUser", "username": "dev_user", "dev_mode": True}

    # Check if request is from local loopback
    client_host = getattr(request, "client", None)
    client_ip = getattr(client_host, "host", "") if client_host else ""
    if request is not None and client_ip in ("127.0.0.1", "::1", "localhost", "testclient"):
        if not init_data:
            if config.HERMES_ENV == "production":
                raise HTTPException(status_code=401, detail="Authentication required: loopback bypass disabled in production")
            return {"id": 0, "first_name": "LocalOperator", "username": "local_admin", "dev_mode": True}

    if not init_data:
        raise HTTPException(status_code=401, detail="Authentication required: X-Telegram-Init-Data header missing")

    return verify_telegram_init_data(init_data, bot_token)
