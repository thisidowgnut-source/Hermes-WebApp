"""Unit tests for AGY stream-json protocol parser."""
from datetime import datetime, timezone
from pathlib import Path
import pytest

from backend.services.agy_protocol import (
    AgyProtocolError,
    parse_agy_stream_line,
)
from backend.models.mission import NormalizedAgyEvent

FIXED_NOW = datetime(2026, 9, 16, 6, 0, 0, tzinfo=timezone.utc)
RESULT_LINE = (
    '{"event":"result","result":{"conversation_id":"11111111-1111-1111-1111-111111111111",'
    '"status":"SUCCESS","response":"Prepared draft.","duration_seconds":2.5,"num_turns":1,'
    '"usage":{"input_tokens":10,"output_tokens":5,"thinking_tokens":1,"cache_read_tokens":0,"total_tokens":16}}}'
)
INIT_LINE = (
    '{"event":"init","conversation_id":"11111111-1111-1111-1111-111111111111",'
    '"init":{"cwd":"G:/Doh-Nut","permission_mode":"request-review"}}'
)
STEP_LINE = (
    '{"event":"step_update","step_update":{"conversation_id":"11111111-1111-1111-1111-111111111111",'
    '"step_index":1,"state":"ACTIVE","step_type":"agent_response","text_delta":"Draft is being prepared."}}'
)


def test_result_event_preserves_conversation_and_usage():
    event = parse_agy_stream_line(RESULT_LINE, FIXED_NOW)
    assert isinstance(event, NormalizedAgyEvent)
    assert event.event_type == "agy.result"
    assert event.provider_conversation_id == "11111111-1111-1111-1111-111111111111"
    assert event.result_status == "SUCCESS"
    assert event.usage is not None
    assert event.usage.total_tokens == 16
    assert event.usage.input_tokens == 10
    assert event.usage.output_tokens == 5
    assert event.created_at == FIXED_NOW


def test_init_event_parsed_correctly():
    event = parse_agy_stream_line(INIT_LINE, FIXED_NOW)
    assert isinstance(event, NormalizedAgyEvent)
    assert event.event_type == "agy.init"
    assert event.provider_conversation_id == "11111111-1111-1111-1111-111111111111"
    assert event.state == "INITIALIZED"


def test_step_update_event_parsed_correctly():
    event = parse_agy_stream_line(STEP_LINE, FIXED_NOW)
    assert isinstance(event, NormalizedAgyEvent)
    assert event.event_type == "agy.step"
    assert event.provider_conversation_id == "11111111-1111-1111-1111-111111111111"
    assert event.state == "ACTIVE"
    assert event.text_delta == "Draft is being prepared."


def test_malformed_json_raises_typed_error():
    with pytest.raises(AgyProtocolError, match="malformed_json"):
        parse_agy_stream_line("{not-json}", FIXED_NOW)


def test_unknown_event_is_diagnostic_not_a_crash():
    assert parse_agy_stream_line('{"event":"future_event"}', FIXED_NOW) is None
    assert parse_agy_stream_line('{"event":"unknown_type","data":{}}', FIXED_NOW) is None


def test_missing_result_dictionary_raises_typed_error():
    with pytest.raises(AgyProtocolError, match="missing_result"):
        parse_agy_stream_line('{"event":"result"}', FIXED_NOW)
    with pytest.raises(AgyProtocolError, match="missing_result"):
        parse_agy_stream_line('{"event":"result","result":"not-a-dict"}', FIXED_NOW)


def test_missing_init_or_step_subdict_raises_unsupported_shape():
    with pytest.raises(AgyProtocolError, match="unsupported_shape"):
        parse_agy_stream_line('{"event":"init","conversation_id":"bad"}', FIXED_NOW)
    with pytest.raises(AgyProtocolError, match="unsupported_shape"):
        parse_agy_stream_line('{"event":"step_update"}', FIXED_NOW)


def test_invalid_usage_raises_typed_error():
    bad_usage_line = (
        '{"event":"result","result":{"conversation_id":"333","status":"SUCCESS",'
        '"usage":{"total_tokens":"not_a_number"}}}'
    )
    with pytest.raises(AgyProtocolError, match="invalid_usage"):
        parse_agy_stream_line(bad_usage_line, FIXED_NOW)


def test_stream_success_fixture_parses_fully():
    fixture_path = Path(__file__).parent / "fixtures" / "agy" / "stream_success.ndjson"
    lines = [l.strip() for l in fixture_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    events = [parse_agy_stream_line(line, FIXED_NOW) for line in lines]
    assert len(events) == 3
    assert [e.event_type for e in events] == ["agy.init", "agy.step", "agy.result"]
    assert events[2].result_status == "SUCCESS"


def test_stream_error_fixture_parses_fully():
    fixture_path = Path(__file__).parent / "fixtures" / "agy" / "stream_error.ndjson"
    lines = [l.strip() for l in fixture_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    events = [parse_agy_stream_line(line, FIXED_NOW) for line in lines]
    assert len(events) == 3
    assert events[2].result_status == "ERROR"
    assert events[2].usage.total_tokens == 5
