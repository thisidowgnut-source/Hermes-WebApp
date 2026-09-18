import asyncio
import json
import time
import psutil
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.swarm_manager import swarm_manager

router = APIRouter()

# Track connected clients for broadcast
connected_clients: set = set()


async def broadcast_to_all(message: Dict[str, Any]):
    """Broadcast message to all connected swarm clients."""
    dead_clients = set()
    for ws in connected_clients:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            dead_clients.add(ws)
    
    for ws in dead_clients:
        connected_clients.discard(ws)


@router.websocket("/ws/swarm")
async def swarm_ws(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    
    # Broadcast initial telemetry state on connect
    try:
        telemetry = swarm_manager.get_telemetry()
        system_info = get_system_snapshot()
        payload = {
            "type": "init",
            "telemetry": telemetry,
            "system": system_info,
            "timestamp": time.time()
        }
        await websocket.send_text(json.dumps(payload))
    except Exception:
        pass

    async def broadcast_loop():
        while True:
            try:
                await asyncio.sleep(2)
                telemetry = swarm_manager.get_telemetry()
                system_info = get_system_snapshot()
                payload = {
                    "type": "telemetry",
                    "telemetry": telemetry,
                    "system": system_info,
                    "timestamp": time.time()
                }
                await websocket.send_text(json.dumps(payload))
            except Exception:
                break

    task = asyncio.create_task(broadcast_loop())

    try:
        while True:
            data = await websocket.receive_text()
            if data in ("ping", '{"type": "ping"}', '{"type":"ping"}'):
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue
            elif data in ("pong", '{"type": "pong"}', '{"type":"pong"}'):
                continue
            
            try:
                msg = json.loads(data)
                mtype = msg.get("type")
                
                if mtype == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
                elif mtype == "get_telemetry":
                    telemetry = swarm_manager.get_telemetry()
                    system_info = get_system_snapshot()
                    payload = {
                        "type": "telemetry",
                        "telemetry": telemetry,
                        "system": system_info,
                        "timestamp": time.time()
                    }
                    await websocket.send_text(json.dumps(payload))
                    
                elif mtype == "spawn":
                    agent = swarm_manager.spawn_agent(
                        name=msg.get("name"),
                        task=msg.get("task"),
                        command=msg.get("command")
                    )
                    await broadcast_to_all({
                        "type": "agent_spawned",
                        "agent": agent,
                        "timestamp": time.time()
                    })
                    
                elif mtype == "terminate":
                    agent_id = msg.get("agent_id")
                    if agent_id:
                        result = swarm_manager.terminate_agent(agent_id)
                        await broadcast_to_all({
                            "type": "agent_terminated",
                            "agent_id": agent_id,
                            "result": result,
                            "timestamp": time.time()
                        })
                        
                elif mtype == "get_agent_logs":
                    agent_id = msg.get("agent_id")
                    lines = msg.get("lines", 100)
                    if agent_id:
                        logs = swarm_manager.get_agent_logs(agent_id, lines)
                        await websocket.send_text(json.dumps({
                            "type": "agent_logs",
                            "agent_id": agent_id,
                            "logs": logs,
                            "timestamp": time.time()
                        }))
                        
                elif mtype == "get_agent_details":
                    agent_id = msg.get("agent_id")
                    if agent_id:
                        details = swarm_manager.get_agent_details(agent_id)
                        await websocket.send_text(json.dumps({
                            "type": "agent_details",
                            "agent_id": agent_id,
                            "details": details,
                            "timestamp": time.time()
                        }))
                        
                elif mtype == "send_command":
                    # Send command to specific agent's stdin
                    agent_id = msg.get("agent_id")
                    command = msg.get("command")
                    if agent_id and command:
                        result = swarm_manager.send_agent_command(agent_id, command)
                        await websocket.send_text(json.dumps({
                            "type": "command_sent",
                            "agent_id": agent_id,
                            "result": result,
                            "timestamp": time.time()
                        }))
                        
                elif mtype == "subscribe_events":
                    # Client wants to subscribe to specific event types
                    event_types = msg.get("events", ["telemetry", "agent_status", "agent_log"])
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "events": event_types,
                        "timestamp": time.time()
                    }))
                    
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e),
                    "timestamp": time.time()
                }))
                
    except (WebSocketDisconnect, asyncio.CancelledError, Exception):
        pass
    finally:
        connected_clients.discard(websocket)
        task.cancel()


def get_system_snapshot() -> Dict[str, Any]:
    """Get current system resource snapshot."""
    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage('C:\\')
        except Exception:
            disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_available_gb": round(mem.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "uptime_seconds": int(time.time() - psutil.boot_time())
        }
    except Exception:
        return {}
