"""Authentication and session management routes."""
from __future__ import annotations
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, Header, Depends

from backend.config import config
from backend.models.mission import OperatorContext
from backend.services.session_auth import (
    session_auth_service,
    rate_limiter,
    validate_telegram_init_data,
    get_session_token_from_request,
    require_operator,
    require_csrf,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/telegram-session")
def create_telegram_session(
    response: Response,
    request: Request,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
):
    """
    Establish an operator session using Telegram WebApp initData.
    Validates HMAC signature and auth_date freshness.
    Checks operator_id against OPERATOR_ALLOWLIST.
    Sets HttpOnly session cookie and returns session metadata + CSRF token.
    """
    if not init_data:
        raise HTTPException(status_code=401, detail="X-Telegram-Init-Data header missing")

    bot_token = config.TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise HTTPException(status_code=401, detail="Telegram bot token not configured")

    user_data = validate_telegram_init_data(
        init_data=init_data,
        bot_token=bot_token,
        max_age_seconds=config.TELEGRAM_MAX_AGE_SECONDS,
    )

    raw_id = user_data.get("id")
    if raw_id is None:
        raise HTTPException(status_code=401, detail="User id missing from Telegram initData")

    try:
        operator_id = int(raw_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid user id in Telegram initData") from exc

    if operator_id not in config.OPERATOR_ALLOWLIST:
        raise HTTPException(status_code=403, detail=f"Operator {operator_id} not authorized")

    # Rate limiting
    rate_limiter.check(scope="session_create", operator_id=operator_id)

    username = user_data.get("username")
    session_token, csrf_token = session_auth_service.create_session(
        operator_id=operator_id,
        username=username,
        is_local=False,
    )

    operator = session_auth_service.validate_session(session_token)
    if not operator:
        raise HTTPException(status_code=500, detail="Failed to initialize session")

    # Set session cookie
    is_production = config.HERMES_ENV == "production"
    response.set_cookie(
        key="hermes_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=86400,
        secure=is_production,
    )
    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=86400,
        secure=is_production,
    )

    return {
        "session_id": str(operator.session_id),
        "session_token": session_token,
        "csrf_token": csrf_token,
        "operator": operator.model_dump(),
    }


@router.post("/session")
def create_local_dev_session(
    response: Response,
    request: Request,
):
    """
    Establish a local development operator session.
    Only permitted when ALLOW_LOCAL_DEVELOPMENT is True and request originates from loopback.
    """
    if not config.ALLOW_LOCAL_DEVELOPMENT:
        raise HTTPException(status_code=403, detail="Local development session creation disabled")

    client_host = getattr(request.client, "host", "") if request.client else ""
    if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
        raise HTTPException(status_code=403, detail="Local development session only allowed from loopback")

    operator_id = 0
    rate_limiter.check(scope="local_session_create", operator_id=operator_id)

    session_token, csrf_token = session_auth_service.create_session(
        operator_id=operator_id,
        username="local_admin",
        is_local=True,
    )

    operator = session_auth_service.validate_session(session_token)
    if not operator:
        raise HTTPException(status_code=500, detail="Failed to initialize local session")

    is_production = config.HERMES_ENV == "production"
    response.set_cookie(
        key="hermes_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=86400,
        secure=is_production,
    )
    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=86400,
        secure=is_production,
    )

    return {
        "session_id": str(operator.session_id),
        "session_token": session_token,
        "csrf_token": csrf_token,
        "operator": operator.model_dump(),
    }


@router.post("/websocket-ticket")
def create_websocket_ticket(
    request: Request,
    csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
):
    """
    Mint a short-lived, single-use ticket for WebSocket authentication.
    Requires a valid operator session and valid X-CSRF-Token header.
    """
    token = get_session_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required: missing session token")

    operator = session_auth_service.validate_session(token)
    if not operator:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    if not csrf_token:
        raise HTTPException(status_code=403, detail="CSRF token missing")

    if not session_auth_service.validate_csrf(token, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    rate_limiter.check(scope="ticket_issue", operator_id=operator.operator_id)

    ticket = session_auth_service.issue_websocket_ticket(operator)
    return {
        "ticket": ticket,
        "expires_in": 60,
    }


@router.get("/session")
def get_current_session(operator: OperatorContext = Depends(require_operator)):
    """Inspect the active operator context."""
    return {"operator": operator.model_dump()}


@router.post("/verify-csrf")
def verify_csrf_check(
    request: Request,
    operator: OperatorContext = Depends(require_operator),
    _: None = Depends(require_csrf),
):
    """State-changing probe endpoint to test CSRF validation."""
    return {"ok": True, "operator_id": operator.operator_id}
