"""Tests for AgySessionManager subprocess lifecycle, serialized input, and recovery."""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
import pytest

from backend.models.mission import (
    AgentProfile,
    ApprovalPolicy,
    MissionState,
    ProjectProfile,
    RunRecord,
)
from backend.services.agy_session_manager import AgySessionManager
from backend.services.mission_store import MissionStore
from backend.services.project_registry import ProjectRegistry

UUID1 = UUID("11111111-1111-1111-1111-111111111111")
UUID2 = UUID("22222222-2222-2222-2222-222222222222")


class FakeStdin:
    """Mock StreamWriter for subprocess stdin."""

    def __init__(self, fake_proc: "FakeProcess") -> None:
        self.fake_proc = fake_proc
        self._closed = False

    def write(self, data: bytes) -> None:
        self.fake_proc._on_stdin_write(data)

    async def drain(self) -> None:
        await self.fake_proc._on_stdin_drain()

    def close(self) -> None:
        self._closed = True

    def is_closing(self) -> bool:
        return self._closed


class FakeProcess:
    """Mock asyncio.subprocess.Process for unit tests."""

    def __init__(
        self,
        fixture_lines: list[str] | None = None,
        auto_respond_turns: bool = False,
    ) -> None:
        self.received_messages: list[str] = []
        self.received_turns: list[dict] = []
        self.termination_calls = 0
        self.kill_calls = 0
        self.returncode: int | None = None
        self._fixture_lines = fixture_lines or []
        self._auto_respond_turns = auto_respond_turns

        self.stdout = asyncio.StreamReader()
        self.stderr = asyncio.StreamReader()
        self.stdin = FakeStdin(self)
        self._exit_event = asyncio.Event()

    def _on_stdin_write(self, data: bytes) -> None:
        text = data.decode("utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    payload = json.loads(line)
                    self.received_turns.append(payload)
                    if "message" in payload:
                        self.received_messages.append(payload["message"])
                except Exception:
                    self.received_messages.append(line)

    async def _on_stdin_drain(self) -> None:
        if self._auto_respond_turns and self.received_turns:
            last_turn = self.received_turns[-1]
            turn_id = last_turn.get("turn_id", "0")
            msg = last_turn.get("message", "")
            step_line = json.dumps({
                "event": "step_update",
                "step_update": {
                    "conversation_id": "test-conv-id",
                    "step_index": len(self.received_turns),
                    "state": "ACTIVE",
                    "text_delta": f"Processing {msg}",
                },
            })
            result_line = json.dumps({
                "event": "result",
                "result": {
                    "conversation_id": "test-conv-id",
                    "status": "SUCCESS",
                    "response": f"Processed {msg}",
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "thinking_tokens": 0,
                        "cache_read_tokens": 0,
                        "total_tokens": 15,
                    },
                },
            })
            self.feed_stdout(step_line)
            self.feed_stdout(result_line)
        await asyncio.sleep(0.01)

    def feed_stdout(self, line: str) -> None:
        self.stdout.feed_data((line + "\n").encode("utf-8"))

    def feed_stderr(self, line: str) -> None:
        self.stderr.feed_data((line + "\n").encode("utf-8"))

    def exit_without_result(self, code: int = 0) -> None:
        self.returncode = code
        self.stdout.feed_eof()
        self.stderr.feed_eof()
        self._exit_event.set()

    def terminate(self) -> None:
        self.termination_calls += 1
        self.returncode = -15
        self.stdout.feed_eof()
        self.stderr.feed_eof()
        self._exit_event.set()

    def kill(self) -> None:
        self.kill_calls += 1
        self.returncode = -9
        self.stdout.feed_eof()
        self.stderr.feed_eof()
        self._exit_event.set()

    async def wait(self) -> int:
        if self.returncode is None:
            await self._exit_event.wait()
        return self.returncode or 0


@pytest.fixture
def store(tmp_path):
    s = MissionStore(db_path=tmp_path / "test_mission.db")
    s.initialize()
    return s


