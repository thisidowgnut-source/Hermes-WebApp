import os
import json
import shutil
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.routers.system import QUEUE_FILE, _write_queue, _read_queue
from backend.config import config

client = TestClient(app)

@pytest.fixture
def tmp_path_local():
    local_tmp = os.path.join(config.BASE_DIR, ".pytest_tmp", "system_tests")
    if os.path.exists(local_tmp):
        shutil.rmtree(local_tmp, ignore_errors=True)
    os.makedirs(local_tmp, exist_ok=True)
    yield local_tmp
    shutil.rmtree(local_tmp, ignore_errors=True)

@pytest.fixture(autouse=True)
def setup_teardown_queue():
    # Save original queue file content if exists
    original_content = None
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            original_content = f.read()
    
    # Initialize clean test queue
    test_data = [
        {"id": "job-1", "title": "Build Artifacts", "status": "pending"},
        {"id": "job-2", "title": "Run Security Audit", "status": "queued"},
        {"title": "Unindexed Item", "status": "staged"}
    ]
    _write_queue(test_data)
    
    yield
    
    # Restore original content
    if original_content is not None:
        os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            f.write(original_content)
    elif os.path.exists(QUEUE_FILE):
        try:
            os.remove(QUEUE_FILE)
        except Exception:
            pass

def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cpu" in data
    assert "ram" in data
    assert "disk" in data
    assert "disk_free" in data
    assert isinstance(data["cpu"], (int, float))
    assert isinstance(data["ram"], (int, float))
    assert isinstance(data["disk"], (int, float))
    assert isinstance(data["disk_free"], (int, float))

def test_get_queue():
    response = client.get("/api/queue")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
    assert "queue" in data
    assert len(data["queue"]) == 3
    assert data["queue"][0]["id"] == "job-1"

def test_delete_queue_item_by_id():
    response = client.delete("/api/queue/job-1")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
    
    get_res = client.get("/api/queue")
    queue = get_res.json()["queue"]
    assert len(queue) == 2
    assert not any(item.get("id") == "job-1" for item in queue if isinstance(item, dict))

def test_delete_queue_item_by_index():
    response = client.delete("/api/queue/0")
    assert response.status_code == 200
    
    get_res = client.get("/api/queue")
    queue = get_res.json()["queue"]
    assert len(queue) == 2

def test_delete_queue_item_not_found():
    response = client.delete("/api/queue/non-existent-id-999")
    assert response.status_code == 404

def test_clear_queue():
    response = client.post("/api/queue/clear")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
    
    get_res = client.get("/api/queue")
    assert len(get_res.json()["queue"]) == 0

def test_stream_telemetry():
    response = client.get("/api/stream/telemetry?limit=1")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    
    content = response.text
    assert "data: " in content
    line = [l for l in content.splitlines() if l.startswith("data: ")][0]
    payload = json.loads(line.replace("data: ", ""))
    assert "cpu" in payload
    assert "ram" in payload

def test_get_obsidian_context():
    response = client.get("/api/system/obsidian-context")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_get_obsidian_context_mocked(tmp_path_local, monkeypatch):
    test_file = os.path.join(tmp_path_local, "context.json")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write('{"vaultPath": "C:\\\\Vault\\\\Note.md"}')
    monkeypatch.setenv("OBSIDIAN_CONTEXT_BRIDGE_PATH", str(test_file))
    
    response = client.get("/api/system/obsidian-context")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["vaultPath"] == "C:\\Vault\\Note.md"

def test_get_kanban_tasks():
    response = client.get("/api/system/kanban")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_get_network_scan():
    response = client.get("/api/system/network-scan")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "total_connections" in data
    assert "connections" in data
    assert isinstance(data["connections"], list)

def test_get_threat_scan():
    response = client.get("/api/system/threat-scan")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "threat_count" in data
    assert "threats" in data
    assert "verdict" in data
    assert data["verdict"] in ("CLEAN", "ALERT")
    assert "high_cpu_processes" in data

