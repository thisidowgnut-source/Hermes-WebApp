"""Pydantic request/response models, enums, and event schemas for missions."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PrimaryExecutor(str, Enum):
    AGY = "agy"
    HERMES = "hermes"


class MissionState(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    WAITING_APPROVAL = "waiting_approval"
    SUCCEEDED = "succeeded"
    NEEDS_VERIFICATION = "needs_verification"
    VERIFIED = "verified"
    FAILED_VERIFICATION = "failed_verification"
    INTERRUPTED = "interrupted"
    UNKNOWN = "unknown"
    CANCELLED = "cancelled"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class RiskClass(str, Enum):
    LOW = "low"
    REVIEW = "review"
    HUMAN_REQUIRED = "human_required"


class EvaluationDecision(str, Enum):
    KEEP = "keep"
    REVERT = "revert"
    ESCALATE = "escalate"
    NEEDS_VERIFICATION = "needs_verification"


class UsageRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int = 0


class NormalizedAgyEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    event_type: str
    provider_conversation_id: str | None = None
    state: str | None = None
    text_delta: str | None = None
    result_status: str | None = None
    usage: UsageRecord | None = None
    tool_name: str | None = None
    created_at: datetime


class AgentProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    display_name: str
    execution: str = "agy"


class ApprovalPolicy(BaseModel):
    model_config = ConfigDict(extra="ignore")
    social_requires_human_confirmation: bool = True
    approval_ttl_seconds: int = 900


class ProjectProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    slug: str
    display_name: str | None = None
    workspace_path: Path
    agy_project_id: str | None = None
    brand_truth_path: Path
    agents: dict[str, AgentProfile]
    approval_policy: ApprovalPolicy

    @property
    def enabled_agents(self) -> list[str]:
        return list(self.agents.keys())


class CreateMissionRequest(BaseModel):
    project_slug: str
    title: str
    objective: str
    primary_executor: PrimaryExecutor
    agent_profile: str
    idempotency_key: UUID


class CreateTurnRequest(BaseModel):
    message: str
    idempotency_key: UUID


class OperatorContext(BaseModel):
    operator_id: int
    username: str | None = None
    session_id: UUID
    is_local_development: bool = False


class PlanningPacket(BaseModel):
    mission_id: UUID
    objective: str
    constraints: list[str] = Field(default_factory=list)
    evidence_artifact_ids: list[UUID] = Field(default_factory=list)
    risk_class: RiskClass
    selected_capability_ids: list[str] = Field(default_factory=list)
    policy_version: str
    iteration_budget: int
    child_concurrency_budget: int
    acceptance_checks: list[str] = Field(default_factory=list)
    sha256: str


class CapabilityReceipt(BaseModel):
    registry_version: str
    mission_intent: str
    selected_capability_ids: list[str] = Field(default_factory=list)
    denied_capability_ids: list[str] = Field(default_factory=list)
    selected_at: datetime


class MeasurementRecord(BaseModel):
    mission_id: UUID
    metric_name: str
    baseline_artifact_id: UUID
    observed_artifact_id: UUID | None = None
    method: str
    comparable: bool
    observed_at: datetime | None = None


class MissionSnapshot(dict):
    """Snapshot representation of a mission, providing both dict and attribute access."""
    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'MissionSnapshot' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        self[name] = value


class MissionEvent(dict):
    """Event representation for a mission, providing both dict and attribute access."""
    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'MissionEvent' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        self[name] = value


class TurnRecord(dict):
    """Turn representation for a mission, providing both dict and attribute access."""
    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'TurnRecord' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        self[name] = value


class RunRecord(dict):
    """Run representation for a mission, providing both dict and attribute access."""
    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'RunRecord' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        self[name] = value


class RunReconciliation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    run_id: str
    mission_id: str
    previous_state: str
    new_state: str
    reason: str

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


class CapabilityResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    component: str
    status: str  # "available", "degraded", "unavailable"
    checked_at: datetime
    evidence: str
    version: Optional[str] = None
    recovery_action: Optional[str] = None

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


class CostRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    run_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    duration_seconds: Optional[float] = None
    created_at: datetime | str

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


class StartupReconciliation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    reconciled_runs: list[RunReconciliation] = Field(default_factory=list)
    reconciled_count: int = 0
    timestamp: datetime

