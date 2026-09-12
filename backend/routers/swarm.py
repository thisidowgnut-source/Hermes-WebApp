from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.services.swarm_manager import swarm_manager

router = APIRouter(prefix="/api/swarm", tags=["swarm"])

class SpawnRequest(BaseModel):
    name: Optional[str] = None
    task: Optional[str] = None
    command: Optional[str] = None

@router.get("/agents")
def get_agents():
    agents = swarm_manager.get_agents()
    active_count = len([a for a in agents if a.get("status") == "running"])
    return {
        "status": "success",
        "active_count": active_count,
        "total_count": len(agents),
        "agents": agents
    }

@router.post("/spawn")
def spawn_agent(req: SpawnRequest = SpawnRequest()):
    agent = swarm_manager.spawn_agent(
        name=req.name,
        task=req.task,
        command=req.command
    )
    return {
        "status": "success",
        "agent": agent
    }

@router.get("/agent/{agent_id}")
def get_agent(agent_id: str):
    agent = swarm_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found"
        )
    return {
        "status": "success",
        "agent": agent
    }

@router.post("/agent/{agent_id}/terminate")
def terminate_agent(agent_id: str):
    agent = swarm_manager.terminate_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found"
        )
    return {
        "status": "success",
        "message": f"Agent {agent_id} terminated",
        "agent": agent
    }
