import os
import sys
import json
import time
import base64
import asyncio
import threading
import pytest
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.swarm_manager import swarm_manager, SWARM_QUEUE_FILE
from backend.services.audio_engine import audio_engine

client = TestClient(app)

# Helper function for generating test PCM audio bytes
def generate_pcm(freq=440.0, duration=0.1, sample_rate=16000):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    sine = 0.5 * np.sin(2 * np.pi * freq * t)
    return (sine * 32767).astype(np.int16).tobytes()

# ============================================================================
# 1. SWARM PROCESS LIFECYCLE STRESS & CORNER CASES
# ============================================================================

def test_swarm_invalid_agent_ids():
    """Test get and terminate on invalid, empty, or malicious agent IDs."""
    invalid_ids = [
        "non-existent-123",
        "",
        "   ",
        "../../etc/passwd",
        "agent-'; DROP TABLE agents;--",
        "<script>alert(1)</script>",
        "a" * 1000
    ]
    for aid in invalid_ids:
        # GET request
        res = client.get(f"/api/swarm/agent/{aid}")
        assert res.status_code in (404, 422), f"Expected 404/422 for invalid aid: {aid}, got {res.status_code}"
        
        # POST terminate request
        res_term = client.post(f"/api/swarm/agent/{aid}/terminate")
        assert res_term.status_code in (404, 422), f"Expected 404/422 for terminate aid: {aid}, got {res_term.status_code}"

def test_swarm_non_existent_pid_termination():
    """Test termination when agent's process is dead or has non-existent PID."""
    # Spawn a quick agent that finishes almost instantly
    res = client.post("/api/swarm/spawn", json={
        "name": "Quick Exit Agent",
        "task": "Exit fast",
        "command": f'"{sys.executable}" -c "exit(0)"'
    })
    assert res.status_code == 200
    agent_id = res.json()["agent"]["id"]
    
    # Wait for process to exit
    time.sleep(1.5)
    
    # Attempt termination on already exited agent
    term_res = client.post(f"/api/swarm/agent/{agent_id}/terminate")
    assert term_res.status_code == 200
    assert term_res.json()["agent"]["status"] in ("completed", "failed")

    # Manually insert agent with fake non-existent PID (e.g. 999999) into swarm_manager
    fake_id = "agent-fake-pid-999999"
    with swarm_manager._lock:
        swarm_manager.agents[fake_id] = {
            "id": fake_id,
            "name": "Ghost Agent",
            "task": "Test non-existent PID",
            "pid": 999999,
            "status": "running",
            "logs": []
        }
    
    term_fake = client.post(f"/api/swarm/agent/{fake_id}/terminate")
    assert term_fake.status_code == 200
    assert term_fake.json()["agent"]["status"] == "failed"

def test_swarm_rapid_spawn_stress():
    """Test rapid parallel spawn requests (20 agents concurrently)."""
    spawn_count = 20
    results = []

    def spawn_worker(idx):
        t0 = time.perf_counter()
        resp = client.post("/api/swarm/spawn", json={
            "name": f"Rapid Agent #{idx}",
            "task": f"Parallel stress iteration {idx}",
            "command": f'"{sys.executable}" -c "__import__(\'time\').sleep(1)"'
        })
        elapsed = time.perf_counter() - t0
        return resp.status_code, resp.json(), elapsed

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(spawn_worker, i) for i in range(spawn_count)]
        for f in as_completed(futures):
            code, data, elapsed = f.result()
            results.append((code, data, elapsed))

    # All spawns should succeed with HTTP 200
    successes = [r for r in results if r[0] == 200 and r[1].get("status") == "success"]
    assert len(successes) == spawn_count, f"Expected {spawn_count} successful spawns, got {len(successes)}"
    
    avg_latency = sum(r[2] for r in results) / len(results)
    max_latency = max(r[2] for r in results)
    print(f"\n[EMPIRICAL METRIC] Rapid Spawn (20 parallel): Avg Latency = {avg_latency*1000:.2f}ms, Max Latency = {max_latency*1000:.2f}ms")

    # Cleanup spawned agents
    for r in successes:
        aid = r[1]["agent"]["id"]
        swarm_manager.terminate_agent(aid)

