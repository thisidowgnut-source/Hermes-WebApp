"""Unit tests for EvaluationService and closed-loop change verification."""
from datetime import datetime, timezone
import uuid
import pytest

from backend.models.mission import EvaluationDecision, MeasurementRecord
from backend.services.evaluation_service import EvaluationService


@pytest.fixture
def evaluation_service():
    return EvaluationService()


@pytest.fixture
def valid_record():
    return MeasurementRecord(
        mission_id=uuid.uuid4(),
        metric_name="test_pass_rate",
        baseline_artifact_id=uuid.uuid4(),
        observed_artifact_id=uuid.uuid4(),
        method="pytest_suite",
        comparable=True,
        observed_at=datetime.now(timezone.utc),
    )


def test_incomparable_measurement_returns_needs_verification(evaluation_service, valid_record):
    incomparable_record = valid_record.model_copy(update={"comparable": False})
    decision = evaluation_service.decide(incomparable_record)
    assert decision == EvaluationDecision.NEEDS_VERIFICATION


def test_missing_observed_artifact_returns_needs_verification(evaluation_service, valid_record):
    missing_observed = valid_record.model_copy(update={"observed_artifact_id": None})
    decision = evaluation_service.decide(missing_observed)
    assert decision == EvaluationDecision.NEEDS_VERIFICATION


def test_valid_measurement_default_keep(evaluation_service, valid_record):
    decision = evaluation_service.decide(valid_record)
    assert decision == EvaluationDecision.KEEP


def test_metric_evaluation_improvement_returns_keep(evaluation_service, valid_record):
    # Pass rate improved from 80% to 95%
    decision = evaluation_service.decide(
        valid_record,
        baseline_value=80.0,
        observed_value=95.0,
        higher_is_better=True,
    )
    assert decision == EvaluationDecision.KEEP


def test_metric_evaluation_regression_returns_revert(evaluation_service, valid_record):
    # Pass rate regressed from 90% to 75%
    decision = evaluation_service.decide(
        valid_record,
        baseline_value=90.0,
        observed_value=75.0,
        higher_is_better=True,
    )
    assert decision == EvaluationDecision.REVERT


def test_metric_evaluation_severe_regression_returns_escalate(evaluation_service, valid_record):
    # Pass rate dropped sharply from 95% to 40% (delta -55 <= -50)
    decision = evaluation_service.decide(
        valid_record,
        baseline_value=95.0,
        observed_value=40.0,
        higher_is_better=True,
        escalation_delta=50.0,
    )
    assert decision == EvaluationDecision.ESCALATE


def test_lower_is_better_metric_evaluation(evaluation_service, valid_record):
    # Latency reduced from 200ms to 120ms (improvement)
    decision = evaluation_service.decide(
        valid_record,
        baseline_value=200.0,
        observed_value=120.0,
        higher_is_better=False,
    )
    assert decision == EvaluationDecision.KEEP

    # Latency spiked from 200ms to 450ms (regression)
    decision_regress = evaluation_service.decide(
        valid_record,
        baseline_value=200.0,
        observed_value=450.0,
        higher_is_better=False,
    )
    assert decision_regress == EvaluationDecision.REVERT


def test_method_hints_trigger_revert_or_escalate(evaluation_service, valid_record):
    revert_record = valid_record.model_copy(update={"method": "manual_revert_requested"})
    assert evaluation_service.decide(revert_record) == EvaluationDecision.REVERT

    escalate_record = valid_record.model_copy(update={"method": "security_violation_escalate"})
    assert evaluation_service.decide(escalate_record) == EvaluationDecision.ESCALATE
