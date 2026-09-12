import base64
import json
import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def generate_test_pcm_bytes(freq: float = 440.0, duration: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Generates 16-bit mono PCM sine wave audio bytes for testing."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    sine_wave = 0.5 * np.sin(2 * np.pi * freq * t)
    int_samples = (sine_wave * 32767).astype(np.int16)
    return int_samples.tobytes()

def test_get_audio_status():
    response = client.get("/api/audio/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["status"] == "active"
    assert "vad_threshold" in data["data"]
    assert "stems_supported" in data["data"]

def test_process_stem_base64():
    pcm_bytes = generate_test_pcm_bytes(freq=440.0, duration=0.2)
    b64_str = base64.b64encode(pcm_bytes).decode("utf-8")

    payload = {
        "audio_base64": b64_str,
        "sample_rate": 16000,
        "vad_threshold": 0.01
    }
    response = client.post("/api/audio/process-stem", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "stems" in data
    assert "vocals" in data["stems"]
    assert "drums" in data["stems"]
    assert "bass" in data["stems"]
    assert "other" in data["stems"]
    assert "spectrum" in data
    assert len(data["spectrum"]) == 32
    assert "vad" in data

def test_process_stem_file_upload():
    pcm_bytes = generate_test_pcm_bytes(freq=120.0, duration=0.2)
    files = {"file": ("test.pcm", pcm_bytes, "application/octet-stream")}

    response = client.post("/api/audio/process-stem", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["bytes_processed"] == len(pcm_bytes)
    assert "stems" in data

def test_set_vad_threshold():
    response = client.post("/api/audio/vad-threshold", json={"threshold": 0.05})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["vad_threshold"] == 0.05

def test_parse_voice_command():
    response = client.post("/api/audio/parse-command", json={"text": "open terminal"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["matched"] is True
    assert data["result"]["intent"] == "open_terminal"
    assert data["result"]["command"] == "pwsh.exe"

def test_audio_websocket_connection_and_streaming():
    with client.websocket_connect("/ws/audio") as websocket:
        # Initial connection frame
        init_frame = websocket.receive_json()
        assert init_frame["type"] == "connection_established"
        assert init_frame["status"] == "ready"

        # Test sending binary PCM chunk
        pcm_bytes = generate_test_pcm_bytes(freq=440.0, duration=0.2)
        websocket.send_bytes(pcm_bytes)

        resp = websocket.receive_json()
        assert resp["type"] == "audio_telemetry"
        assert "vad" in resp
        assert "stems" in resp
        assert "spectrum" in resp
        assert len(resp["spectrum"]) == 32

        # Test sending JSON VAD update frame
        websocket.send_json({"action": "set_vad", "threshold": 0.03})
        vad_resp = websocket.receive_json()
        assert vad_resp["type"] == "vad_updated"
        assert vad_resp["vad_threshold"] == 0.03

        # Test sending JSON voice command simulation frame
        websocket.send_json({"action": "simulate_speech", "text": "show swarm"})
        cmd_resp = websocket.receive_json()
        assert cmd_resp["type"] == "voice_command"
        assert cmd_resp["matched"] is True
        assert cmd_resp["voice_command"]["intent"] == "swarm_control"
