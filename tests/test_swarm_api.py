import os
import json
import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.swarm_manager import swarm_manager, SWARM_QUEUE_FILE

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown_swarm():
    # Save original queue file content if exists
    original_content = None
    if os.path.exists(SWARM_QUEUE_FILE):
        try:
            with open(SWARM_QUEUE_FILE, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception:
            pass

    # Clear swarm manager in-memory state
    with swarm_manager._lock:
        swarm_manager.agents = {}
        swarm_manager._processes = {}
        swarm_manager._save_state_unlocked()

    yield

    # Cleanup any running processes spawned during tests
    with swarm_manager._lock:
        agent_ids = list(swarm_manager.agents.keys())
    for aid in agent_ids:
        try:
            swarm_manager.terminate_agent(aid)
        except Exception:
            pass

    # Restore original content
    if original_content is not None:
        os.makedirs(os.path.dirname(SWARM_QUEUE_FILE), exist_ok=True)
        with open(SWARM_QUEUE_FILE, "w", encoding="utf-8") as f:
            f.write(original_content)
    elif os.path.exists(SWARM_QUEUE_FILE):
        try:
            os.remove(SWARM_QUEUE_FILE)
        except Exception:
            pass

def test_get_agents_empty():
    response = client.get("/api/swarm/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["active_count"] == 0
    assert data["total_count"] == 0
    assert isinstance(data["agents"], list)

def test_spawn_agent():
    payload = {
        "name": "Test Auditor Agent",
        "task": "Perform automated security scan",
        "command": "python -c \"import time; time.sleep(5)\""
    }
    response = client.post("/api/swarm/spawn", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    agent = data["agent"]
    assert agent["name"] == "Test Auditor Agent"
    assert agent["task"] == "Perform automated security scan"
    assert agent["status"] == "running"
    assert "id" in agent
    assert agent["pid"] is not None

def test_get_agent_by_id():
    spawn_res = client.post("/api/swarm/spawn", json={"name": "Fetch Test Agent", "task": "Testing get_agent"})
    agent_id = spawn_res.json()["agent"]["id"]

    response = client.get(f"/api/swarm/agent/{agent_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    agent = data["agent"]
    assert agent["id"] == agent_id
    assert "metrics" in agent
    assert "cpu_percent" in agent["metrics"]
    assert "memory_mb" in agent["metrics"]

def test_get_agent_not_found():
    response = client.get("/api/swarm/agent/non-existent-agent-999")
    assert response.status_code == 404

def test_terminate_agent():
    spawn_res = client.post("/api/swarm/spawn", json={
        "name": "Terminator Target",
        "task": "Long running task",
        "command": "python -c \"import time; time.sleep(60)\""
    })
    agent_id = spawn_res.json()["agent"]["id"]

    term_res = client.post(f"/api/swarm/agent/{agent_id}/terminate")
    assert term_res.status_code == 200
    term_data = term_res.json()
    assert term_data["status"] == "success"
    assert term_data["agent"]["status"] == "failed"

    # Verify agent list status update
    get_res = client.get(f"/api/swarm/agent/{agent_id}")
    assert get_res.json()["agent"]["status"] == "failed"

def test_terminate_agent_not_found():
    response = client.post("/api/swarm/agent/non-existent-agent-888/terminate")
    assert response.status_code == 404

def test_swarm_websocket():
    with client.websocket_connect("/ws/swarm") as websocket:
        # Initial telemetry broadcast
        data = websocket.receive_json()
        assert data.get("type") in ("telemetry", "swarm_telemetry")
        assert "active_count" in data or ("data" in data and "active_count" in data["data"])

        # Send ping and consume any broadcast frames until pong
        websocket.send_text("ping")
        got_pong = False
        for _ in range(5):
            try:
                msg = websocket.receive_json()
                if msg.get("type") == "pong":
                    got_pong = True
                    break
            except Exception:
                break
        assert got_pong, "Expected pong response from WebSocket ping"

        # Send spawn command over WebSocket
        websocket.send_json({
            "type": "spawn",
            "name": "WS Subagent",
            "task": "WS Spawn Task",
            "command": "python -c \"import time; time.sleep(2)\""
        })

        spawned_msg = None
        for _ in range(5):
            try:
                msg = websocket.receive_json()
                if msg.get("type") == "agent_spawned":
                    spawned_msg = msg
                    break
            except Exception:
                break

        assert spawned_msg is not None
        assert spawned_msg["agent"]["name"] == "WS Subagent"


def test_swarm_manager_defensive_load_null_or_invalid(tmp_path):
    from backend.services.swarm_manager import SwarmManager

    # 1. Test loading state from a file containing "null"
    null_file = tmp_path / "null_agents.json"
    null_file.write_text("null", encoding="utf-8")
    sm = SwarmManager(file_path=str(null_file))
    assert isinstance(sm.agents, dict)
    assert sm.agents == {}

    # 2. Test loading state from an empty file ""
    empty_file = tmp_path / "empty_agents.json"
    empty_file.write_text("", encoding="utf-8")
    sm_empty = SwarmManager(file_path=str(empty_file))
    assert isinstance(sm_empty.agents, dict)
    assert sm_empty.agents == {}

    # 3. Test loading state from a file containing corrupted JSON
    corrupt_file = tmp_path / "corrupt_agents.json"
    corrupt_file.write_text("{corrupt json content...", encoding="utf-8")
    sm_corrupt = SwarmManager(file_path=str(corrupt_file))
    assert isinstance(sm_corrupt.agents, dict)
    assert sm_corrupt.agents == {}

    # 4. Test loading state from a file containing non-dict JSON e.g. "[1, 2, 3]"
    list_file = tmp_path / "list_agents.json"
    list_file.write_text("[1, 2, 3]", encoding="utf-8")
    sm2 = SwarmManager(file_path=str(list_file))
    assert isinstance(sm2.agents, dict)
    assert sm2.agents == {}


