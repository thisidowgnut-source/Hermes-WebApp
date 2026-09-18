"""Unit and integration tests for SQLite WAL mission store."""
import uuid
import pytest

from backend.models.mission import (
    CreateMissionRequest,
    CreateTurnRequest,
    MissionState,
    OperatorContext,
    PrimaryExecutor,
)
from backend.services.mission_policy import InvalidMissionTransition
from backend.services.mission_store import MissionStore


@pytest.fixture
def store(tmp_path):
    """Provide an initialized MissionStore using a temporary SQLite database."""
    db_path = tmp_path / "test_missions.db"
    s = MissionStore(db_path)
    s.initialize()
    return s


@pytest.fixture
def operator():
    """Standard operator context for testing."""
    return OperatorContext(
        operator_id=12345,
        username="test_operator",
        session_id=uuid.uuid4(),
        is_local_development=True,
    )


@pytest.fixture
def create_request():
    """Sample CreateMissionRequest."""
    return CreateMissionRequest(
        project_slug="doh-nut",
        title="Test Doh-Nut Automation",
        objective="Run headless Doh-Nut workflow for remote testing",
        primary_executor=PrimaryExecutor.AGY,
        agent_profile="dohnut-orchestrator",
        idempotency_key=uuid.uuid4(),
    )


def test_same_operator_and_idempotency_key_creates_one_mission(store, operator, create_request):
    """Idempotency test: repeated calls with identical operator and idempotency_key must return same mission."""
    first = store.create_mission(create_request, operator)
    second = store.create_mission(create_request, operator)

    assert second.mission_id == first.mission_id
    assert second["mission_id"] == first["mission_id"]
    assert store.count_rows("missions") == 1
    assert store.count_rows("idempotency_keys") == 1

    # Only 1 initial mission.created event should have been recorded
    events = store.get_events(first.mission_id)
    assert len(events) == 1
    assert events[0].event_type == "mission.created"
    assert events[0].sequence == 1


def test_different_idempotency_key_creates_different_missions(store, operator, create_request):
    """Different idempotency key creates a second separate mission."""
    first = store.create_mission(create_request, operator)

    req2 = create_request.model_copy(update={"idempotency_key": uuid.uuid4(), "title": "Second Mission"})
    second = store.create_mission(req2, operator)

    assert second.mission_id != first.mission_id
    assert store.count_rows("missions") == 2
    assert store.count_rows("idempotency_keys") == 2


def test_monotonic_event_sequencing_per_mission(store, operator, create_request):
    """Verify that event sequences are allocated strictly monotonically (1, 2, 3...) per mission."""
    mission_a = store.create_mission(create_request, operator)
    # create_mission records event sequence 1 ("mission.created")
    ev2 = store.append_event(mission_a.mission_id, "run.queued", {"attempt": 1})
    ev3 = store.append_event(mission_a.mission_id, "run.starting", {"executor": "agy"})
    ev4 = store.append_event(
        mission_a.mission_id,
        "step.progress",
        {"authorization": "Bearer super-secret", "status": "active"},
    )

    assert ev2.sequence == 2
    assert ev3.sequence == 3
    assert ev4.sequence == 4

    # Redaction check on event payload
    assert ev4.payload["authorization"] == "[REDACTED]"
    assert ev4.payload["status"] == "active"

    # Separate mission must start its own sequence from 1
    req_b = create_request.model_copy(update={"idempotency_key": uuid.uuid4()})
    mission_b = store.create_mission(req_b, operator)
    events_b = store.get_events(mission_b.mission_id)
    assert len(events_b) == 1
    assert events_b[0].sequence == 1

    ev_b2 = store.append_event(mission_b.mission_id, "run.queued", {})
    assert ev_b2.sequence == 2


