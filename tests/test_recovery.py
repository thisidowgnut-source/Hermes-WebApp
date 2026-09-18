"""Tests for restart recovery, uncompleted run reconciliation, and cost recording."""
from uuid import uuid4
import pytest

from backend.models.mission import (
    MissionState,
    StartupReconciliation,
    UsageRecord,
)
from backend.services.agy_session_manager import AgySessionManager
from backend.services.mission_service import MissionService
from backend.services.mission_store import MissionStore, record_cost
from backend.services.project_registry import ProjectRegistry


@pytest.fixture
def store(tmp_path):
    s = MissionStore(db_path=tmp_path / "recovery_test.db")
    s.initialize()
    return s


@pytest.fixture
def registry(tmp_path):
    p_dir = tmp_path / "projects"
    p_dir.mkdir()
    doh_dir = tmp_path / "Doh-Nut"
    doh_dir.mkdir()
    agents_dir = doh_dir / ".gemini" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "dohnut-orchestrator.md").write_text("# Orchestrator", encoding="utf-8")
    (doh_dir / "brand.md").write_text("# Brand", encoding="utf-8")

    import json
    data = {
        "slug": "doh-nut",
        "display_name": "Doh-Nut",
        "workspace_path": str(doh_dir),
        "brand_truth_path": str(doh_dir / "brand.md"),
        "approval_policy": {
            "social_requires_human_confirmation": True,
            "approval_ttl_seconds": 900,
        },
        "agents": {
            "dohnut-orchestrator": {
                "display_name": "Orchestrator",
                "execution": "agy",
            }
        },
    }
    (p_dir / "doh-nut.json").write_text(json.dumps(data), encoding="utf-8")
    return ProjectRegistry(projects_dir=p_dir)


@pytest.fixture
def manager(store, registry):
    return AgySessionManager(store, registry)


@pytest.fixture
def mission_service(store, registry, manager):
    return MissionService(store=store, registry=registry, manager=manager)


def test_restart_without_terminal_result_is_interrupted(store, manager):
    """Uncompleted running run must be classified as INTERRUPTED during reconciliation."""
    run = store.create_running_run_without_result()
    assert run.state == MissionState.RUNNING

    reconciliation = manager.reconcile_incomplete_runs()
    assert len(reconciliation) == 1
    assert reconciliation[0].new_state == MissionState.INTERRUPTED
    assert reconciliation[0]["new_state"] == MissionState.INTERRUPTED.value
    assert reconciliation[0].run_id == str(run.id)

    updated_run = store.get_run(run.id)
    assert updated_run is not None
    assert updated_run.state == MissionState.INTERRUPTED


def test_mission_service_reconcile_startup_emits_recovery_events(store, mission_service):
    """Startup reconciliation updates store state and appends recovery diagnostic events."""
    m_id = uuid4()
    run1 = store.create_running_run_without_result(mission_id=m_id)
    run2 = store.create_run(
        mission_id=m_id,
        run_id=uuid4(),
        executor="agy",
        agent_profile="dohnut-orchestrator",
        state=MissionState.STARTING,
    )

    reconciliation = mission_service.reconcile_startup()
    assert isinstance(reconciliation, StartupReconciliation)
    assert reconciliation.reconciled_count == 2
    assert len(reconciliation.reconciled_runs) == 2

    # Check database state
    assert store.get_run(run1.id).state == MissionState.INTERRUPTED
    assert store.get_run(run2["id"]).state == MissionState.INTERRUPTED

    # Check diagnostic recovery events in mission_events
    events = store.get_events(m_id, after_sequence=0)
    interrupted_events = [e for e in events if e.get("event_type") == "run.interrupted"]
    assert len(interrupted_events) == 2


def test_record_cost_persists_usage_and_computes_cost(store):
    """Token usage must be persisted with accurate non-zero cost calculation."""
    run_id = uuid4()
    usage = UsageRecord(
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
    )

    cost_rec = store.record_cost(run_id=run_id, usage=usage, duration_seconds=2.4)
    assert cost_rec.run_id == str(run_id)
    assert cost_rec.input_tokens == 1000
    assert cost_rec.output_tokens == 500
    assert cost_rec.total_tokens == 1500
    assert cost_rec.cost_usd > 0.0
    assert cost_rec.duration_seconds == 2.4

    # Top-level helper function
    cost_rec2 = record_cost(run_id=run_id, usage=None, store=store)
    assert cost_rec2.input_tokens == 0
    assert cost_rec2.output_tokens == 0
    assert cost_rec2.cost_usd == 0.0
