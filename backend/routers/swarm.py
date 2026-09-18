from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.services.swarm_manager import swarm_manager

router = APIRouter(prefix="/api/swarm", tags=["swarm"])

class SpawnRequest(BaseModel):
    name: Optional[str] = None
    task: Optional[str] = None
    command: Optional[str] = None

class SubtaskSpec(BaseModel):
    role: str
    name: Optional[str] = None
    task: str
    command: Optional[str] = None

class DelegateGoalRequest(BaseModel):
    goal: str
    orchestrator_name: Optional[str] = "Orchestrator-Lead"
    goal_mode: Optional[bool] = True
    subtasks: Optional[List[SubtaskSpec]] = None

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
    # P0 hardening: reject shell metacharacters in custom command (allow plain executables/args only)
    if req.command and any(ch in req.command for ch in ['&', '|', ';', '`', '$(', '\n', '\r']):
        raise HTTPException(status_code=400, detail="Command rejected: shell metacharacters not allowed")
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

@router.post("/delegate")
def delegate_goal(req: DelegateGoalRequest):
    if req.subtasks:
        for st in req.subtasks:
            if st.command and any(ch in st.command for ch in ['&', '|', ';', '`', '$(', '\n', '\r']):
                raise HTTPException(status_code=400, detail="Command rejected: shell metacharacters not allowed")
    
    subtasks_data = [st.model_dump() for st in req.subtasks] if req.subtasks else None
    result = swarm_manager.delegate_goal(
        goal=req.goal,
        orchestrator_name=req.orchestrator_name or "Orchestrator-Lead",
        subtasks=subtasks_data,
        goal_mode=req.goal_mode if req.goal_mode is not None else True
    )
    return {
        "status": "success",
        "delegation": result,
        **{k: v for k, v in result.items() if k != "status"}
    }

@router.get("/delegations")
def get_delegations():
    delegations = swarm_manager.get_delegations()
    return {
        "status": "success",
        "count": len(delegations),
        "delegations": delegations
    }

@router.get("/delegation/{delegation_id}")
def get_delegation(delegation_id: str):
    delegation = swarm_manager.get_delegation(delegation_id)
    if not delegation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delegation with ID '{delegation_id}' not found"
        )
    return {
        "status": "success",
        "delegation": delegation
    }
