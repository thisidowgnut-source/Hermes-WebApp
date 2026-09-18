"""Server session, CSRF, one-time WebSocket ticket, allowlist, and in-memory rate limit services."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import json
import logging
import secrets
import threading
import time
import urllib.parse
from uuid import UUID, uuid4
from typing import Any, Optional

from fastapi import HTTPException, Request, Depends, Header
from backend.models.mission import OperatorContext
from backend.config import config

logger = logging.getLogger(__name__)


def validate_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 86400,
    now: datetime | None = None
) -> dict[str, Any]:
    """
    Parse and verify Telegram WebApp initData HMAC-SHA256 signature with freshness checks.

    1. Extracts hash, compares HMAC-SHA256 in constant time.
    2. Parses user JSON safely.
    3. Checks int(auth_date), rejects if (now - auth_date) > max_age_seconds or auth_date in future.
    """
    if not init_data or not isinstance(init_data, str):
        raise HTTPException(status_code=401, detail="Invalid Telegram initData: payload missing or empty")

    if not bot_token:
        raise HTTPException(status_code=401, detail="Telegram bot token not provided for verification")

    try:
        parsed_pairs = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Telegram initData format: {exc}") from exc

    data_dict = dict(parsed_pairs)

    if "hash" not in data_dict:
        raise HTTPException(status_code=401, detail="Invalid Telegram initData: missing hash parameter")

    received_hash = data_dict.pop("hash")

    # Sort remaining keys alphabetically
    sorted_items = sorted(data_dict.items(), key=lambda item: item[0])
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_items)

    # Calculate HMAC-SHA256 signature
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash.lower(), received_hash.lower()):
        raise HTTPException(status_code=401, detail="Invalid Telegram WebApp signature")

    # Validate auth_date
    if "auth_date" not in data_dict:
        raise HTTPException(status_code=401, detail="Invalid Telegram initData: missing auth_date parameter")

    try:
        auth_date = int(data_dict["auth_date"])
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid Telegram initData: auth_date must be integer") from exc

    # Freshness verification
    if max_age_seconds > 0:
        if now is None:
            current_time = datetime.now(timezone.utc)
        else:
            current_time = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        current_timestamp = int(current_time.timestamp())

        if (current_timestamp - auth_date) > max_age_seconds:
            raise HTTPException(status_code=401, detail="Telegram initData has expired")

        if auth_date > current_timestamp:
            raise HTTPException(status_code=401, detail="Telegram initData auth_date is in the future")

    # Return parsed user data dict
    user_data: dict[str, Any] = {}
    if "user" in data_dict:
        try:
            user_data = json.loads(data_dict["user"])
        except json.JSONDecodeError:
            user_data = {"raw_user": data_dict["user"]}
    else:
        user_data = data_dict.copy()

    user_data.setdefault("auth_date", auth_date)
    return user_data


@dataclass
class SessionRecord:
    session_id: UUID
    token_hash: str
    csrf_token: str
    operator_id: int
    username: Optional[str]
    is_local_development: bool
    created_at: datetime
    expires_at: datetime


@dataclass
class WebSocketTicketRecord:
    ticket_hash: str
    session_id: UUID
    operator_id: int
    username: Optional[str]
    is_local_development: bool
    created_at: datetime
    expires_at: datetime
    consumed_at: Optional[datetime] = None


class SessionAuthService:
    """Manages operator sessions, CSRF validation, and single-use WebSocket tickets."""

    def __init__(self, session_ttl_seconds: int = 86400, ticket_ttl_seconds: int = 60):
        self.session_ttl_seconds = session_ttl_seconds
        self.ticket_ttl_seconds = ticket_ttl_seconds
        self._sessions_by_hash: dict[str, SessionRecord] = {}
        self._sessions_by_id: dict[UUID, SessionRecord] = {}
        self._tickets_by_hash: dict[str, WebSocketTicketRecord] = {}
        self._lock = threading.Lock()

    def create_session(
        self,
        operator_id: int,
        username: str | None,
        is_local: bool = False
    ) -> tuple[str, str]:
        """
        Generates opaque session token (secrets.token_urlsafe(32)) and CSRF token (secrets.token_urlsafe(32)).
        Hashes session token with SHA256 and stores in operator_sessions.
        Returns (session_token, csrf_token).
        """
        session_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        session_id = uuid4()
        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.session_ttl_seconds)

        record = SessionRecord(
            session_id=session_id,
            token_hash=token_hash,
            csrf_token=csrf_token,
            operator_id=operator_id,
            username=username,
            is_local_development=is_local,
            created_at=now,
            expires_at=expires_at,
        )

        with self._lock:
            self._sessions_by_hash[token_hash] = record
            self._sessions_by_id[session_id] = record

        # Optional integration with mission_store if present
        try:
            from backend.services.mission_store import mission_store
            if mission_store and hasattr(mission_store, "save_operator_session"):
                mission_store.save_operator_session(
                    session_id=str(session_id),
                    token_hash=token_hash,
                    csrf_token=csrf_token,
                    operator_id=operator_id,
                    username=username,
                    is_local=is_local,
                    created_at=now.isoformat(),
                    expires_at=expires_at.isoformat(),
                )
        except Exception:
            pass

        return session_token, csrf_token

    def validate_session(self, session_token: str) -> OperatorContext | None:
        """
        Validates session token. Hashes token and checks storage.
        Returns OperatorContext if valid and not expired, else None.
        """
        if not session_token or not isinstance(session_token, str):
            return None

        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)

        with self._lock:
            record = self._sessions_by_hash.get(token_hash)
            if not record:
                try:
                    sess_uuid = UUID(session_token)
                    record = self._sessions_by_id.get(sess_uuid)
                except (ValueError, TypeError):
                    record = None

            if not record:
                return None

            if now > record.expires_at:
                return None

            return OperatorContext(
                operator_id=record.operator_id,
                username=record.username,
                session_id=record.session_id,
                is_local_development=record.is_local_development,
            )

    def get_session_record(self, session_token: str) -> SessionRecord | None:
        """Helper to get full session record including CSRF token."""
        if not session_token:
            return None
        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)

        with self._lock:
            record = self._sessions_by_hash.get(token_hash)
            if not record:
                try:
                    sess_uuid = UUID(session_token)
                    record = self._sessions_by_id.get(sess_uuid)
                except (ValueError, TypeError):
                    record = None

            if record and now <= record.expires_at:
                return record
            return None

    def validate_csrf(self, session_token: str, csrf_token: str) -> bool:
        """Validates CSRF token for a given session."""
        if not session_token or not csrf_token:
            return False
        record = self.get_session_record(session_token)
        if not record:
            return False
        return hmac.compare_digest(record.csrf_token, csrf_token)

    def issue_websocket_ticket(self, operator: OperatorContext) -> str:
        """
        Generates single-use ticket string, hashes and stores with 60-second TTL.
        """
        ticket = f"wst_{secrets.token_urlsafe(32)}"
        ticket_hash = hashlib.sha256(ticket.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.ticket_ttl_seconds)

        record = WebSocketTicketRecord(
            ticket_hash=ticket_hash,
            session_id=operator.session_id,
            operator_id=operator.operator_id,
            username=operator.username,
            is_local_development=operator.is_local_development,
            created_at=now,
            expires_at=expires_at,
            consumed_at=None,
        )

        with self._lock:
            self._tickets_by_hash[ticket_hash] = record

        # Optional integration with mission_store
        try:
            from backend.services.mission_store import mission_store
            if mission_store and hasattr(mission_store, "save_websocket_ticket"):
                mission_store.save_websocket_ticket(
                    ticket_hash=ticket_hash,
                    session_id=str(operator.session_id),
                    operator_id=operator.operator_id,
                    username=operator.username,
                    is_local=operator.is_local_development,
                    created_at=now.isoformat(),
                    expires_at=expires_at.isoformat(),
                )
        except Exception:
            pass

        return ticket

    def consume_websocket_ticket(self, ticket: str) -> OperatorContext:
        """
        Validates ticket hash, checks expiry, marks ticket consumed (single use).
        If invalid or already consumed, raises HTTPException(401).
        """
        if not ticket or not isinstance(ticket, str):
            raise HTTPException(status_code=401, detail="Invalid ticket: missing or empty")

        ticket_hash = hashlib.sha256(ticket.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)

        with self._lock:
            record = self._tickets_by_hash.get(ticket_hash)
            if not record:
                raise HTTPException(status_code=401, detail="Invalid ticket: ticket not found")

            if record.consumed_at is not None:
                raise HTTPException(status_code=401, detail="Ticket already consumed")

            if now > record.expires_at:
                raise HTTPException(status_code=401, detail="Ticket expired")

            # Single-use consumption
            record.consumed_at = now

            return OperatorContext(
                operator_id=record.operator_id,
                username=record.username,
                session_id=record.session_id,
                is_local_development=record.is_local_development,
            )

    def clear(self) -> None:
        """Clear all in-memory sessions and tickets (for testing)."""
        with self._lock:
            self._sessions_by_hash.clear()
            self._sessions_by_id.clear()
            self._tickets_by_hash.clear()


class RateLimiter:
    """In-memory sliding window rate limiter protected by threading.Lock."""

    def __init__(self):
        self._windows: dict[tuple[str, int], list[float]] = {}
        self._lock = threading.Lock()

    def check(
        self,
        scope: str,
        operator_id: int,
        max_requests: int = 60,
        window_seconds: int = 60
    ) -> None:
        """
        In-memory sliding window using timestamps and threading.Lock.
        Raises HTTPException(status_code=429, detail="Rate limit exceeded") if limit reached.
        """
        now = time.monotonic()
        key = (scope, operator_id)
        threshold = now - window_seconds

        with self._lock:
            timestamps = self._windows.get(key, [])
            timestamps = [t for t in timestamps if t > threshold]

            if len(timestamps) >= max_requests:
                self._windows[key] = timestamps
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            timestamps.append(now)
            self._windows[key] = timestamps

    def reset(self, scope: Optional[str] = None, operator_id: Optional[int] = None) -> None:
        """Reset rate limiter windows (for testing)."""
        with self._lock:
            if scope is None and operator_id is None:
                self._windows.clear()
            elif scope is not None and operator_id is not None:
                self._windows.pop((scope, operator_id), None)
            else:
                to_delete = [
                    k for k in self._windows
                    if (scope is None or k[0] == scope) and (operator_id is None or k[1] == operator_id)
                ]
                for k in to_delete:
                    self._windows.pop(k, None)


# Module singletons
session_auth_service = SessionAuthService()
rate_limiter = RateLimiter()


def get_session_token_from_request(request: Request) -> str | None:
    """Extract session token from cookies or request headers."""
    # 1. Cookies
    for name in ("hermes_session", "session_id", "session"):
        val = request.cookies.get(name)
        if val:
            return val

    # 2. X-Session-Token header
    val = request.headers.get("X-Session-Token")
    if val:
        return val

    # 3. Authorization: Bearer <token>
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:].strip()

    return None


def get_session_auth_service() -> Any:
    return session_auth_service


def require_operator(
    request: Request,
    service: Any = Depends(get_session_auth_service)
) -> OperatorContext:
    """
    FastAPI dependency enforcing valid session authentication.
    Returns OperatorContext or raises 401.
    """
    token = get_session_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required: missing session token")

    operator = service.validate_session(token)
    if not operator:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return operator


def require_csrf(
    request: Request,
    operator: OperatorContext = Depends(require_operator),
    service: Any = Depends(get_session_auth_service)
) -> None:
    """
    FastAPI dependency verifying X-CSRF-Token header against operator session.
    Raises 403 on CSRF failure.
    """
    token = get_session_token_from_request(request)
    csrf_header = request.headers.get("X-CSRF-Token")

    if not csrf_header:
        raise HTTPException(status_code=403, detail="CSRF token missing")

    if not token or not service.validate_csrf(token, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