@pytest.fixture
def registry(tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    doh_dir = tmp_path / "Doh-Nut"
    doh_dir.mkdir()
    agents_dir = doh_dir / ".gemini" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "dohnut-orchestrator.md").write_text("# Doh-Nut Orchestrator", encoding="utf-8")
    (doh_dir / "brand.md").write_text("# Brand Truth", encoding="utf-8")
    profile_data = {
        "slug": "doh-nut",
        "display_name": "Doh-Nut",
        "workspace_path": str(doh_dir),
        "agy_project_id": "agy-test-proj",
        "brand_truth_path": str(doh_dir / "brand.md"),
        "approval_policy": {
            "social_requires_human_confirmation": True,
            "approval_ttl_seconds": 900,
        },
        "agents": {
            "dohnut-orchestrator": {
                "display_name": "Doh-Nut Orchestrator",
                "execution": "agy",
            }
        },
    }
    (projects_dir / "doh-nut.json").write_text(json.dumps(profile_data), encoding="utf-8")
    return ProjectRegistry(projects_dir=projects_dir)


@pytest.fixture
def manager(store, registry):
    return AgySessionManager(store=store, registry=registry)


@pytest.fixture
def sample_profile(registry):
    return registry.get("doh-nut")


async def make_running_run(manager, store, sample_profile, monkeypatch):
    proc = FakeProcess(auto_respond_turns=True)

    async def _mock_exec(*args, **kwargs):
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _mock_exec)

    mission_id = uuid4()
    run_id = uuid4()
    await manager.start_run(
        mission_id=mission_id,
        run_id=run_id,
        profile=sample_profile,
        agent_profile="dohnut-orchestrator",
    )
    run = store.get_run(run_id)
    run._test_process = proc
    return run


@pytest.mark.asyncio
async def test_turns_are_serialized_for_one_run(manager, store, sample_profile, monkeypatch):
    running_run = await make_running_run(manager, store, sample_profile, monkeypatch)
    fake_process = running_run._test_process
    await manager.enqueue_turn(running_run.id, UUID1, "first")
    await manager.enqueue_turn(running_run.id, UUID2, "second")
    await manager.wait_until_idle(running_run.id)
    assert fake_process.received_messages == ["first", "second"]
    await manager.cancel_run(running_run.id)


@pytest.mark.asyncio
async def test_exit_zero_without_result_becomes_interrupted(manager, store, sample_profile, monkeypatch):
    fake_process = FakeProcess(auto_respond_turns=False)

    async def _mock_exec(*args, **kwargs):
        return fake_process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _mock_exec)

    mission_id = uuid4()
    run_id = uuid4()
    await manager.start_run(
        mission_id=mission_id,
        run_id=run_id,
        profile=sample_profile,
        agent_profile="dohnut-orchestrator",
    )

    fake_process.exit_without_result(0)
    await manager.wait_for_terminal(run_id)
    assert store.get_run(run_id).state == MissionState.INTERRUPTED


@pytest.mark.asyncio
async def test_cancel_is_idempotent_and_kills_process_tree_once(manager, store, sample_profile, monkeypatch):
    running_run = await make_running_run(manager, store, sample_profile, monkeypatch)
    fake_process = running_run._test_process
    await manager.cancel_run(running_run.id)
    await manager.cancel_run(running_run.id)
    assert fake_process.termination_calls == 1


def test_recovery_reconcile_incomplete_runs_marks_dangling_as_interrupted(manager, store):
    mission_id = uuid4()
    run_id1 = uuid4()
    run_id2 = uuid4()

    # Create runs directly in store that are not active in memory
    store.create_run(
        mission_id=mission_id,
        run_id=run_id1,
        executor="agy",
        agent_profile="dohnut-orchestrator",
        state=MissionState.RUNNING,
    )
    store.create_run(
        mission_id=mission_id,
        run_id=run_id2,
        executor="agy",
        agent_profile="dohnut-orchestrator",
        state=MissionState.STARTING,
    )

    reconciled = manager.reconcile_incomplete_runs()
    assert len(reconciled) == 2
    assert {r["run_id"] for r in reconciled} == {str(run_id1), str(run_id2)}
    assert all(r["new_state"] == MissionState.INTERRUPTED.value for r in reconciled)

    assert store.get_run(run_id1).state == MissionState.INTERRUPTED
    assert store.get_run(run_id2).state == MissionState.INTERRUPTED


