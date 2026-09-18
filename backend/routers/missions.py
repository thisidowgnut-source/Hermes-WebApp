"""API routes for mission creation, inspection, turn submission, and event streams."""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from backend.models.mission import (
    CreateMissionRequest,
    CreateTurnRequest,
    OperatorContext,
)
from backend.services.capability_registry import CapabilityRegistry
from backend.services.mission_service import (
    MissionService,
    get_mission_service,
)
from backend.services.project_registry import (
    AgentProfileNotFound,
    ProjectNotFound,
)
from backend.services.session_auth import (
    rate_limiter,
    require_csrf,
    require_operator,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["missions"])


@router.post("/missions", response_model=None)
async def create_mission(
    request: CreateMissionRequest,
    operator: OperatorContext = Depends(require_operator),
    _: None = Depends(require_csrf),
    service: MissionService = Depends(get_mission_service),
) -> Response:
    """Create a new mission idempotently.
    
    Returns 201 Created on first invocation.
    Returns 200 OK on idempotent replay with the same operator and idempotency_key.
    """
    rate_limiter.check("mission_create", operator_id=operator.operator_id)

    try:
        profile = service.registry.get(request.project_slug)
    except ProjectNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    try:
        service.registry.require_agent(request.project_slug, request.agent_profile)
    except AgentProfileNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    result = await service.create_mission(request, operator)
    is_replay = result.pop("_is_replay", False)

    status_code = 200 if is_replay else 201
    return JSONResponse(status_code=status_code, content=result)


@router.get("/missions", response_model=List[dict])
def list_missions(
    operator: OperatorContext = Depends(require_operator),
    service: MissionService = Depends(get_mission_service),
) -> list[dict]:
    """List all missions visible to the operator."""
    return service.list_missions(operator)


@router.get("/missions/{mission_id}")
def get_mission(
    mission_id: str,
    operator: OperatorContext = Depends(require_operator),
    service: MissionService = Depends(get_mission_service),
) -> dict:
    """Get mission snapshot by ID."""
    mission = service.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found.")
    return mission


@router.post("/missions/{mission_id}/turns", response_model=None)
async def submit_turn(
    mission_id: str,
    request: CreateTurnRequest,
    operator: OperatorContext = Depends(require_operator),
    _: None = Depends(require_csrf),
    service: MissionService = Depends(get_mission_service),
) -> Response:
    """Submit a new turn message for the mission."""
    rate_limiter.check("turn_create", operator_id=operator.operator_id)

    mission = service.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found.")

    try:
        turn_record = await service.submit_turn(mission_id, request, operator)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return JSONResponse(status_code=202, content=turn_record)


@router.post("/missions/{mission_id}/cancel")
async def cancel_mission(
    mission_id: str,
    operator: OperatorContext = Depends(require_operator),
    _: None = Depends(require_csrf),
    service: MissionService = Depends(get_mission_service),
) -> dict:
    """Cancel an active mission and its executor runs."""
    mission = service.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found.")

    try:
        return await service.cancel_mission(mission_id, operator)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/missions/{mission_id}/events", response_model=List[dict])
def get_mission_events(
    mission_id: str,
    after_sequence: int = Query(default=0, ge=0),
    operator: OperatorContext = Depends(require_operator),
    service: MissionService = Depends(get_mission_service),
) -> list[dict]:
    """Retrieve durable events for a mission after a given monotonic sequence."""
    mission = service.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found.")

    return service.get_events_after(mission_id, after_sequence=after_sequence)


@router.get("/capabilities", response_model=List[dict])
def list_capabilities() -> list[dict]:
    """List available capabilities from orchestration defaults or registry."""
    try:
        registry = CapabilityRegistry()
        return [
            {"name": name, **details}
            for name, details in registry.capabilities.items()
        ]
    except Exception as exc:
        logger.warning("Could not read capability registry: %s", exc)
        return [
            {"name": "plan", "id": "cap-plan"},
            {"name": "verify", "id": "cap-verify"},
            {"name": "kanban_sync", "id": "cap-kanban-sync"},
        ]
