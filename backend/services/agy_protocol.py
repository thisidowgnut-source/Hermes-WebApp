"""AGY NDJSON stream parser and conversion to normalized mission events."""
from __future__ import annotations
from datetime import datetime
import json
import logging
from typing import Any

from backend.models.mission import NormalizedAgyEvent, UsageRecord

logger = logging.getLogger(__name__)


class AgyProtocolError(Exception):
    """Raised when an AGY stream line fails structural or validation checks."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def _parse_usage(raw_usage: Any) -> UsageRecord | None:
    if raw_usage is None:
        return None
    if not isinstance(raw_usage, dict):
        raise AgyProtocolError("invalid_usage", "Usage payload must be a dictionary")
    try:
        return UsageRecord(
            input_tokens=int(raw_usage.get("input_tokens", 0) or 0),
            output_tokens=int(raw_usage.get("output_tokens", 0) or 0),
            thinking_tokens=int(raw_usage.get("thinking_tokens", 0) or 0),
            cache_read_tokens=int(raw_usage.get("cache_read_tokens", 0) or 0),
            total_tokens=int(raw_usage.get("total_tokens", 0) or 0),
        )
    except (TypeError, ValueError) as exc:
        raise AgyProtocolError("invalid_usage", f"Usage numbers invalid: {exc}") from exc


def _parse_init(raw_init: Any, conv_id: str | None, now: datetime) -> NormalizedAgyEvent:
    if not isinstance(raw_init, dict):
        raise AgyProtocolError("unsupported_shape", "Event 'init' missing 'init' dictionary")
    cid = conv_id or raw_init.get("conversation_id")
    return NormalizedAgyEvent(
        event_type="agy.init",
        provider_conversation_id=str(cid) if cid else None,
        state="INITIALIZED",
        created_at=now,
    )


def _parse_step(raw_step: Any, now: datetime) -> NormalizedAgyEvent:
    if not isinstance(raw_step, dict):
        raise AgyProtocolError("unsupported_shape", "Event 'step_update' missing dictionary")
    cid = raw_step.get("conversation_id")
    return NormalizedAgyEvent(
        event_type="agy.step",
        provider_conversation_id=str(cid) if cid else None,
        state=str(raw_step.get("state")) if raw_step.get("state") is not None else None,
        text_delta=str(raw_step.get("text_delta")) if raw_step.get("text_delta") is not None else None,
        tool_name=str(raw_step.get("tool_name")) if raw_step.get("tool_name") is not None else None,
        created_at=now,
    )


def _parse_result(raw_result: Any, now: datetime) -> NormalizedAgyEvent:
    if not isinstance(raw_result, dict):
        raise AgyProtocolError("missing_result", "Event 'result' missing valid 'result' dictionary")
    cid = raw_result.get("conversation_id")
    status = raw_result.get("status")
    response_text = raw_result.get("response")
    raw_usage = raw_result.get("usage")
    usage = _parse_usage(raw_usage)

    return NormalizedAgyEvent(
        event_type="agy.result",
        provider_conversation_id=str(cid) if cid else None,
        result_status=str(status) if status is not None else None,
        text_delta=str(response_text) if response_text is not None else None,
        usage=usage,
        created_at=now,
    )


def parse_agy_stream_line(line: str, now: datetime) -> NormalizedAgyEvent | None:
    """Parse a single line of AGY stream-json NDJSON output.

    Returns:
        NormalizedAgyEvent on known valid events.
        None for benign/unknown future events (logged diagnostically).

    Raises:
        AgyProtocolError on bad JSON or invalid event shapes.
    """
    stripped = line.strip()
    if not stripped:
        return None

    try:
        payload = json.loads(stripped)
    except Exception as exc:
        raise AgyProtocolError("malformed_json", f"Failed to parse line as JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise AgyProtocolError("unsupported_shape", "Top-level JSON payload must be an object")

    event_name = payload.get("event")
    if not event_name:
        raise AgyProtocolError("unsupported_shape", "Event object missing 'event' type field")

    if event_name == "init":
        return _parse_init(payload.get("init"), payload.get("conversation_id"), now)
    elif event_name == "step_update":
        return _parse_step(payload.get("step_update"), now)
    elif event_name == "result":
        return _parse_result(payload.get("result"), now)

    logger.debug("Received unknown AGY event: %s", event_name)
    return None
