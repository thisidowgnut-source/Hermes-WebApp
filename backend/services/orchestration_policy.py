"""Astra-aligned orchestration policy, planning packet service, and risk containment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from backend.models.mission import MissionState, PlanningPacket, RiskClass


class PlanningPacketRequired(Exception):
    """Raised when multi-step Hermes or coordinator execution lacks a planning packet."""


class UnknownCapability(Exception):
    """Raised when an unregistered capability profile is requested."""


class BudgetExhausted(Exception):
    """Raised when iteration, concurrency, or elapsed time budgets are exceeded."""


class OrchestrationPolicy:
    """Loads and validates orchestration configuration, classifies intent risk, and gates states."""

    DEFAULT_POLICY_PATH = (
        Path(__file__).resolve().parent.parent.parent
        / "config"
        / "orchestration"
        / "defaults.json"
    )

    HUMAN_REQUIRED_KEYWORDS = (
        "publish",
        "credential",
        "browser_publish",
        "external",
        "financial",
        "destructive",
        "captcha",
        "2fa",
    )

    def __init__(self, config_path: Path | str | None = None) -> None:
        self.config_path = Path(config_path) if config_path else self.DEFAULT_POLICY_PATH
        self._load_and_validate()

    def _load_and_validate(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Orchestration policy config not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as err:
            raise ValueError(f"Failed to parse orchestration policy JSON: {err}") from err

        required_keys = (
            "policy_version",
            "iteration_budget",
            "child_concurrency_budget",
            "elapsed_seconds_budget",
            "risk_classes",
            "capabilities",
        )
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required orchestration policy field: {key}")

        if not isinstance(data["policy_version"], str) or not data["policy_version"].strip():
            raise ValueError("policy_version must be a non-empty string")

        for num_field in ("iteration_budget", "child_concurrency_budget", "elapsed_seconds_budget"):
            val = data.get(num_field)
            if not isinstance(val, int) or val <= 0:
                raise ValueError(f"{num_field} must be a positive integer, got: {val}")

        risk_classes = data.get("risk_classes")
        if not isinstance(risk_classes, dict):
            raise ValueError("risk_classes must be a dictionary")

        for risk_tier in ("low", "review", "human_required"):
            if risk_tier not in risk_classes or not isinstance(risk_classes[risk_tier], list):
                raise ValueError(f"risk_classes must contain a list for '{risk_tier}'")

        if not isinstance(data.get("capabilities"), dict):
            raise ValueError("capabilities must be a dictionary")

        self.config = data
        self.policy_version: str = data["policy_version"]
        self.iteration_budget: int = data["iteration_budget"]
        self.child_concurrency_budget: int = data["child_concurrency_budget"]
        self.elapsed_seconds_budget: int = data["elapsed_seconds_budget"]
        self.risk_classes: dict[str, list[str]] = data["risk_classes"]
        self.capabilities: dict[str, Any] = data["capabilities"]

    def _extract_intent_str(self, intent_or_request: Any) -> str:
        """Extracts text string safely from raw string or request-like object."""
        if hasattr(intent_or_request, "intent"):
            return str(getattr(intent_or_request, "intent"))
        if hasattr(intent_or_request, "action"):
            return str(getattr(intent_or_request, "action"))
        if hasattr(intent_or_request, "message"):
            return str(getattr(intent_or_request, "message"))
        if hasattr(intent_or_request, "objective"):
            return str(getattr(intent_or_request, "objective"))
        return str(intent_or_request)

    def classify(self, intent: str | Any) -> RiskClass:
        """Classifies intent into RiskClass (LOW, REVIEW, HUMAN_REQUIRED).

        Any intent containing publish, credential, browser_publish, external
        returns RiskClass.HUMAN_REQUIRED.
        """
        raw_text = self._extract_intent_str(intent).strip().lower()

        # Check explicit keywords
        for keyword in self.HUMAN_REQUIRED_KEYWORDS:
            if keyword in raw_text:
                return RiskClass.HUMAN_REQUIRED

        # Check configured risk classes lists
        for configured_intent in self.risk_classes.get("human_required", []):
            if configured_intent.lower() in raw_text:
                return RiskClass.HUMAN_REQUIRED

        for configured_intent in self.risk_classes.get("review", []):
            if configured_intent.lower() in raw_text or raw_text == configured_intent.lower():
                return RiskClass.REVIEW

        for configured_intent in self.risk_classes.get("low", []):
            if configured_intent.lower() in raw_text or raw_text == configured_intent.lower():
                return RiskClass.LOW

        # Unknown or unmatched intent defaults to REVIEW for containment
        return RiskClass.REVIEW

    def transition_for_intent(self, intent: str | Any) -> MissionState:
        """Returns MissionState based on intent risk classification.

        If HUMAN_REQUIRED returns MissionState.WAITING_HUMAN,
        else MissionState.STARTING.
        """
        risk = self.classify(intent)
        if risk == RiskClass.HUMAN_REQUIRED:
            return MissionState.WAITING_HUMAN
        return MissionState.STARTING

    def transition_for(self, intent_or_request: str | Any) -> MissionState:
        """Convenience alias for transition_for_intent."""
        return self.transition_for_intent(intent_or_request)

    def validate_packet_for_multistep(
        self,
        packet: PlanningPacket | None,
        is_multistep: bool = True,
    ) -> None:
        """Fails closed if a multi-step execution lacks a persisted planning packet."""
        if is_multistep and packet is None:
            raise PlanningPacketRequired(
                "A persisted planning packet is required for multi-step execution before entering running."
            )

    def enforce_iteration_budget(self, current_iterations: int, budget: int | None = None) -> None:
        """Enforces iteration limits without silent retries."""
        limit = budget if budget is not None else self.iteration_budget
        if current_iterations >= limit:
            raise BudgetExhausted(
                f"Iteration budget exhausted: {current_iterations} >= {limit}. Halting execution."
            )

    def enforce_concurrency_budget(self, current_children: int, budget: int | None = None) -> None:
        """Enforces child concurrency limits."""
        limit = budget if budget is not None else self.child_concurrency_budget
        if current_children >= limit:
            raise BudgetExhausted(
                f"Child concurrency budget exhausted: {current_children} >= {limit}."
            )


class PlanningPacketService:
    """Constructs and validates cryptographic planning packets for missions."""

    def __init__(self, policy: OrchestrationPolicy | None = None) -> None:
        self.policy = policy or OrchestrationPolicy()

    def create_for_mission(
        self,
        mission_id: UUID,
        objective: str,
        intent: str,
        evidence_artifact_ids: list[UUID],
        capabilities: list[str],
        iteration_budget: int = 25,
        child_concurrency_budget: int = 3,
        constraints: list[str] | None = None,
        acceptance_checks: list[str] | None = None,
        policy_version: str | None = None,
    ) -> PlanningPacket:
        """Creates an immutable PlanningPacket with a canonical SHA256 digest."""
        risk_class = self.policy.classify(intent)
        effective_policy_version = policy_version or self.policy.policy_version
        effective_constraints = constraints or []
        effective_acceptance_checks = acceptance_checks or []

        # Build canonical payload for deterministic SHA256
        canonical_dict = {
            "mission_id": str(mission_id),
            "objective": objective,
            "constraints": effective_constraints,
            "evidence_artifact_ids": sorted(str(artifact_id) for artifact_id in evidence_artifact_ids),
            "risk_class": risk_class.value,
            "selected_capability_ids": sorted(capabilities),
            "policy_version": effective_policy_version,
            "iteration_budget": iteration_budget,
            "child_concurrency_budget": child_concurrency_budget,
            "acceptance_checks": effective_acceptance_checks,
        }
        canonical_bytes = json.dumps(
            canonical_dict,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        packet_sha256 = hashlib.sha256(canonical_bytes).hexdigest()

        return PlanningPacket(
            mission_id=mission_id,
            objective=objective,
            constraints=effective_constraints,
            evidence_artifact_ids=evidence_artifact_ids,
            risk_class=risk_class,
            selected_capability_ids=capabilities,
            policy_version=effective_policy_version,
            iteration_budget=iteration_budget,
            child_concurrency_budget=child_concurrency_budget,
            acceptance_checks=effective_acceptance_checks,
            sha256=packet_sha256,
        )

    def validate_multistep_requirement(
        self,
        packet: PlanningPacket | None,
        is_multistep: bool = True,
    ) -> None:
        """Validates that a planning packet is present for multi-step tasks."""
        if is_multistep and packet is None:
            raise PlanningPacketRequired(
                "A verified planning packet is required for multi-step execution."
            )