def test_get_env_info():
    response = client.get("/api/system/env-info")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "hostname" in data
    assert "os" in data
    assert "architecture" in data
    assert "cpu_count_logical" in data
    assert "ram_total_gb" in data
    assert "uptime" in data
    assert "drives" in data
    assert isinstance(data["drives"], list)
    assert "network_interfaces" in data

def test_get_swarm_status():
    response = client.get("/api/system/swarm-status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "swarm_size" in data
    assert "agents" in data
    assert isinstance(data["agents"], list)

def test_file_read_write(tmp_path):
    test_file = tmp_path / "test_note.txt"
    test_file.write_text("Hello Hermes OS", encoding="utf-8")

    # Read test
    res = client.post("/api/files/read", json={"path": str(test_file)})
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["content"] == "Hello Hermes OS"

    # Write test
    res_write = client.post("/api/files/write", json={"path": str(test_file), "content": "Updated Content", "create_backup": True})
    assert res_write.status_code == 200
    assert res_write.json()["status"] == "success"
    assert test_file.read_text(encoding="utf-8") == "Updated Content"
    assert os.path.exists(f"{test_file}.bak")

def test_file_read_nonexistent():
    res = client.post("/api/files/read", json={"path": "C:\\nonexistent_file_12345.txt"})
    assert res.status_code == 404

def test_get_system_services():
    res = client.get("/api/system/services")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "total" in data
    assert "running_count" in data
    assert isinstance(data["services"], list)

def test_control_service_invalid_action():
    res = client.post("/api/system/services/ADPSvc/invalid_action")
    assert res.status_code == 400

def test_send_telegram_alert():
    res = client.post("/api/system/send-alert", json={"title": "Test Alert", "message": "Test payload", "level": "INFO"})
    assert res.status_code == 200
    assert res.json()["status"] in ("success", "skipped", "error")

def test_fim_baseline_and_scan(tmp_path):
    # Test FIM baseline creation and scan
    res_base = client.post("/api/forensics/fim/baseline", json={"dir": str(tmp_path)})
    assert res_base.status_code == 200
    assert res_base.json()["status"] == "success"

    # Scan clean
    res_scan = client.get(f"/api/forensics/fim/scan?dir={tmp_path}")
    assert res_scan.status_code == 200
    assert res_scan.json()["status"] == "success"
    assert res_scan.json()["tampered_count"] == 0

def test_firewall_rules_endpoint():
    res = client.get("/api/forensics/firewall/rules")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "rules" in res.json()

def test_event_logs_endpoint():
    res = client.get("/api/forensics/event-logs")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "logs" in res.json()

def test_workflow_schedule_and_list():
    # Schedule task
    res_sch = client.post("/api/workflow/task/schedule", json={
        "name": "Auto Sync Task",
        "cron_expr": "*/10 * * * *",
        "command": "python scripts/sync.py",
        "interval_sec": 600
    })
    assert res_sch.status_code == 200
    assert res_sch.json()["status"] == "success"
    task_id = res_sch.json()["task"]["id"]

    # List tasks
    res_list = client.get("/api/workflow/tasks")
    assert res_list.status_code == 200
    assert res_list.json()["status"] == "success"
    assert res_list.json()["count"] >= 1

    # Cancel task
    res_can = client.post(f"/api/workflow/task/{task_id}/cancel")
    assert res_can.status_code == 200
    assert res_can.json()["status"] == "success"

def test_workflow_dag_endpoint():
    res = client.get("/api/workflow/dag")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "nodes" in res.json()
    assert "edges" in res.json()

def test_obsidian_graph_endpoint():
    res = client.get("/api/obsidian/graph")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "nodes" in res.json()
    assert "edges" in res.json()

def test_obsidian_search_endpoint():
    res = client.post("/api/obsidian/search", json={"query": "Hermes"})
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "results" in res.json()