def test_build_argv_with_and_without_agy_project_id(manager, tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    profile_with_proj = ProjectProfile(
        slug="doh-nut",
        workspace_path=ws,
        agy_project_id="proj-12345",
        brand_truth_path=ws / "brand.md",
        agents={"dohnut-orchestrator": AgentProfile(display_name="Orchestrator")},
        approval_policy=ApprovalPolicy(),
    )
    argv1 = manager._build_argv(
        profile_with_proj, UUID("11111111-1111-1111-1111-111111111111"), "dohnut-orchestrator"
    )
    assert argv1 == [
        "agy",
        "--project",
        "proj-12345",
        "--agent",
        "dohnut-orchestrator",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
    ]

    profile_without_proj = ProjectProfile(
        slug="doh-nut",
        workspace_path=ws,
        agy_project_id=None,
        brand_truth_path=ws / "brand.md",
        agents={"dohnut-orchestrator": AgentProfile(display_name="Orchestrator")},
        approval_policy=ApprovalPolicy(),
    )
    argv2 = manager._build_argv(
        profile_without_proj, UUID("11111111-1111-1111-1111-111111111111"), "dohnut-orchestrator"
    )
    assert argv2 == [
        "agy",
        "--agent",
        "dohnut-orchestrator",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
    ]


@pytest.mark.asyncio
async def test_cannot_start_already_active_run(manager, store, sample_profile, monkeypatch):
    running_run = await make_running_run(manager, store, sample_profile, monkeypatch)
    with pytest.raises(ValueError, match="already active"):
        await manager.start_run(
            mission_id=running_run.mission_id,
            run_id=running_run.id,
            profile=sample_profile,
            agent_profile="dohnut-orchestrator",
        )
    await manager.cancel_run(running_run.id)


@pytest.mark.asyncio
async def test_stream_success_fixture_execution(manager, store, sample_profile, monkeypatch):
    fixture_path = Path(__file__).parent / "fixtures" / "agy" / "stream_success.ndjson"
    lines = [l.strip() for l in fixture_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    fake_proc = FakeProcess()

    async def _mock_exec(*args, **kwargs):
        # Asynchronously feed fixture lines to stdout
        async def _feed():
            await asyncio.sleep(0.01)
            for l in lines:
                fake_proc.feed_stdout(l)
                await asyncio.sleep(0.01)
            fake_proc.exit_without_result(0)

        asyncio.create_task(_feed())
        return fake_proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _mock_exec)

    mission_id = uuid4()
    run_id = uuid4()
    await manager.start_run(
        mission_id=mission_id,
        run_id=run_id,
        profile=sample_profile,
        agent_profile="dohnut-orchestrator",
    )

    await manager.wait_for_terminal(run_id)

    run = store.get_run(run_id)
    assert run.state == MissionState.SUCCEEDED
    assert run.provider_conversation_id == "11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_stream_error_fixture_execution(manager, store, sample_profile, monkeypatch):
    fixture_path = Path(__file__).parent / "fixtures" / "agy" / "stream_error.ndjson"
    lines = [l.strip() for l in fixture_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    fake_proc = FakeProcess()

    async def _mock_exec(*args, **kwargs):
        async def _feed():
            await asyncio.sleep(0.01)
            for l in lines:
                fake_proc.feed_stdout(l)
                await asyncio.sleep(0.01)
            fake_proc.exit_without_result(1)

        asyncio.create_task(_feed())
        return fake_proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _mock_exec)

    mission_id = uuid4()
    run_id = uuid4()
    await manager.start_run(
        mission_id=mission_id,
        run_id=run_id,
        profile=sample_profile,
        agent_profile="dohnut-orchestrator",
    )

    await manager.wait_for_terminal(run_id)

    run = store.get_run(run_id)
    assert run.state == MissionState.FAILED
    assert run.provider_conversation_id == "22222222-2222-2222-2222-222222222222"
