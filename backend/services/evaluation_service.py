"""Evaluation service for closed-loop change verification and keep/revert/escalate decisions."""
from __future__ import annotations

from typing import Any
from backend.models.mission import EvaluationDecision, MeasurementRecord


class EvaluationService:
    """Evaluates change-oriented mission measurements against baselines."""

    def decide(
        self,
        measurement: MeasurementRecord,
        baseline_value: float | None = None,
        observed_value: float | None = None,
        higher_is_better: bool = True,
        escalation_delta: float | None = None,
    ) -> EvaluationDecision:
        """Decides whether to KEEP, REVERT, or ESCALATE based on measurement provenance and metrics.

        Fails closed:
        - If not measurement.comparable: returns EvaluationDecision.NEEDS_VERIFICATION
        - If measurement.observed_artifact_id is None: returns EvaluationDecision.NEEDS_VERIFICATION
        - If comparable and valid: evaluates metric and returns EvaluationDecision.KEEP, REVERT, or ESCALATE.
        """
        # Incomparable measurement cannot prove change
        if not measurement.comparable:
            return EvaluationDecision.NEEDS_VERIFICATION

        # Missing observed artifact has no empirical evidence
        if measurement.observed_artifact_id is None:
            return EvaluationDecision.NEEDS_VERIFICATION

        # Check explicit method hints
        method_str = (measurement.method or "").lower()
        if "escalate" in method_str:
            return EvaluationDecision.ESCALATE
        if "revert" in method_str:
            return EvaluationDecision.REVERT

        # Quantitative metric evaluation
        if baseline_value is not None and observed_value is not None:
            delta = (
                (observed_value - baseline_value)
                if higher_is_better
                else (baseline_value - observed_value)
            )

            # Check severe regression / escalation threshold
            if escalation_delta is not None and delta <= -abs(escalation_delta):
                return EvaluationDecision.ESCALATE

            # Any negative delta is a regression warranting revert
            if delta < 0:
                return EvaluationDecision.REVERT

            return EvaluationDecision.KEEP

        # Default for verified, comparable measurement with positive observation
        return EvaluationDecision.KEEP


__all__ = ["EvaluationService", "EvaluationDecision"]
