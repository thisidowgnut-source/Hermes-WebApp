"""AGY session manager for running, managing, and recovering AGY subprocesses."""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union
from uuid import UUID

from backend.models.mission import MissionState, ProjectProfile, RunRecord, RunReconciliation
from backend.services.agy_protocol import parse_agy_stream_line
from backend.services.mission_store import MissionStore
from backend.services.project_registry import ProjectRegistry

logger = logging.getLogger(__name__)


class ActiveRunRecord:
    """Internal tracking record for an actively managed AGY subprocess run."""

    def __init__(
        self,
        run_id: UUID,
        mission_id: UUID,
        profile: ProjectProfile,
        agent_profile: str,
        process: asyncio.subprocess.Process,
    ) -> None:
        self.run_id = run_id
        self.mission_id = mission_id
        self.profile = profile
        self.agent_profile = agent_profile
        self.process = process
        self.queue: asyncio.Queue[tuple[UUID, str]] = asyncio.Queue()
        self.provider_conversation_id: Optional[str] = None

        self.stdout_task: Optional[asyncio.Task] = None
        self.stderr_task: Optional[asyncio.Task] = None
        self.runner_task: Optional[asyncio.Task] = None

        self.is_cancelled: bool = False
        self.termination_called: bool = False
        self.termination_lock: asyncio.Lock = asyncio.Lock()

        self.last_result_received: bool = False
        self.active_turn_id: Optional[UUID] = None
        self.turn_in_flight: bool = False

        self.current_turn_event: asyncio.Event = asyncio.Event()
        self.idle_event: asyncio.Event = asyncio.Event()
        self.process_done_event: asyncio.Event = asyncio.Event()

        # Initially idle
        self.idle_event.set()


