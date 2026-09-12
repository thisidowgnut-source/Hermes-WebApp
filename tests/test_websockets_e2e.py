import json
import pytest
import subprocess
import sys
import time
import urllib.request
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import config

client = TestClient(app)

def test_websocket_terminal_e2e():
    """
    Test /ws/terminal WebSocket endpoint:
    - Handshake (connect successfully)
    - Ping/Pong exchange
    - Text command exchange
    - Disconnect
    """
    with client.websocket_connect("/ws/terminal") as websocket:
        # Ping / Pong
        websocket.send_text("ping")
        resp = websocket.receive_text()
        data = json.loads(resp)
        assert data.get("type") == "pong"

        # Text command exchange
        websocket.send_text("Write-Output 'HERMES_TERMINAL_TEST'")
        output_received = False
        for _ in range(10):
            try:
                msg = websocket.receive_text()
                if "HERMES_TERMINAL_TEST" in msg:
                    output_received = True
                    break
            except Exception:
                break
        assert output_received, "Expected terminal command output not received"

def test_websocket_browser_e2e():
    """
    Test /ws/browser WebSocket endpoint:
    - Handshake (connect successfully)
    - Ping/Pong exchange
    - Frame receipt
    - Disconnect
    """
    with client.websocket_connect("/ws/browser") as websocket:
        websocket.send_text(json.dumps({"type": "ping"}))
        
        # Read messages until we get a pong or frame
        got_pong_or_frame = False
        for _ in range(5):
            try:
                msg = websocket.receive_text()
                data = json.loads(msg)
                if data.get("type") in ("pong", "frame"):
                    got_pong_or_frame = True
                    break
            except Exception:
                break
        assert got_pong_or_frame, "Expected pong or frame from browser WebSocket"

def test_websocket_audio_e2e():
    """
    Test /ws/audio WebSocket endpoint:
    - Handshake (connect successfully)
    - Binary PCM audio send
    - JSON transcript/command frame receipt
    - Disconnect
    """
    with client.websocket_connect("/ws/audio") as websocket:
        # Handshake frame check
        init_frame = websocket.receive_json()
        assert init_frame.get("type") in ("connection_established", "pong")

        # Ping / Pong check
        websocket.send_text(json.dumps({"type": "ping"}))
        resp = websocket.receive_json()
        assert resp.get("type") == "pong"

        # Binary PCM audio frame send
        dummy_pcm = b"\x00\x01\x00\x02" * 100
        websocket.send_bytes(dummy_pcm)

        # JSON transcript/command frame receipt
        data_audio = websocket.receive_json()
        assert data_audio.get("type") in ("audio_telemetry", "speech_transcript")
        assert "transcript" in data_audio or "speech_transcript" in data_audio
        assert "data" in data_audio or "vad" in data_audio

def test_websocket_swarm_e2e():
    """
    Test /ws/swarm WebSocket endpoint:
    - Handshake (connect successfully)
    - Telemetry/status broadcast receipt
    - Ping/Pong exchange
    - Disconnect
    """
    with client.websocket_connect("/ws/swarm") as websocket:
        # Telemetry/status broadcast receipt on connect
        initial_msg = websocket.receive_text()
        data_init = json.loads(initial_msg)
        assert data_init.get("type") in ("telemetry", "swarm_telemetry")
        assert "data" in data_init or "active_count" in data_init

        # Ping / Pong exchange
        websocket.send_text(json.dumps({"type": "ping"}))
        resp = websocket.receive_text()
        data = json.loads(resp)
        assert data.get("type") == "pong"

def test_uvicorn_launcher_port_9220():
    """
    Uvicorn Launcher Check: Verify programmatically that main.py launches app cleanly on port 9220.
    """
    assert config.PORT in (9220, 9230)
    assert config.HOST in ("127.0.0.1", "0.0.0.0")

    running = False
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{config.PORT}/api/stats", timeout=1)
        if req.status == 200:
            running = True
    except Exception:
        running = False

    if not running:
        proc = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=config.BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        try:
            for _ in range(15):
                time.sleep(0.5)
                if proc.poll() is not None:
                    out, _ = proc.communicate()
                    pytest.fail(f"main.py exited prematurely with code {proc.returncode}:\n{out}")
                try:
                    req = urllib.request.urlopen("http://127.0.0.1:9220/api/stats", timeout=1)
                    if req.status == 200:
                        running = True
                        break
                except Exception:
                    pass
            assert running, "Server launched via main.py on port 9220 did not respond within timeout"
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
    else:
        assert running, "Live server on port 9220 is running cleanly and responding with HTTP 200 OK"