def test_get_events_after_sequence_filter(store, operator, create_request):
    """Verify that get_events filters results correctly using after_sequence."""
    mission = store.create_mission(create_request, operator)
    store.append_event(mission.mission_id, "ev2", {})
    store.append_event(mission.mission_id, "ev3", {})
    store.append_event(mission.mission_id, "ev4", {})
    store.append_event(mission.mission_id, "ev5", {})

    all_events = store.get_events(mission.mission_id)
    assert len(all_events) == 5
    assert [e.sequence for e in all_events] == [1, 2, 3, 4, 5]

    after_2 = store.get_events(mission.mission_id, after_sequence=2)
    assert len(after_2) == 3
    assert [e.sequence for e in after_2] == [3, 4, 5]

    after_4 = store.get_events(mission.mission_id, after_sequence=4)
    assert len(after_4) == 1
    assert after_4[0].sequence == 5

    after_5 = store.get_events(mission.mission_id, after_sequence=5)
    assert len(after_5) == 0


def test_update_mission_state_transition_enforcement(store, operator, create_request):
    """Verify that update_mission_state enforces state machine policy and records transition events."""
    mission = store.create_mission(create_request, operator)
    assert mission.state == MissionState.DRAFT.value

    # Legal transition: DRAFT -> QUEUED
    store.update_mission_state(mission.mission_id, MissionState.QUEUED)
    fetched = store.get_mission(mission.mission_id)
    assert fetched.state == MissionState.QUEUED.value

    # Illegal transition: QUEUED -> VERIFIED must raise InvalidMissionTransition
    with pytest.raises(InvalidMissionTransition):
        store.update_mission_state(mission.mission_id, MissionState.VERIFIED)

    # State must remain unchanged after failed transition
    fetched = store.get_mission(mission.mission_id)
    assert fetched.state == MissionState.QUEUED.value

    # Legal progression: QUEUED -> STARTING -> RUNNING -> SUCCEEDED -> VERIFIED
    store.update_mission_state(mission.mission_id, MissionState.STARTING)
    store.update_mission_state(mission.mission_id, MissionState.RUNNING)
    store.update_mission_state(mission.mission_id, MissionState.SUCCEEDED)
    store.update_mission_state(mission.mission_id, MissionState.VERIFIED)

    final_snapshot = store.get_mission(mission.mission_id)
    assert final_snapshot.state == MissionState.VERIFIED.value

    # Terminal state check: VERIFIED -> RUNNING must raise
    with pytest.raises(InvalidMissionTransition):
        store.update_mission_state(mission.mission_id, MissionState.RUNNING)

    # State transition events should be appended to the ledger
    events = store.get_events(mission.mission_id)
    state_changed_events = [e for e in events if e.event_type == "mission.state_changed"]
    assert len(state_changed_events) == 5  # DRAFT->QUEUED, QUEUED->STARTING, STARTING->RUNNING, RUNNING->SUCCEEDED, SUCCEEDED->VERIFIED


def test_get_mission_nonexistent_returns_none(store):
    """Querying an unknown mission ID returns None."""
    assert store.get_mission(uuid.uuid4()) is None
    assert store.get_mission("nonexistent-id") is None


def test_update_mission_state_nonexistent_raises_value_error(store):
    """Updating a nonexistent mission raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        store.update_mission_state(uuid.uuid4(), MissionState.RUNNING)


def test_enqueue_turn_allocates_sequence_and_appends_event(store, operator, create_request):
    """Verify turn queuing behavior and event recording."""
    mission = store.create_mission(create_request, operator)

    turn_req1 = CreateTurnRequest(message="Run tests for dohnut", idempotency_key=uuid.uuid4())
    turn1 = store.enqueue_turn(mission.mission_id, turn_req1, operator)

    assert turn1.sequence == 1
    assert turn1.message == "Run tests for dohnut"
    assert turn1.state == "queued"

    turn_req2 = CreateTurnRequest(message="Confirm results", idempotency_key=uuid.uuid4())
    turn2 = store.enqueue_turn(mission.mission_id, turn_req2, operator)

    assert turn2.sequence == 2
    assert store.count_rows("mission_turns") == 2

    turn_events = [e for e in store.get_events(mission.mission_id) if e.event_type == "turn.enqueued"]
    assert len(turn_events) == 2
    assert turn_events[0].payload["message"] == "Run tests for dohnut"
    assert turn_events[1].payload["message"] == "Confirm results"