class AgySessionManager:
    """Manages the lifecycle of project-scoped AGY executor processes with serialized input."""

    def __init__(self, store: MissionStore, registry: ProjectRegistry) -> None:
        self.store = store
        self.registry = registry
        self._active_runs: dict[UUID, ActiveRunRecord] = {}

    def _build_argv(
        self,
        profile: ProjectProfile,
        run_id: Union[UUID, Any],
        agent_profile: Optional[str] = None,
        executable_override: Optional[str] = None,
    ) -> list[str]:
        """Construct the typed argv list for starting an AGY subprocess."""
        exe = executable_override or "agy"
        argv = [exe]

        if profile.agy_project_id is not None:
            argv.extend(["--project", str(profile.agy_project_id)])

        agent = agent_profile
        if agent is None and hasattr(run_id, "agent_profile"):
            agent = run_id.agent_profile
        if agent is None:
            agent = "default"

        argv.extend([
            "--agent",
            str(agent),
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
        ])
        return argv

    async def start_run(
        self,
        mission_id: Union[UUID, str, None] = None,
        run_id: Union[UUID, str, None] = None,
        profile: Optional[ProjectProfile] = None,
        agent_profile: Optional[str] = None,
        executable_override: Optional[str] = None,
    ) -> None:
        """Spawn and register an AGY subprocess for the given mission and run."""
        # Support start_run(run_id) single-argument invocation
        if run_id is None and mission_id is not None:
            actual_run_id = UUID(str(mission_id))
            run_rec = self.store.get_run(actual_run_id)
            if not run_rec:
                raise ValueError(f"Run '{actual_run_id}' not found in store.")
            actual_mission_id = UUID(str(run_rec["mission_id"]))
            mission = self.store.get_mission(actual_mission_id)
            if not mission:
                raise ValueError(f"Mission '{actual_mission_id}' not found in store.")
            actual_profile = self.registry.get(mission["project_slug"])
            actual_agent_profile = run_rec["agent_profile"]
        else:
            if mission_id is None or run_id is None:
                raise ValueError("Both mission_id and run_id are required to start a run.")
            actual_mission_id = UUID(str(mission_id))
            actual_run_id = UUID(str(run_id))
            actual_profile = profile
            actual_agent_profile = agent_profile or "default"
            if actual_profile is None:
                mission = self.store.get_mission(actual_mission_id)
                if mission:
                    actual_profile = self.registry.get(mission["project_slug"])
                else:
                    raise ValueError(f"Profile not provided and mission '{actual_mission_id}' not found.")

        # Check if run is already active
        existing_active = self._active_runs.get(actual_run_id)
        if existing_active and existing_active.process.returncode is None:
            raise ValueError(f"Run '{actual_run_id}' is already active.")

        # Ensure run is in store and transitioned to STARTING
        stored_run = self.store.get_run(actual_run_id)
        if not stored_run:
            self.store.create_run(
                mission_id=actual_mission_id,
                run_id=actual_run_id,
                executor="agy",
                agent_profile=actual_agent_profile,
                state=MissionState.STARTING,
            )
        else:
            self.store.update_run_state(actual_run_id, MissionState.STARTING)

        argv = self._build_argv(
            actual_profile,
            actual_run_id,
            actual_agent_profile,
            executable_override=executable_override,
        )

        spawn_kwargs: dict[str, Any] = {
            "stdin": asyncio.subprocess.PIPE,
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "cwd": str(actual_profile.workspace_path),
            "shell": False,
        }

        if sys.platform == "win32":
            import subprocess
            spawn_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        process = await asyncio.create_subprocess_exec(*argv, **spawn_kwargs)

        active_run = ActiveRunRecord(
            run_id=actual_run_id,
            mission_id=actual_mission_id,
            profile=actual_profile,
            agent_profile=actual_agent_profile,
            process=process,
        )
        self._active_runs[actual_run_id] = active_run

        # Transition run state to RUNNING
        self.store.update_run_state(actual_run_id, MissionState.RUNNING)
        self.store.append_event(
            actual_mission_id,
            "run.started",
            {"run_id": str(actual_run_id), "agent_profile": actual_agent_profile},
        )

        active_run.stdout_task = asyncio.create_task(self._read_stdout(actual_run_id))
        active_run.stderr_task = asyncio.create_task(self._read_stderr(actual_run_id))
        active_run.runner_task = asyncio.create_task(self._run_input_loop(actual_run_id))

    async def enqueue_turn(
        self, run_id: Union[UUID, str], turn_id: Union[UUID, str], message: str
    ) -> None:
        """Enqueue a user message turn for serialized execution by the active run."""
        u_run_id = UUID(str(run_id))
        u_turn_id = UUID(str(turn_id))

        active_run = self._active_runs.get(u_run_id)
        if not active_run:
            raise ValueError(f"Run '{u_run_id}' is not active.")

        active_run.idle_event.clear()
        await active_run.queue.put((u_turn_id, message))

    async def wait_until_idle(self, run_id: Union[UUID, str], timeout: float = 5.0) -> None:
        """Wait until all currently queued turns for the run have been consumed."""
        u_run_id = UUID(str(run_id))
        active_run = self._active_runs.get(u_run_id)
        if not active_run:
            return

        if active_run.queue.empty() and not active_run.turn_in_flight:
            return

        async def _check_idle():
            while not active_run.queue.empty() or active_run.turn_in_flight:
                await asyncio.sleep(0.02)

        await asyncio.wait_for(_check_idle(), timeout=timeout)

    async def wait_for_terminal(self, run_id: Union[UUID, str], timeout: float = 5.0) -> None:
        """Wait until the subprocess for the run completes execution."""
        u_run_id = UUID(str(run_id))
        active_run = self._active_runs.get(u_run_id)
        if not active_run:
            return

        if active_run.process_done_event.is_set():
            return

        await asyncio.wait_for(active_run.process_done_event.wait(), timeout=timeout)

    async def cancel_run(self, run_id: Union[UUID, str]) -> None:
        """Idempotently cancel an active run and terminate its process tree."""
        u_run_id = UUID(str(run_id))
        active_run = self._active_runs.get(u_run_id)
        if not active_run:
            stored = self.store.get_run(u_run_id)
            if stored and stored.state not in (
                MissionState.CANCELLED,
                MissionState.SUCCEEDED,
                MissionState.FAILED,
            ):
                self.store.update_run_state(u_run_id, MissionState.CANCELLED)
            return

        async with active_run.termination_lock:
            if active_run.termination_called:
                return
            active_run.termination_called = True
            active_run.is_cancelled = True

            # Gracefully close stdin
            if active_run.process.stdin and not active_run.process.stdin.is_closing():
                try:
                    active_run.process.stdin.close()
                except Exception:
                    pass

            # Terminate or kill process if alive
            if active_run.process.returncode is None:
                try:
                    active_run.process.terminate()
                except ProcessLookupError:
                    pass
                except Exception as e:
                    logger.warning("Failed to terminate process for run %s: %s", u_run_id, e)
                    try:
                        active_run.process.kill()
                    except Exception:
                        pass

            if active_run.runner_task and not active_run.runner_task.done():
                active_run.runner_task.cancel()

            self.store.update_run_state(u_run_id, MissionState.CANCELLED)
            try:
                self.store.append_event(
                    active_run.mission_id,
                    "run.cancelled",
                    {"run_id": str(u_run_id)},
                )
            except Exception:
                pass

            active_run.current_turn_event.set()
            active_run.idle_event.set()
            active_run.process_done_event.set()

    def reconcile_incomplete_runs(self) -> list[RunReconciliation]:
        """Detect dangling STARTING or RUNNING runs and classify them as INTERRUPTED."""
        incomplete_runs = self.store.get_incomplete_runs()
        reconciled: list[RunReconciliation] = []

        for run in incomplete_runs:
            r_id_str = str(run["id"])
            try:
                u_run_id = UUID(r_id_str)
            except Exception:
                u_run_id = r_id_str

            active_run = self._active_runs.get(u_run_id)
            if active_run and active_run.process.returncode is None:
                # Still legitimately alive
                continue

            prev_state = (
                run["state"].value if isinstance(run["state"], MissionState) else str(run["state"])
            )
            self.store.update_run_state(u_run_id, MissionState.INTERRUPTED)

            entry = RunReconciliation(
                run_id=r_id_str,
                mission_id=str(run["mission_id"]),
                previous_state=prev_state,
                new_state=MissionState.INTERRUPTED.value,
                reason="Process not active or cannot be proven alive during reconciliation",
            )
            reconciled.append(entry)

        return reconciled

    async def _run_input_loop(self, run_id: UUID) -> None:
        """Worker task consuming turns from the run's queue and feeding them sequentially to stdin."""
        active_run = self._active_runs.get(run_id)
        if not active_run:
            return

        try:
            while True:
                turn_id, message = await active_run.queue.get()
                active_run.active_turn_id = turn_id
                active_run.turn_in_flight = True
                active_run.current_turn_event.clear()

                if active_run.process.returncode is not None or active_run.is_cancelled:
                    active_run.queue.task_done()
                    break

                ndjson_line = json.dumps({"turn_id": str(turn_id), "message": message}) + "\n"
                try:
                    if active_run.process.stdin and not active_run.process.stdin.is_closing():
                        active_run.process.stdin.write(ndjson_line.encode("utf-8"))
                        await active_run.process.stdin.drain()
                except (BrokenPipeError, ConnectionResetError, OSError) as e:
                    logger.warning("Cannot write turn to stdin for run %s: %s", run_id, e)
                    active_run.queue.task_done()
                    break

                # Wait for result of this turn before feeding the next turn
                await active_run.current_turn_event.wait()
                active_run.active_turn_id = None
                active_run.turn_in_flight = False
                active_run.queue.task_done()

                if active_run.queue.empty():
                    active_run.idle_event.set()

        except asyncio.CancelledError:
            pass
        finally:
            active_run.turn_in_flight = False
            active_run.idle_event.set()

    async def _read_stdout(self, run_id: UUID) -> None:
        """Worker task reading, parsing, and normalizing AGY NDJSON lines from stdout."""
        active_run = self._active_runs.get(run_id)
        if not active_run:
            return

        proc = active_run.process
        try:
            while True:
                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break

                line_str = line_bytes.decode("utf-8", errors="replace")
                now = datetime.now(timezone.utc)
                try:
                    event = parse_agy_stream_line(line_str, now)
                except Exception as exc:
                    logger.warning("Error parsing AGY stream line for run %s: %s", run_id, exc)
                    continue

                if event is None:
                    continue

                if event.event_type == "agy.init":
                    if event.provider_conversation_id:
                        active_run.provider_conversation_id = event.provider_conversation_id
                        self.store.set_run_provider_conversation_id(
                            run_id, event.provider_conversation_id
                        )
                    self.store.append_event(
                        active_run.mission_id,
                        "run.initialized",
                        {"provider_conversation_id": event.provider_conversation_id},
                    )

                elif event.event_type == "agy.step":
                    self.store.append_event(
                        active_run.mission_id,
                        "run.step",
                        {
                            "text_delta": event.text_delta,
                            "state": event.state,
                            "tool_name": event.tool_name,
                        },
                    )

                elif event.event_type == "agy.result":
                    active_run.last_result_received = True
                    if event.provider_conversation_id:
                        active_run.provider_conversation_id = event.provider_conversation_id
                        self.store.set_run_provider_conversation_id(
                            run_id, event.provider_conversation_id
                        )

                    if event.result_status == "SUCCESS":
                        self.store.update_run_state(run_id, MissionState.SUCCEEDED)
                        self.store.append_event(
                            active_run.mission_id,
                            "run.succeeded",
                            {
                                "result_status": "SUCCESS",
                                "response": event.text_delta,
                                "usage": event.usage.model_dump() if event.usage else None,
                            },
                        )
                    else:
                        self.store.update_run_state(run_id, MissionState.FAILED)
                        self.store.append_event(
                            active_run.mission_id,
                            "run.failed",
                            {
                                "result_status": event.result_status,
                                "response": event.text_delta,
                                "usage": event.usage.model_dump() if event.usage else None,
                            },
                        )

                    # Turn is complete!
                    active_run.current_turn_event.set()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception("Unexpected error in stdout reader for run %s: %s", run_id, e)
        finally:
            await proc.wait()
            # If process terminated without receiving a result, transition to INTERRUPTED
            if not active_run.is_cancelled:
                if not active_run.last_result_received:
                    self.store.update_run_state(run_id, MissionState.INTERRUPTED)
                    try:
                        self.store.append_event(
                            active_run.mission_id,
                            "run.interrupted",
                            {"returncode": proc.returncode},
                        )
                    except Exception:
                        pass

            if active_run.runner_task and not active_run.runner_task.done():
                active_run.runner_task.cancel()
            if active_run.stderr_task and not active_run.stderr_task.done():
                active_run.stderr_task.cancel()

            active_run.current_turn_event.set()
            active_run.idle_event.set()
            active_run.process_done_event.set()

    async def _read_stderr(self, run_id: UUID) -> None:
        """Worker task reading stderr diagnostics and storing them as events."""
        active_run = self._active_runs.get(run_id)
        if not active_run:
            return

        proc = active_run.process
        try:
            while True:
                line_bytes = await proc.stderr.readline()
                if not line_bytes:
                    break
                line_str = line_bytes.decode("utf-8", errors="replace").strip()
                if line_str:
                    try:
                        self.store.append_event(
                            active_run.mission_id,
                            "run.stderr",
                            {"stderr": line_str},
                        )
                    except Exception:
                        pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("Error reading stderr for run %s: %s", run_id, e)
