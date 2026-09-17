"""Authenticated WebSocket endpoint for mission event streaming with cursor replay."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from backend.services.mission_service import get_mission_service
from backend.services.session_auth import session_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["missions_ws"])


@router.websocket("/ws/missions/{mission_id}")
async def mission_events_ws(websocket: WebSocket, mission_id: str) -> None:
    """Authenticated WebSocket stream for mission events with historical replay.
    
    1. Accepts connection.
    2. Awaits initial JSON payload: {"ticket": "<ticket>", "after_sequence": <int>}.
    3. Validates ticket via session_auth_service. If invalid, closes with 4401.
    4. Replays durable events sequence > after_sequence.
    5. Subscribes to live mission events and streams to client.
    6. Handles disconnects cleanly.
    """
    await websocket.accept()

    # Step 1: Await initial JSON handshake with ticket within 10 seconds
    try:
        data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
    except (asyncio.TimeoutError, WebSocketDisconnect, Exception) as exc:
        logger.warning("WebSocket handshake failed or timed out for mission %s: %s", mission_id, exc)
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close(code=4401, reason="Handshake timeout or invalid payload")
            except Exception:
                pass
        return

    if not isinstance(data, dict) or "ticket" not in data:
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close(code=4401, reason="Missing ticket in handshake")
            except Exception:
                pass
        return

    ticket = str(data.get("ticket"))
    try:
        after_sequence = int(data.get("after_sequence", 0))
    except (ValueError, TypeError):
        after_sequence = 0

    # Step 2: Validate ticket via session_auth_service
    try:
        operator = session_auth_service.consume_websocket_ticket(ticket)
    except Exception as exc:
        logger.warning("Invalid WebSocket ticket for mission %s: %s", mission_id, exc)
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close(code=4401, reason="Unauthorized ticket")
            except Exception:
                pass
        return

    # Step 3: Check mission existence
    service = get_mission_service()
    mission = service.get_mission(mission_id)
    if not mission:
        logger.warning("Mission %s not found during WebSocket handshake", mission_id)
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close(code=4404, reason="Mission not found")
            except Exception:
                pass
        return

    # Step 4: Register live subscription and replay historical events
    queue = service.subscribe(mission_id)
    try:
        # Replay durable events from store
        historical_events = service.get_events_after(mission_id, after_sequence=after_sequence)
        last_seq = after_sequence

        for event in historical_events:
            await websocket.send_json(event)
            last_seq = max(last_seq, event.get("sequence", 0))

        # Step 5: Live event forwarding and disconnect monitor
        async def forward_loop() -> None:
            nonlocal last_seq
            while True:
                ev = await queue.get()
                ev_seq = ev.get("sequence", 0)
                if ev_seq > last_seq:
                    await websocket.send_json(ev)
                    last_seq = ev_seq

        async def receive_loop() -> None:
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    break

        forward_task = asyncio.create_task(forward_loop())
        receive_task = asyncio.create_task(receive_loop())

        done, pending = await asyncio.wait(
            [forward_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from mission %s", mission_id)
    except Exception as exc:
        logger.warning("WebSocket streaming error for mission %s: %s", mission_id, exc)
    finally:
        service.unsubscribe(mission_id, queue)