def test_swarm_json_persistence_corruption_handling():
    """Test how swarm_manager handles corrupted JSON persistence files on startup/reload."""
    os.makedirs(os.path.dirname(SWARM_QUEUE_FILE), exist_ok=True)
    
    corruption_cases = [
        "{invalid_json: true,",     # Syntax error
        "BINARY_NON_JSON_GARBAGE_12345\x00\xFF", # Binary
        "",                         # Empty file
        "null",                     # JSON null
        "[]"                        # JSON array instead of dict
    ]

    for corrupt_content in corruption_cases:
        with open(SWARM_QUEUE_FILE, "w", encoding="utf-8", errors="ignore") as f:
            f.write(corrupt_content)
        
        # Force _load_state()
        try:
            swarm_manager._load_state()
            # Must recover gracefully without raising exception
            assert isinstance(swarm_manager.agents, dict), f"Failed to recover dict state for corrupt case: {corrupt_content}"
        except Exception as e:
            pytest.fail(f"_load_state crashed on corrupt JSON input '{corrupt_content}': {e}")


# ============================================================================
# 2. AUDIO STREAM & VAD STRESS & BOUNDARY CASES
# ============================================================================

def test_audio_invalid_pcm_chunk_sizes():
    """Test audio processing under odd byte lengths, empty bytes, and zero/huge arrays."""
    # 1. Odd number of bytes (e.g. 15 bytes)
    odd_bytes = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e"
    b64_odd = base64.b64encode(odd_bytes).decode("utf-8")
    res_odd = client.post("/api/audio/process-stem", json={"audio_base64": b64_odd})
    assert res_odd.status_code == 200
    assert res_odd.json()["bytes_processed"] == 15

    # 2. Empty byte payload via base64 ""
    res_empty = client.post("/api/audio/process-stem", json={"audio_base64": ""})
    assert res_empty.status_code == 400

    # 3. Direct empty raw body
    res_raw_empty = client.post("/api/audio/process-stem", data=b"")
    assert res_raw_empty.status_code == 400

    # 4. Large PCM chunk (1 MB of PCM noise)
    large_pcm = np.random.randint(-32768, 32767, size=500000, dtype=np.int16).tobytes()
    b64_large = base64.b64encode(large_pcm).decode("utf-8")
    t0 = time.perf_counter()
    res_large = client.post("/api/audio/process-stem", json={"audio_base64": b64_large})
    elapsed = time.perf_counter() - t0
    assert res_large.status_code == 200
    data_large = res_large.json()
    assert data_large["bytes_processed"] == len(large_pcm)
    assert len(data_large["spectrum"]) == 32
    print(f"\n[EMPIRICAL METRIC] Large PCM Stem Processing (1MB): Elapsed = {elapsed*1000:.2f}ms")

def test_audio_vad_threshold_bounds():
    """Test VAD threshold setting under extreme and invalid boundary values."""
    test_bounds = [
        (-1.0, 0.001),     # Below min -> clamped to 0.001
        (0.0, 0.001),      # Zero -> clamped to 0.001
        (0.5, 0.5),        # Valid
        (1.0, 1.0),        # Upper max limit
        (2.5, 1.0),        # Above max -> clamped to 1.0
        (-999.0, 0.001)    # Very negative -> clamped to 0.001
    ]
    for val, expected_clamped in test_bounds:
        res = client.post("/api/audio/vad-threshold", json={"threshold": val})
        assert res.status_code == 200
        assert res.json()["vad_threshold"] == pytest.approx(expected_clamped, abs=1e-4)

    # Invalid type test
    res_bad = client.post("/api/audio/vad-threshold", json={"threshold": "invalid_string"})
    assert res_bad.status_code == 422

def test_audio_empty_audio_clips():
    """Test process_stem service method directly with 0-byte input."""
    res = audio_engine.process_stem(b"")
    assert res["status"] == "empty"
    assert res["stems"] == {"vocals": 0.0, "drums": 0.0, "bass": 0.0, "other": 0.0}
    assert res["spectrum"] == [0.0] * 32

    vad = audio_engine.detect_vad(b"")
    assert vad["is_speech"] is False
    assert vad["rms"] == 0.0
    assert vad["db"] == -100.0

