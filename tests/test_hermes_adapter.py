"""Unit tests for HermesAdapter, capability gating, and one-hop handoff validation."""
from uuid import uuid4
import pytest

from backend.services.hermes_adapter import (
    DelegationLoopError,
    HermesAdapter,
    HermesTaskRequest,
    HermesTaskResult,
    HermesUnsupportedError,
    HandoffProposal,
    validate_handoff,
)


def test_disabled_hermes_returns_unsupported():
    """Verify disabled Hermes returns status='unsupported' without raising an error."""
    adapter = HermesAdapter(enabled=False)
    assert adapter.is_available() == {"status": "disabled", "version": "1.0.0"}

    request = HermesTaskRequest(
        task_type="plan",
        prompt="Analyze codebase and create task blueprint",
    )
    result = adapter.submit(request)
    assert isinstance(result, HermesTaskResult)
    assert result.status == "unsupported"
    assert result.granted_capabilities == []
    assert result.output_artifacts == []
    assert result.execution_duration_seconds == 0.0


def test_handoff_cannot_exceed_depth_1():
    """Verify handoff depth cannot exceed 1 and raises DelegationLoopError."""
    adapter = HermesAdapter(enabled=True)
    source_mission_id = uuid4()

    # Depth 2: must fail
    request_depth_2 = HermesTaskRequest(
        task_type="plan",
        prompt="Recursive sub-delegation",
        handoff_depth=2,
    )
    with pytest.raises(DelegationLoopError, match="Handoff depth exceeded limit of 1"):
        adapter.validate_handoff(source_mission_id, request_depth_2)

    # Depth 3: must fail
    request_depth_3 = HermesTaskRequest(
        task_type="verify",
        prompt="Deep verification",
        handoff_depth=3,
    )
    with pytest.raises(DelegationLoopError, match="Handoff depth exceeded limit of 1"):
        adapter.validate_handoff(source_mission_id, request_depth_3)

    # Depth 1: allowed (single hop)
    request_depth_1 = HermesTaskRequest(
        task_type="plan",
        prompt="One-hop plan request",
        handoff_depth=1,
    )
    adapter.validate_handoff(source_mission_id, request_depth_1)

    # Depth 0: allowed
    request_depth_0 = HermesTaskRequest(
        task_type="verify",
        prompt="Direct task",
        handoff_depth=0,
    )
    adapter.validate_handoff(source_mission_id, request_depth_0)


def test_handoff_cannot_return_to_ancestor_mission():
    """Verify handoff cycle detection raises DelegationLoopError when returning to an ancestor."""
    adapter = HermesAdapter(enabled=True)
    source_mission_id = uuid4()
    origin_mission_id = uuid4()
    intermediate_mission_id = uuid4()

    # Ancestry containing origin_mission_id -> must raise cycle error
    cyclic_request = HermesTaskRequest(
        task_type="plan",
        prompt="Attempting to delegate back to origin",
        origin_mission_id=origin_mission_id,
        ancestry_ids=[intermediate_mission_id, origin_mission_id],
        handoff_depth=1,
    )
    with pytest.raises(DelegationLoopError, match="Cycle detected in delegation ancestry"):
        adapter.validate_handoff(source_mission_id, cyclic_request)

    # Cycle detection with string UUID representation
    cyclic_request_str = HermesTaskRequest(
        task_type="verify",
        prompt="Cycle with string ID",
        origin_mission_id=origin_mission_id,
        ancestry_ids=[str(origin_mission_id)],
        handoff_depth=1,
    )
    with pytest.raises(DelegationLoopError, match="Cycle detected in delegation ancestry"):
        adapter.validate_handoff(source_mission_id, cyclic_request_str)

    # Valid handoff where origin is not in ancestry
    valid_request = HermesTaskRequest(
        task_type="plan",
        prompt="Valid handoff without cycle",
        origin_mission_id=origin_mission_id,
        ancestry_ids=[intermediate_mission_id],
        handoff_depth=1,
    )
    adapter.validate_handoff(source_mission_id, valid_request)


def test_hermes_plan_has_no_browser_or_social_permissions():
    """Verify Hermes coordinator plan never grants browser, social, or shell capabilities."""
    adapter = HermesAdapter(enabled=True)
    assert adapter.is_available() == {"status": "available", "version": "1.0.0"}

    # Standard plan request
    plan_request = HermesTaskRequest(
        task_type="plan",
        prompt="Generate execution plan for Doh-Nut campaign",
    )
    result = adapter.submit(plan_request)
    assert result.status in {"succeeded", "unsupported"}
    assert result.status == "succeeded"
    assert "browser" not in result.granted_capabilities
    assert "social" not in result.granted_capabilities
    assert "shell" not in result.granted_capabilities
    assert "plan" in result.granted_capabilities

    # Request attempting to escalate with forbidden capabilities
    escalation_request = HermesTaskRequest(
        task_type="plan",
        prompt="Attempting to gain dangerous permissions",
        requested_capabilities=["plan", "browser", "social", "shell", "bash"],
    )
    escalation_result = adapter.submit(escalation_request)
    assert escalation_result.status == "succeeded"
    assert "browser" not in escalation_result.granted_capabilities
    assert "social" not in escalation_result.granted_capabilities
    assert "shell" not in escalation_result.granted_capabilities
    assert "bash" not in escalation_result.granted_capabilities
    assert escalation_result.granted_capabilities == ["plan"]


def test_hermes_forbidden_task_types_return_unsupported():
    """Verify tasks requesting forbidden types directly (e.g. browser, social, shell) are rejected."""
    adapter = HermesAdapter(enabled=True)

    for forbidden_type in ("browser", "social", "shell", "destructive"):
        req = HermesTaskRequest(task_type=forbidden_type, prompt=f"Execute {forbidden_type}")
        result = adapter.submit(req)
        assert result.status == "unsupported"
        assert result.granted_capabilities == []


def test_propose_handoff_lifecycle():
    """Verify propose_handoff creates a valid HandoffProposal and rejects invalid handoffs."""
    adapter = HermesAdapter(enabled=True)
    source_id = uuid4()
    target_id = uuid4()

    valid_req = HermesTaskRequest(
        task_type="verify",
        prompt="Verify mission output",
        handoff_depth=1,
    )
    proposal = adapter.propose_handoff(
        source_mission_id=source_id,
        task_request=valid_req,
        target_mission_id=target_id,
    )
    assert isinstance(proposal, HandoffProposal)
    assert proposal.source_mission_id == source_id
    assert proposal.target_mission_id == target_id
    assert proposal.handoff_depth == 1
    assert proposal.task_request == valid_req

    # Invalid handoff raises DelegationLoopError via propose_handoff
    invalid_req = HermesTaskRequest(
        task_type="verify",
        prompt="Exceeded depth",
        handoff_depth=2,
    )
    with pytest.raises(DelegationLoopError, match="Handoff depth exceeded limit of 1"):
        adapter.propose_handoff(source_id, invalid_req)


def test_hermes_unsupported_error():
    """Verify HermesUnsupportedError exception is defined and catchable."""
    with pytest.raises(HermesUnsupportedError, match="Operation not supported"):
        raise HermesUnsupportedError("Operation not supported")
