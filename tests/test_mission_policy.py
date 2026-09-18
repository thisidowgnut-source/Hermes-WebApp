"""Unit tests for mission state transitions and payload redaction policies."""
import json
import pytest

from backend.models.mission import MissionState
from backend.services.mission_policy import (
    InvalidMissionTransition,
    assert_transition,
    is_valid_transition,
    redact_payload,
)


def test_valid_transitions():
    """Verify that expected legal state transitions succeed without error."""
    # Happy path: draft -> queued -> starting -> running -> succeeded -> verified
    assert_transition(MissionState.DRAFT, MissionState.QUEUED)
    assert_transition(MissionState.QUEUED, MissionState.STARTING)
    assert_transition(MissionState.STARTING, MissionState.RUNNING)
    assert_transition(MissionState.RUNNING, MissionState.SUCCEEDED)
    assert_transition(MissionState.SUCCEEDED, MissionState.VERIFIED)

    # Verification flow: succeeded -> needs_verification -> verified
    assert_transition(MissionState.SUCCEEDED, MissionState.NEEDS_VERIFICATION)
    assert_transition(MissionState.NEEDS_VERIFICATION, MissionState.VERIFIED)
    assert_transition(MissionState.NEEDS_VERIFICATION, MissionState.FAILED_VERIFICATION)

    # Human in the loop / approval flows
    assert_transition(MissionState.RUNNING, MissionState.WAITING_HUMAN)
    assert_transition(MissionState.WAITING_HUMAN, MissionState.RUNNING)
    assert_transition(MissionState.RUNNING, MissionState.WAITING_APPROVAL)
    assert_transition(MissionState.WAITING_APPROVAL, MissionState.RUNNING)

    # Interruption and recovery
    assert_transition(MissionState.RUNNING, MissionState.INTERRUPTED)
    assert_transition(MissionState.INTERRUPTED, MissionState.QUEUED)

    # Unknown to recovery/failure
    assert_transition(MissionState.RUNNING, MissionState.UNKNOWN)
    assert_transition(MissionState.UNKNOWN, MissionState.NEEDS_VERIFICATION)
    assert_transition(MissionState.UNKNOWN, MissionState.FAILED)
    assert_transition(MissionState.UNKNOWN, MissionState.CANCELLED)

    # Cancellation / failures / timeouts
    assert_transition(MissionState.DRAFT, MissionState.CANCELLED)
    assert_transition(MissionState.QUEUED, MissionState.CANCELLED)
    assert_transition(MissionState.STARTING, MissionState.FAILED)
    assert_transition(MissionState.RUNNING, MissionState.TIMED_OUT)
    assert_transition(MissionState.RUNNING, MissionState.FAILED)
    assert_transition(MissionState.RUNNING, MissionState.CANCELLED)

    # Helper function check
    assert is_valid_transition(MissionState.DRAFT, MissionState.QUEUED) is True
    assert is_valid_transition("draft", "queued") is True


def test_invalid_transitions_raise_exception():
    """Verify that illegal transitions raise InvalidMissionTransition."""
    # UNKNOWN directly to VERIFIED must fail
    with pytest.raises(InvalidMissionTransition, match="Invalid mission state transition"):
        assert_transition(MissionState.UNKNOWN, MissionState.VERIFIED)

    # Terminal states cannot transition to anything
    terminal_states = [
        MissionState.VERIFIED,
        MissionState.FAILED_VERIFICATION,
        MissionState.CANCELLED,
        MissionState.FAILED,
        MissionState.TIMED_OUT,
    ]
    for term in terminal_states:
        with pytest.raises(InvalidMissionTransition):
            assert_transition(term, MissionState.RUNNING)
        with pytest.raises(InvalidMissionTransition):
            assert_transition(term, MissionState.QUEUED)
        assert is_valid_transition(term, MissionState.RUNNING) is False

    # Cannot skip stages (e.g. draft directly to running, draft to verified)
    with pytest.raises(InvalidMissionTransition):
        assert_transition(MissionState.DRAFT, MissionState.RUNNING)
    with pytest.raises(InvalidMissionTransition):
        assert_transition(MissionState.DRAFT, MissionState.VERIFIED)

    # String input support and validation
    with pytest.raises(InvalidMissionTransition):
        assert_transition("draft", "running")


def test_redaction_replaces_bearer_and_cookie_values():
    """Verify that redact_payload masks bearer tokens, cookies, and other secrets."""
    payload = {
        "authorization": "Bearer abcdefghijklmnopqrstuvwxyz",
        "cookie": "sid=secret_session_data",
        "normal_key": "safe_value",
    }
    redacted = redact_payload(payload)
    dumped = json.dumps(redacted)

    assert "abcdefghijklmnopqrstuvwxyz" not in dumped
    assert "secret_session_data" not in dumped
    assert redacted["authorization"] == "[REDACTED]"
    assert redacted["cookie"] == "[REDACTED]"
    assert redacted["normal_key"] == "safe_value"


def test_redaction_nested_structures_and_selective_token_matching():
    """Verify that deep nested dictionaries, lists, and token fields are redacted while token counts remain intact."""
    complex_payload = {
        "auth": {
            "token": "ghp_1234567890abcdef",
            "password": "supersecretpassword",
            "api_secret": "sk-proj-xyz987",
        },
        "items": [
            {"cookie": "csrftoken=abc123xyz"},
            {"name": "test_artifact", "sha256": "abcdef123456"},
        ],
        "usage": {
            "input_tokens": 120,
            "output_tokens": 45,
            "total_tokens": 165,
        },
    }
    redacted = redact_payload(complex_payload)
    dumped = json.dumps(redacted)

    assert "ghp_1234567890abcdef" not in dumped
    assert "supersecretpassword" not in dumped
    assert "sk-proj-xyz987" not in dumped
    assert "csrftoken=abc123xyz" not in dumped

    assert redacted["auth"]["token"] == "[REDACTED]"
    assert redacted["auth"]["password"] == "[REDACTED]"
    assert redacted["auth"]["api_secret"] == "[REDACTED]"
    assert redacted["items"][0]["cookie"] == "[REDACTED]"
    assert redacted["items"][1]["sha256"] == "abcdef123456"

    # Numeric token metrics are not redacted
    assert redacted["usage"]["input_tokens"] == 120
    assert redacted["usage"]["output_tokens"] == 45
    assert redacted["usage"]["total_tokens"] == 165