def test_audio_unrecognized_voice_commands():
    """Test voice command parser with unrecognized, gibberish, empty, or special char inputs."""
    test_inputs = [
        ("", False, "unknown"),
        ("   ", False, "unknown"),
        ("asdfghjkl zxcvbnm 12345", False, "unknown"),
        ("🤖👽 Quantum flux generator 🚀", False, "unknown"),
        ("DROP DATABASE system;", False, "unknown"),
        ("a" * 10000, False, "unknown"),
        # Valid intents for comparison
        ("please open terminal now", True, "open_terminal"),
        ("can you show swarm agents", True, "swarm_control")
    ]
    for text, expected_match, expected_intent in test_inputs:
        res = client.post("/api/audio/parse-command", json={"text": text})
        assert res.status_code == 200
        data = res.json()["result"]
        assert data["matched"] is expected_match
        if not expected_match:
            assert data["intent"] == "unknown"
            assert data["command"] is None
        else:
            assert data["intent"] == expected_intent


# ============================================================================
# 3. WEBSOCKET CONNECTIVITY STRESS & CORNER CASES
# ============================================================================

def test_ws_unexpected_disconnects_and_reconnects():
    """Test opening and immediately closing WebSocket connections across endpoints."""
    endpoints = ["/ws/swarm", "/ws/audio", "/ws/terminal"]
    for ep in endpoints:
        for _ in range(5):
            with client.websocket_connect(ep) as ws:
                # Close immediately without sending/reading
                pass

def test_ws_ping_pong_frame_handling():
    """Test ping/pong frame behavior under raw strings, JSON frames, and rapid floods."""
    # Test on /ws/swarm
    with client.websocket_connect("/ws/swarm") as ws:
        _ = ws.receive_text() # Consume initial telemetry
        
        # 1. Plain text "ping"
        ws.send_text("ping")
        resp1 = json.loads(ws.receive_text())
        assert resp1.get("type") == "pong"

        # 2. JSON '{"type": "ping"}'
        ws.send_text(json.dumps({"type": "ping"}))
        resp2 = json.loads(ws.receive_text())
        assert resp2.get("type") == "pong"

        # 3. Plain text "pong" (should be ignored gracefully)
        ws.send_text("pong")

        # 4. Rapid ping flood (10 pings)
        t0 = time.perf_counter()
        pongs_received = 0
        for _ in range(10):
            ws.send_text("ping")
        for _ in range(10):
            try:
                msg = json.loads(ws.receive_text())
                if msg.get("type") == "pong":
                    pongs_received += 1
            except Exception:
                pass
        elapsed = time.perf_counter() - t0
        assert pongs_received == 10, f"Expected 10 pongs, got {pongs_received}"
        print(f"\n[EMPIRICAL METRIC] WS Ping Flood (10 frames): Elapsed = {elapsed*1000:.2f}ms")

def test_ws_concurrent_connections():
    """Test concurrent WebSocket connections across /ws/swarm, /ws/audio, /ws/terminal."""
    connection_count = 5

    def ws_worker(ep):
        try:
            with client.websocket_connect(ep) as ws:
                if ep == "/ws/swarm":
                    msg = ws.receive_text()
                    assert "telemetry" in msg
                elif ep == "/ws/audio":
                    msg = ws.receive_json()
                    assert msg["type"] == "connection_established"
                elif ep == "/ws/terminal":
                    ws.send_text("ping")
                    msg = ws.receive_text()
                    assert "pong" in msg
                time.sleep(0.5)
                return True
        except Exception as e:
            return False

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = []
        for ep in ["/ws/swarm", "/ws/audio", "/ws/terminal"]:
            for _ in range(connection_count):
                futures.append(executor.submit(ws_worker, ep))
        
        results = [f.result() for f in as_completed(futures)]

    passed = sum(1 for r in results if r is True)
    total = len(results)
    assert passed == total, f"Concurrent WS test: {passed}/{total} connections succeeded"
    print(f"\n[EMPIRICAL METRIC] Concurrent WS Connections: {passed}/{total} Passed")
