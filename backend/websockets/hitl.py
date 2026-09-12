"""
HITL (Human-in-the-Loop) WebSocket Handler
===========================================
Allows AI agents to pause execution and request human intervention
for CAPTCHAs, 2FA, complex auth flows, or ambiguous decisions.
"""
import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter()

# Active HITL sessions
hitl_sessions: Dict[str, Dict[str, Any]] = {}


class HitlRequest(BaseModel):
    """Request from AI agent for human intervention."""
    agent_id: str
    agent_name: str
    reason: str  # "captcha", "2fa", "consent", "ambiguous", "approval"
    context: Dict[str, Any]
    timeout_seconds: int = 300
    priority: str = "high"  # "low", "medium", "high", "critical"


class HitlResponse(BaseModel):
    """Human response to HITL request."""
    session_id: str
    action: str  # "continue", "abort", "retry", "custom"
    payload: Dict[str, Any] = {}


@router.websocket("/ws/hitl")
async def hitl_ws(websocket: WebSocket):
    """WebSocket endpoint for HITL communication.
    
    Frontend (Telegram Mini App) connects here to receive HITL requests
    and send human responses back to the requesting agent.
    """
    await websocket.accept()
    client_id = str(uuid.uuid4())[:8]
    
    # Track connected clients
    connected_clients = hitl_sessions.setdefault("_clients", {})
    connected_clients[client_id] = websocket
    
    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "client_id": client_id,
            "message": "HITL channel established"
        }))
        
        while True:
            data = await websocket.receive_text()
            
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue
            
            msg_type = msg.get("type")
            
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
            elif msg_type == "hitl_response":
                # Human responded to a HITL request
                session_id = msg.get("session_id")
                action = msg.get("action")
                payload = msg.get("payload", {})
                
                if session_id in hitl_sessions:
                    session = hitl_sessions[session_id]
                    session["response"] = {"action": action, "payload": payload}
                    session["event"].set()  # Wake up waiting agent
                    
                    # Notify agent via callback if registered
                    if "callback" in session:
                        try:
                            await session["callback"](session["response"])
                        except Exception:
                            pass
                        
                    await websocket.send_text(json.dumps({
                        "type": "ack",
                        "session_id": session_id,
                        "status": "delivered"
                    }))
                    
            elif msg_type == "get_pending":
                # Frontend requests pending HITL sessions
                pending = [
                    {
                        "session_id": sid,
                        "agent_name": s["agent_name"],
                        "reason": s["reason"],
                        "context": s["context"],
                        "priority": s["priority"],
                        "created_at": s["created_at"]
                    }
                    for sid, s in hitl_sessions.items()
                    if sid != "_clients" and "response" not in s
                ]
                await websocket.send_text(json.dumps({
                    "type": "pending_list",
                    "sessions": pending
                }))
                
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    except Exception as e:
        print(f"HITL WS error: {e}")
    finally:
        connected_clients.pop(client_id, None)


async def request_human_intervention(
    agent_id: str,
    agent_name: str,
    reason: str,
    context: Dict[str, Any],
    timeout_seconds: int = 300,
    priority: str = "high"
) -> Dict[str, Any]:
    """
    Called by AI agents to request human intervention.
    Blocks until human responds or timeout.
    """
    session_id = str(uuid.uuid4())
    event = asyncio.Event()
    
    session = {
        "session_id": session_id,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "reason": reason,
        "context": context,
        "priority": priority,
        "timeout": timeout_seconds,
        "created_at": asyncio.get_event_loop().time(),
        "event": event,
        "response": None
    }
    
    hitl_sessions[session_id] = session
    
    # Broadcast to all connected clients
    connected_clients = hitl_sessions.get("_clients", {})
    broadcast_msg = json.dumps({
        "type": "hitl_request",
        "session_id": session_id,
        "agent_name": agent_name,
        "reason": reason,
        "context": context,
        "priority": priority,
        "timeout": timeout_seconds
    })
    
    for ws in connected_clients.values():
        try:
            await ws.send_text(broadcast_msg)
        except Exception:
            pass
    
    # Wait for response or timeout
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        hitl_sessions.pop(session_id, None)
        return {
            "status": "timeout",
            "session_id": session_id,
            "message": f"No human response within {timeout_seconds}s"
        }
    
    response = session.get("response", {})
    hitl_sessions.pop(session_id, None)
    
    return {
        "status": "completed",
        "session_id": session_id,
        "action": response.get("action"),
        "payload": response.get("payload", {})
    }


@router.post("/api/hitl/request")
async def http_request_hitl(request: HitlRequest):
    """HTTP endpoint for agents to request HITL (non-WS clients)."""
    result = await request_human_intervention(
        agent_id=request.agent_id,
        agent_name=request.agent_name,
        reason=request.reason,
        context=request.context,
        timeout_seconds=request.timeout_seconds,
        priority=request.priority
    )
    return result


@router.get("/api/hitl/pending")
async def get_pending_hitl():
    """Get list of pending HITL requests."""
    pending = [
        {
            "session_id": sid,
            "agent_name": s["agent_name"],
            "reason": s["reason"],
            "context": s["context"],
            "priority": s["priority"],
            "created_at": s["created_at"]
        }
        for sid, s in hitl_sessions.items()
        if sid != "_clients" and "response" not in s
    ]
    return {"status": "success", "pending": pending, "count": len(pending)}