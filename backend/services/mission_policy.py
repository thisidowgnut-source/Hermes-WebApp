"""Mission state machine transitions, authorization rules, and payload redaction."""
from __future__ import annotations

from typing import Any
from backend.models.mission import MissionState
from backend.services.hermes_adapter import DelegationLoopError, validate_handoff


class InvalidMissionTransition(Exception):
    """Raised when an illegal mission state transition is attempted."""
    pass


# Valid state transitions map as defined by the mission architecture
VALID_TRANSITIONS: dict[MissionState, set[MissionState]] = {
    MissionState.DRAFT: {
        MissionState.QUEUED,
        MissionState.CANCELLED,
    },
    MissionState.QUEUED: {
        MissionState.STARTING,
        MissionState.CANCELLED,
    },
    MissionState.STARTING: {
        MissionState.RUNNING,
        MissionState.FAILED,
        MissionState.CANCELLED,
        MissionState.INTERRUPTED,
        MissionState.UNKNOWN,
    },
    MissionState.RUNNING: {
        MissionState.WAITING_HUMAN,
        MissionState.WAITING_APPROVAL,
        MissionState.SUCCEEDED,
        MissionState.NEEDS_VERIFICATION,
        MissionState.INTERRUPTED,
        MissionState.UNKNOWN,
        MissionState.CANCELLED,
        MissionState.FAILED,
        MissionState.TIMED_OUT,
    },
    MissionState.WAITING_HUMAN: {
        MissionState.RUNNING,
        MissionState.CANCELLED,
        MissionState.FAILED,
    },
    MissionState.WAITING_APPROVAL: {
        MissionState.RUNNING,
        MissionState.CANCELLED,
        MissionState.FAILED,
    },
    MissionState.SUCCEEDED: {
        MissionState.NEEDS_VERIFICATION,
        MissionState.VERIFIED,
    },
    MissionState.NEEDS_VERIFICATION: {
        MissionState.VERIFIED,
        MissionState.FAILED_VERIFICATION,
        MissionState.INTERRUPTED,
    },
    MissionState.VERIFIED: set(),
    MissionState.FAILED_VERIFICATION: set(),
    MissionState.INTERRUPTED: {
        MissionState.QUEUED,
        MissionState.CANCELLED,
        MissionState.FAILED,
    },
    MissionState.UNKNOWN: {
        MissionState.NEEDS_VERIFICATION,
        MissionState.CANCELLED,
        MissionState.FAILED,
    },
    MissionState.CANCELLED: set(),
    MissionState.FAILED: set(),
    MissionState.TIMED_OUT: set(),
}


def is_valid_transition(from_state: MissionState | str, to_state: MissionState | str) -> bool:
    """Check if a transition between two states is allowed."""
    try:
        f_state = MissionState(from_state) if isinstance(from_state, str) else from_state
        t_state = MissionState(to_state) if isinstance(to_state, str) else to_state
    except (ValueError, KeyError):
        return False
    return t_state in VALID_TRANSITIONS.get(f_state, set())


def assert_transition(from_state: MissionState | str, to_state: MissionState | str) -> None:
    """Assert that a transition from one state to another is valid.

    Raises:
        InvalidMissionTransition: If the transition is not in the valid transition map.
    """
    if isinstance(from_state, str):
        from_state = MissionState(from_state)
    if isinstance(to_state, str):
        to_state = MissionState(to_state)

    allowed = VALID_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise InvalidMissionTransition(
            f"Invalid mission state transition from '{from_state.value}' to '{to_state.value}'"
        )


SENSITIVE_KEYS = {"authorization", "cookie", "token", "password", "secret"}


def _is_sensitive_key(k: Any) -> bool:
    if not isinstance(k, str):
        return False
    k_lower = k.lower().strip()
    if k_lower in SENSITIVE_KEYS:
        return True
    if any(s in k_lower for s in ("authorization", "cookie", "password", "secret")):
        return True
    # For token, avoid matching tokens plural like input_tokens, total_tokens
    if k_lower.endswith(("_token", "-token")) and not k_lower.endswith(("_tokens", "-tokens")):
        return True
    return False


def redact_payload(value: Any) -> Any:
    """Recursively redact sensitive keys: 'authorization', 'cookie', 'token', 'password', 'secret',
    replacing strings with '[REDACTED]'."""
    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            if _is_sensitive_key(k):
                if isinstance(v, str):
                    result[k] = "[REDACTED]"
                elif isinstance(v, (dict, list, tuple, set)):
                    result[k] = redact_payload(v)
                else:
                    result[k] = "[REDACTED]" if isinstance(v, (str, bytes)) else v
            else:
                result[k] = redact_payload(v)
        return result
    elif isinstance(value, list):
        return [redact_payload(item) for item in value]
    elif isinstance(value, tuple):
        return tuple(redact_payload(item) for item in value)
    elif isinstance(value, set):
        return {redact_payload(item) for item in value}
    return value
