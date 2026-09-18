"""Mission service coordinating persistence, agent profiles, execution managers, and event fan-out."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID, uuid4

from backend.config import config
from backend.models.mission import (
    CreateMissionRequest,
    CreateTurnRequest,
    MissionSnapshot,
    MissionState,
    OperatorContext,
    PrimaryExecutor,
    ProjectProfile,
    RunReconciliation,
    RunRecord,
    StartupReconciliation,
    TurnRecord,
)
from backend.services.agy_session_manager import AgySessionManager
from backend.services.hermes_adapter import HermesAdapter
from backend.services.mission_store import MissionStore
from backend.services.project_registry import (
    AgentProfileNotFound,
    ProjectNotFound,
    ProjectRegistry,
)

logger = logging.getLogger(__name__)


class MissionService:
    """Coordinates mission persistence, executor lifecycle, and WebSocket fan-out."""

    def __init__(
        self,
        store: Optional[MissionStore] = None,
        registry: Optional[ProjectRegistry] = None,
        agy_manager: Optional[AgySessionManager] = None,
        hermes_adapter: Optional[HermesAdapter] = None,
        manager: Optional[AgySessionManager] = None,
    ) -> None:
        self.store = store or MissionStore()
        self.store.initialize()
        self.registry = registry or ProjectRegistry()
        self.agy_manager = agy_manager or manager or AgySessionManager(store=self.store, registry=self.registry)
        self.manager = self.agy_manager
        self.hermes_adapter = (
            hermes_adapter
            if hermes_adapter is not None
            else (HermesAdapter() if getattr(config, "HERMES_ADAPTER_ENABLED", False) else None)
        )

        # In-memory fan-out: mission_id string -> set of asyncio.Queue
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

        # Hook into store event listener for real-time fan-out
        self.store.register_event_listener(self._on_store_event)

    def reconcile_startup(self) -> Any:
        """Reconcile any incomplete runs across startup/recovery."""
        reconciled = self.agy_manager.reconcile_incomplete_runs()

        class _ReconciliationResult:
            def __init__(self, count: int, items: list[dict]):
                self.reconciled_count = count
                self.items = items

        return _ReconciliationResult(len(reconciled), reconciled)

    def _on_store_event(self, mission_id: str, event: dict) -> None:
        """Called synchronously when store appends an event. Broadcast to queues."""
        m_id = str(mission_id)
        queues = self._subscribers.get(m_id, set()).copy()
        for q in queues:
            try:
                q.put_nowait(event)
            except Exception:
                pass

    def subscribe(self, mission_id: Union[UUID, str]) -> asyncio.Queue:
        """Register a new event queue subscriber for a mission."""
        m_id = str(mission_id)
        q: asyncio.Queue = asyncio.Queue()
        if m_id not in self._subscribers:
            self._subscribers[m_id] = set()
        self._subscribers[m_id].add(q)
        return q

    def unsubscribe(self, mission_id: Union[UUID, str], queue: asyncio.Queue) -> None:
        """Unregister an event queue subscriber."""
        m_id = str(mission_id)
        if m_id in self._subscribers:
            self._subscribers[m_id].discard(queue)
            if not self._subscribers[m_id]:
                del self._subscribers[m_id]

    async def publish_event(self, mission_id: Union[UUID, str], event: dict) -> None:
        """Directly publish an event to all subscribers of a mission."""
        m_id = str(mission_id)
        queues = self._subscribers.get(m_id, set()).copy()
        for q in queues:
            try:
                await q.put(event)
            except Exception:
                pass

    async def create_mission(
        self, request: CreateMissionRequest, operator: OperatorContext
    ) -> dict:
        """Idempotently validate and create a mission, allocating an initial run and starting executor."""
        if isinstance(request, dict):
            request = CreateMissionRequest.model_validate(request)

        # 1. Validate project profile and agent in registry
        profile = self.registry.get(request.project_slug)
        self.registry.require_agent(request.project_slug, request.agent_profile)

        # 2. Check if already created (idempotent replay)
        existing = self.store.check_idempotency(
            operator_id=operator.operator_id,
            operation="create_mission",
            idempotency_key=request.idempotency_key,
        )
        if existing:
            m_id = str(existing.get("mission_id") or existing.get("id"))
            existing_mission = self.store.get_mission(m_id) or existing
            latest_run = self.store.get_latest_run_for_mission(m_id)
            run_id = str(latest_run["id"]) if latest_run else existing.get("run_id")
            correlation_id = str(existing.get("correlation_id") or request.idempotency_key)

            state = (
                existing_mission["state"]
                if isinstance(existing_mission, dict) and "state" in existing_mission
                else "queued"
            )

            return {
                "mission_id": m_id,
                "id": m_id,
                "state": state,
                "status": state,
                "run_id": run_id,
                "correlation_id": correlation_id,
                "next_action": existing.get("next_action", "Awaiting executor slot"),
                "project_slug": request.project_slug,
                "agent_profile": request.agent_profile,
                "title": request.title,
                "objective": request.objective,
                "primary_executor": (
                    request.primary_executor.value
                    if hasattr(request.primary_executor, "value")
                    else str(request.primary_executor)
                ),
                "_is_replay": True,
            }

        # 3. Create mission in store
        snapshot = self.store.create_mission(request, operator)
        m_id = str(snapshot["mission_id"])
        u_m_id = UUID(m_id)

        # Advance state to QUEUED
        try:
            self.store.update_mission_state(u_m_id, MissionState.QUEUED)
        except Exception:
            pass

        # 4. Allocate run in store
        run_id = uuid4()
        executor_str = (
            request.primary_executor.value
            if hasattr(request.primary_executor, "value")
            else str(request.primary_executor)
        )
        self.store.create_run(
            mission_id=u_m_id,
            run_id=run_id,
            executor=executor_str,
            agent_profile=request.agent_profile,
            state=MissionState.QUEUED,
        )

        # Append run.queued event
        self.store.append_event(
            mission_id=u_m_id,
            event_type="run.queued",
            payload={
                "run_id": str(run_id),
                "executor": executor_str,
                "agent_profile": request.agent_profile,
            },
        )

        # 5. If primary_executor == AGY, invoke agy_manager.start_run asynchronously
        if request.primary_executor == PrimaryExecutor.AGY:
            async def _bg_start_run():
                try:
                    await self.agy_manager.start_run(
                        mission_id=u_m_id,
                        run_id=run_id,
                        profile=profile,
                        agent_profile=request.agent_profile,
                    )
                except Exception as exc:
                    logger.error("Failed to start AGY run %s for mission %s: %s", run_id, u_m_id, exc)
                    try:
                        self.store.update_run_state(run_id, MissionState.FAILED)
                        self.store.update_mission_state(u_m_id, MissionState.FAILED)
                        self.store.append_event(
                            mission_id=u_m_id,
                            event_type="run.failed",
                            payload={"run_id": str(run_id), "error": str(exc)},
                        )
                    except Exception:
                        pass

            asyncio.create_task(_bg_start_run())

        correlation_id = str(request.idempotency_key)
        return {
            "mission_id": m_id,
            "id": m_id,
            "state": MissionState.QUEUED.value,
            "status": MissionState.QUEUED.value,
            "run_id": str(run_id),
            "correlation_id": correlation_id,
            "next_action": "Awaiting executor slot",
            "project_slug": request.project_slug,
            "agent_profile": request.agent_profile,
            "title": request.title,
            "objective": request.objective,
            "primary_executor": executor_str,
            "_is_replay": False,
        }

    async def submit_turn(
        self,
        mission_id: Union[UUID, str],
        request: CreateTurnRequest,
        operator: OperatorContext,
    ) -> dict:
        """Enqueue a new turn record and forward to active executor if present."""
        if isinstance(request, dict):
            request = CreateTurnRequest.model_validate(request)

        u_m_id = UUID(str(mission_id))
        mission = self.store.get_mission(u_m_id)
        if not mission:
            raise ValueError(f"Mission '{u_m_id}' not found.")

        # Enqueue turn in store (allocates sequence and appends turn.enqueued event)
        turn_record = self.store.enqueue_turn(u_m_id, request, operator)
        u_turn_id = UUID(str(turn_record["turn_id"]))

        # If run is active in agy_manager, forward turn
        active_run_id: Optional[UUID] = None
        if hasattr(self.agy_manager, "_active_runs"):
            for r_id, active_rec in self.agy_manager._active_runs.items():
                if str(active_rec.mission_id) == str(u_m_id) and getattr(active_rec.process, "returncode", None) is None:
                    active_run_id = r_id
                    break

        if active_run_id is not None:
            try:
                await self.agy_manager.enqueue_turn(active_run_id, u_turn_id, request.message)
            except Exception as exc:
                logger.warning("Failed to forward turn to active AGY run %s: %s", active_run_id, exc)

        return dict(turn_record)

    async def cancel_mission(
        self, mission_id: Union[UUID, str], operator: OperatorContext | None = None
    ) -> dict:
        """Cancel active runs and transition mission to CANCELLED state."""
        u_m_id = UUID(str(mission_id))
        mission = self.store.get_mission(u_m_id)
        if not mission:
            raise ValueError(f"Mission '{u_m_id}' not found.")

        # Find any active runs for this mission in agy_manager
        active_run_ids: list[UUID] = []
        if hasattr(self.agy_manager, "_active_runs"):
            for r_id, active_rec in self.agy_manager._active_runs.items():
                if str(active_rec.mission_id) == str(u_m_id):
                    active_run_ids.append(r_id)

        for r_id in active_run_ids:
            try:
                await self.agy_manager.cancel_run(r_id)
            except Exception as exc:
                logger.warning("Error cancelling active run %s: %s", r_id, exc)

        if not active_run_ids:
            latest_run = self.store.get_latest_run_for_mission(u_m_id)
            if latest_run:
                try:
                    await self.agy_manager.cancel_run(UUID(str(latest_run["id"])))
                except Exception:
                    pass

        # Update mission state to CANCELLED if not already terminal
        current_state = mission["state"]
        if current_state != MissionState.CANCELLED.value:
            try:
                self.store.update_mission_state(u_m_id, MissionState.CANCELLED)
            except Exception as exc:
                logger.warning("Could not transition mission %s to CANCELLED via policy: %s", u_m_id, exc)

        return {"status": "cancelled"}

    def get_events_after(
        self, mission_id: Union[UUID, str], after_sequence: int = 0
    ) -> list[dict]:
        """Read durable events from store ordered by monotonic sequence > after_sequence."""
        events = self.store.get_events(mission_id, after_sequence=after_sequence)
        return [dict(ev) for ev in events]

    def list_missions(self, operator: OperatorContext | None = None) -> list[dict]:
        """Read visible missions from store."""
        return self.store.list_missions(operator)

    def get_mission(self, mission_id: Union[UUID, str]) -> dict | None:
        """Read mission by ID."""
        m = self.store.get_mission(mission_id)
        return dict(m) if m else None

    def reconcile_startup(self) -> StartupReconciliation:
        """Reconciles dangling runs across server restart, marking incomplete runs as INTERRUPTED
        and appending recovery diagnostic events.
        """
        reconciled_list = self.agy_manager.reconcile_incomplete_runs()

        for item in reconciled_list:
            run_id = str(item.run_id) if hasattr(item, "run_id") else str(item.get("run_id"))
            mission_id_str = str(item.mission_id) if hasattr(item, "mission_id") else str(item.get("mission_id"))
            prev_state = item.previous_state if hasattr(item, "previous_state") else item.get("previous_state")

            if mission_id_str:
                try:
                    self.store.append_event(
                        mission_id=UUID(mission_id_str),
                        event_type="run.interrupted",
                        payload={
                            "run_id": run_id,
                            "reason": "Process interrupted across service restart",
                            "previous_state": str(prev_state),
                        },
                    )
                except Exception as exc:
                    logger.warning(
                        f"Failed to record recovery event for mission {mission_id_str}: {exc}"
                    )

        reconciled_models = [
            item if isinstance(item, RunReconciliation) else RunReconciliation(**item)
            for item in reconciled_list
        ]

        return StartupReconciliation(
            reconciled_runs=reconciled_models,
            reconciled_count=len(reconciled_models),
            timestamp=datetime.now(timezone.utc),
        )



# Module singleton management
_default_mission_service: Optional[MissionService] = None


def get_mission_service() -> MissionService:
    """Dependency provider returning singleton MissionService."""
    global _default_mission_service
    if _default_mission_service is None:
        store = MissionStore()
        store.initialize()
        registry = ProjectRegistry()
        agy_manager = AgySessionManager(store=store, registry=registry)
        hermes_adapter = (
            HermesAdapter() if getattr(config, "HERMES_ADAPTER_ENABLED", False) else None
        )
        _default_mission_service = MissionService(
            store=store,
            registry=registry,
            agy_manager=agy_manager,
            hermes_adapter=hermes_adapter,
        )
    return _default_mission_service


def set_mission_service(service: Optional[MissionService]) -> None:
    """Set or reset singleton MissionService (useful for unit testing)."""
    global _default_mission_service
    _default_mission_service = service
