import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dohnut_stats_endpoint():
    response = client.get("/api/dohnut/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "revenue_today" in data
    assert "baking_pipeline" in data
    assert "catering_queue" in data
    assert "inventory" in data
    assert len(data["inventory"]["signature_flavors"]) > 0

def test_dohnut_social_accounts_endpoint():
    response = client.get("/api/dohnut/social/accounts")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "accounts" in data
    platforms = [a["platform"] for a in data["accounts"]]
    assert "tiktok" in platforms
    assert "instagram" in platforms

def test_dohnut_social_generate_endpoint():
    payload = {
        "topic": "Kuih Burger Donut Special Promo",
        "tone": "hype, tempting food review"
    }
    response = client.post("/api/dohnut/social/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "package" in data
    assert "tiktok" in data["package"]
    assert "instagram" in data["package"]
    assert "threads" in data["package"]
    assert "facebook" in data["package"]
    assert "x" in data["package"]
    assert "youtube" in data["package"]

def test_dohnut_ai_labs_status_endpoint():
    response = client.get("/api/dohnut/ai-labs/status")
    assert response.status_code == 200
    data = response.json()
    assert "webbridge" in data
    assert "open_design" in data

def test_dohnut_agent_swarm_status_endpoint():
    response = client.get("/api/dohnut/agent-swarm/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "agents" in data
    agent_names = [a["name"] for a in data["agents"]]
    assert any("Hermes" in name for name in agent_names)
    assert any("WebBridge" in name for name in agent_names)


def test_dohnut_publish_webbridge_endpoint():
    """Verify 1-tap post dispatch to WebBridge with OS clipboard sync."""
    payload = {
        "platform": "tiktok",
        "content": "Viral Doh-Nut test post with rich glaze ASMR",
    }
    response = client.post("/api/dohnut/social/publish-webbridge", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["platform"] == "tiktok"
    assert "target_url" in data
    assert "tiktok.com" in data["target_url"]
    assert data["clipboard_synced"] is True
    assert "message" in data

