"""Unit tests for OrchestrationPolicy, PlanningPacketService, and risk gating."""
import json
from pathlib import Path
import tempfile
import uuid
import pytest

from backend.models.mission import MissionState, RiskClass
from backend.services.orchestration_policy import (
    BudgetExhausted,
    OrchestrationPolicy,
    PlanningPacketRequired,
    PlanningPacketService,
)


class MockRequest:
    def __init__(self, intent: str) -> None:
        self.intent = intent


def test_orchestration_policy_loads_defaults():
    policy = OrchestrationPolicy()
    assert policy.policy_version == "1.0.0"
    assert policy.iteration_budget == 25
    assert policy.child_concurrency_budget == 3
    assert policy.elapsed_seconds_budget == 1800
    assert "low" in policy.risk_classes
    assert "review" in policy.risk_classes
    assert "human_required" in policy.risk_classes
    assert "plan" in policy.capabilities
    assert "verify" in policy.capabilities
    assert "kanban_sync" in policy.capabilities


def test_orchestration_policy_fails_closed_on_missing_or_corrupt():
    with pytest.raises(FileNotFoundError):
        OrchestrationPolicy("nonexistent_path_to_policy.json")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write("{invalid_json}")
        corrupt_path = f.name
    try:
        with pytest.raises(ValueError):
            OrchestrationPolicy(corrupt_path)
    finally:
        Path(corrupt_path).unlink(missing_ok=True)


def test_orchestration_policy_classification():
    policy = OrchestrationPolicy()

    # Low risk
    assert policy.classify("plan") == RiskClass.LOW
    assert policy.classify("verify") == RiskClass.LOW
    assert policy.classify("kanban_sync") == RiskClass.LOW
    assert policy.classify("code_index_read") == RiskClass.LOW

    # Review risk
    assert policy.classify("draft_social") == RiskClass.REVIEW
    assert policy.classify("write_spec") == RiskClass.REVIEW
    assert policy.classify("benchmark") == RiskClass.REVIEW

    # Human required - explicit triggers
    assert policy.classify("browser_publish") == RiskClass.HUMAN_REQUIRED
    assert policy.classify("publish new social campaign") == RiskClass.HUMAN_REQUIRED
    assert policy.classify("credential_write") == RiskClass.HUMAN_REQUIRED
    assert policy.classify("update secret credential") == RiskClass.HUMAN_REQUIRED
    assert policy.classify("financial_action") == RiskClass.HUMAN_REQUIRED
    assert policy.classify("external_transmission") == RiskClass.HUMAN_REQUIRED
    assert policy.classify("execute external api transfer") == RiskClass.HUMAN_REQUIRED

    # Request-like object
    req = MockRequest("browser_publish")
    assert policy.classify(req) == RiskClass.HUMAN_REQUIRED


def test_transition_for_intent():
    policy = OrchestrationPolicy()

    # High-risk intents transition to WAITING_HUMAN
    assert policy.transition_for_intent("browser_publish") == MissionState.WAITING_HUMAN
    assert policy.transition_for_intent("external_transmission") == MissionState.WAITING_HUMAN
    assert policy.transition_for_intent("credential_write") == MissionState.WAITING_HUMAN
    assert policy.transition_for(MockRequest("publish_post")) == MissionState.WAITING_HUMAN

    # Safe / low / review intents transition to STARTING
    assert policy.transition_for_intent("plan") == MissionState.STARTING
    assert policy.transition_for_intent("verify") == MissionState.STARTING
    assert policy.transition_for_intent("draft_social") == MissionState.STARTING


def test_planning_packet_creation_and_sha256():
    service = PlanningPacketService()
    mission_id = uuid.uuid4()
    art_id1 = uuid.uuid4()
    art_id2 = uuid.uuid4()

    packet = service.create_for_mission(
        mission_id=mission_id,
        objective="Create comprehensive test plan",
        intent="plan",
        evidence_artifact_ids=[art_id1, art_id2],
        capabilities=["cap-plan"],
        iteration_budget=25,
        child_concurrency_budget=3,
    )

    assert packet.mission_id == mission_id
    assert packet.risk_class == RiskClass.LOW
    assert packet.selected_capability_ids == ["cap-plan"]
    assert packet.policy_version == "1.0.0"
    assert packet.iteration_budget == 25
    assert packet.child_concurrency_budget == 3
    assert len(packet.sha256) == 64  # SHA256 hex string

    # Create another packet with identical payload -> identical SHA256
    packet_same = service.create_for_mission(
        mission_id=mission_id,
        objective="Create comprehensive test plan",
        intent="plan",
        evidence_artifact_ids=[art_id1, art_id2],
        capabilities=["cap-plan"],
        iteration_budget=25,
        child_concurrency_budget=3,
    )
    assert packet.sha256 == packet_same.sha256

    # Packet with changed objective -> different SHA256
    packet_diff = service.create_for_mission(
        mission_id=mission_id,
        objective="Different objective",
        intent="plan",
        evidence_artifact_ids=[art_id1, art_id2],
        capabilities=["cap-plan"],
        iteration_budget=25,
        child_concurrency_budget=3,
    )
    assert packet.sha256 != packet_diff.sha256


def test_multistep_planning_packet_requirement():
    service = PlanningPacketService()
    policy = OrchestrationPolicy()

    # None packet with multistep raises PlanningPacketRequired
    with pytest.raises(PlanningPacketRequired, match="planning packet is required"):
        service.validate_multistep_requirement(packet=None, is_multistep=True)

    with pytest.raises(PlanningPacketRequired, match="planning packet is required"):
        policy.validate_packet_for_multistep(packet=None, is_multistep=True)

    # With packet, validation passes
    mission_id = uuid.uuid4()
    packet = service.create_for_mission(
        mission_id=mission_id,
        objective="Multi-step test",
        intent="plan",
        evidence_artifact_ids=[],
        capabilities=["cap-plan"],
    )
    service.validate_multistep_requirement(packet=packet, is_multistep=True)
    policy.validate_packet_for_multistep(packet=packet, is_multistep=True)

    # Single-step without packet does not raise
    service.validate_multistep_requirement(packet=None, is_multistep=False)
    policy.validate_packet_for_multistep(packet=None, is_multistep=False)


def test_budget_exhaustion_enforcement():
    policy = OrchestrationPolicy()

    # Normal execution within budget does not raise
    policy.enforce_iteration_budget(current_iterations=10, budget=25)
    policy.enforce_iteration_budget(current_iterations=24, budget=25)

    # Exceeding budget raises BudgetExhausted
    with pytest.raises(BudgetExhausted, match="Iteration budget exhausted"):
        policy.enforce_iteration_budget(current_iterations=25, budget=25)

    with pytest.raises(BudgetExhausted, match="Iteration budget exhausted"):
        policy.enforce_iteration_budget(current_iterations=30, budget=25)

    # Concurrency budget
    policy.enforce_concurrency_budget(current_children=2, budget=3)
    with pytest.raises(BudgetExhausted, match="Child concurrency budget exhausted"):
        policy.enforce_concurrency_budget(current_children=3, budget=3)
