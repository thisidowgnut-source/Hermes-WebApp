"""Hermes coordinator adapter providing feature-flagged task execution, capability containment, and bounded one-hop handoff validation."""
from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4

try:
    from backend.config import config
except ImportError:
    config = None  # type: ignore


class DelegationLoopError(Exception):
    """Raised when delegation depth exceeds limit or cyclic ancestry is detected."""
    pass


class HermesUnsupportedError(Exception):
    """Raised when an unsupported operation or capability is requested from Hermes."""
    pass


@dataclass
class HermesTaskRequest:
    """Request payload for submitting a task to the Hermes coordinator."""
    task_type: str  # "plan", "verify", "kanban_sync"
    prompt: str
    context_artifact_ids: list[UUID] = field(default_factory=list)
    origin_mission_id: UUID | None = None
    ancestry_ids: list[UUID] = field(default_factory=list)
    handoff_depth: int = 0
    requested_capabilities: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.context_artifact_ids is None:
            self.context_artifact_ids = []
        if self.ancestry_ids is None:
            self.ancestry_ids = []
        if self.requested_capabilities is None:
            self.requested_capabilities = []


@dataclass
class HermesTaskResult:
    """Execution result returned by the Hermes coordinator."""
    status: str = "unsupported"  # "succeeded", "unsupported", "failed"
    granted_capabilities: list[str] = field(default_factory=list)
    output_artifacts: list[dict[str, Any]] = field(default_factory=list)
    execution_duration_seconds: float = 0.0


@dataclass
class HandoffProposal:
    """Proposal for handing off execution between missions."""
    source_mission_id: UUID
    target_mission_id: UUID
    handoff_depth: int
    task_request: HermesTaskRequest


def validate_handoff(source_mission_id: UUID, target_task: HermesTaskRequest) -> None:
    """Validates that a handoff proposal complies with one-hop and cycle-free constraints.

    1. Checks handoff_depth <= 1. If handoff_depth > 1, raises DelegationLoopError("Handoff depth exceeded limit of 1").
    2. Checks origin_mission_id not in target_task.ancestry_ids. If present, raises DelegationLoopError("Cycle detected in delegation ancestry").
    """
    if target_task.handoff_depth > 1:
        raise DelegationLoopError("Handoff depth exceeded limit of 1")

    if target_task.origin_mission_id is not None:
        origin_str = str(target_task.origin_mission_id)
        ancestry_strs = {str(aid) for aid in target_task.ancestry_ids}
        if origin_str in ancestry_strs:
            raise DelegationLoopError("Cycle detected in delegation ancestry")


@runtime_checkable
class HermesAdapterProtocol(Protocol):
    def is_available(self) -> dict[str, str]:
        ...

    def submit(self, request: HermesTaskRequest) -> HermesTaskResult:
        ...

    def validate_handoff(self, source_mission_id: UUID, target_task: HermesTaskRequest) -> None:
        ...


class HermesAdapter:
    """Feature-flagged coordinator adapter for Hermes tasks with bounded handoffs and capability restrictions."""

    FORBIDDEN_CAPABILITIES: frozenset[str] = frozenset({"browser", "social", "shell"})
    ALLOWED_TASK_TYPES: frozenset[str] = frozenset({"plan", "verify", "kanban_sync"})

    def __init__(self, enabled: bool | None = None) -> None:
        if enabled is None:
            self.enabled: bool = getattr(config, "HERMES_ADAPTER_ENABLED", False) if config else False
        else:
            self.enabled: bool = bool(enabled)

    def is_available(self) -> dict[str, str]:
        """Returns availability status and adapter version."""
        return {
            "status": "available" if self.enabled else "disabled",
            "version": "1.0.0",
        }

    def submit(self, request: HermesTaskRequest) -> HermesTaskResult:
        """Submit a task to the Hermes coordinator.

        If not enabled, returns HermesTaskResult(status="unsupported", granted_capabilities=[]).
        Validates capabilities: Hermes adapter NEVER grants "browser", "social", or "shell" capabilities.
        Only grants "plan", "verify", or "kanban_sync".
        """
        if not self.enabled:
            return HermesTaskResult(status="unsupported", granted_capabilities=[])

        clean_task_type = (request.task_type or "").strip().lower()
        if clean_task_type in self.FORBIDDEN_CAPABILITIES or clean_task_type not in self.ALLOWED_TASK_TYPES:
            return HermesTaskResult(status="unsupported", granted_capabilities=[])

        start_time = time.monotonic()

        candidate_caps = [clean_task_type]
        if hasattr(request, "requested_capabilities") and request.requested_capabilities:
            for cap in request.requested_capabilities:
                c_clean = str(cap).strip().lower()
                if c_clean not in candidate_caps:
                    candidate_caps.append(c_clean)

        granted: list[str] = []
        for cap in candidate_caps:
            if cap in self.FORBIDDEN_CAPABILITIES:
                continue
            if cap in self.ALLOWED_TASK_TYPES and cap not in granted:
                granted.append(cap)

        # Final guarantee that no forbidden capabilities exist
        granted = [c for c in granted if c not in self.FORBIDDEN_CAPABILITIES and c in self.ALLOWED_TASK_TYPES]

        if not granted:
            return HermesTaskResult(status="unsupported", granted_capabilities=[])

        duration = time.monotonic() - start_time

        return HermesTaskResult(
            status="succeeded",
            granted_capabilities=granted,
            output_artifacts=[],
            execution_duration_seconds=round(duration, 4),
        )

    def validate_handoff(self, source_mission_id: UUID, target_task: HermesTaskRequest) -> None:
        """Validates that a handoff proposal complies with one-hop and cycle-free constraints."""
        validate_handoff(source_mission_id, target_task)

    def propose_handoff(
        self,
        source_mission_id: UUID,
        task_request: HermesTaskRequest,
        target_mission_id: UUID | None = None,
    ) -> HandoffProposal:
        """Validates and creates a bounded HandoffProposal."""
        self.validate_handoff(source_mission_id, task_request)
        if target_mission_id is None:
            target_mission_id = uuid4()
        return HandoffProposal(
            source_mission_id=source_mission_id,
            target_mission_id=target_mission_id,
            handoff_depth=task_request.handoff_depth,
            task_request=task_request,
        )


__all__ = [
    "DelegationLoopError",
    "HermesUnsupportedError",
    "HermesTaskRequest",
    "HermesTaskResult",
    "HandoffProposal",
    "validate_handoff",
    "HermesAdapterProtocol",
    "HermesAdapter",
]
