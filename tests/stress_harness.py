import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure .queue/swarm_agents.json is valid before importing app
queue_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".queue", "swarm_agents.json")
os.makedirs(os.path.dirname(queue_path), exist_ok=True)
if not os.path.exists(queue_path) or open(queue_path, "r", encoding="utf-8").read().strip() in ("null", "", "None"):
    with open(queue_path, "w", encoding="utf-8") as f:
        f.write("{}")

# Clear TELEGRAM_BOT_TOKEN environment variable so bot polling (which requires external internet access) is skipped
os.environ["TELEGRAM_BOT_TOKEN"] = ""

import json
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
import numpy as np

from backend.main import app
from backend.services.swarm_manager import SwarmManager
from backend.services.audio_engine import AudioEngine

client = TestClient(app)

def main():
    print("=================================================================", flush=True)
    print("       HERMES-WEBAPP EMPIRICAL STRESS TEST & AUDIT HARNESS       ", flush=True)
    print("=================================================================", flush=True)

    # -----------------------------------------------------------------
    # STRESS TEST 1: Swarm Manager Concurrent Process Spawning
    # -----------------------------------------------------------------
    print("\n[STRESS TEST 1] Swarm Manager Process Spawning (20 Concurrent Agents)", flush=True)
    tmp_queue = os.path.join(".pytest_tmp", "stress_swarm.json")
    os.makedirs(os.path.dirname(tmp_queue), exist_ok=True)
    if os.path.exists(tmp_queue):
        os.remove(tmp_queue)

    sm = SwarmManager(file_path=tmp_queue)
    start_t = time.time()

    py_cmd = f'"{sys.executable}" -c "import time, sys; print(\\"START\\"); sys.stdout.flush(); time.sleep(0.2); print(\\"END\\"); sys.stdout.flush()"'

    def spawn_fn(i):
        return sm.spawn_agent(name=f"Worker-{i}", task=f"Task-{i}", command=py_cmd)

    with ThreadPoolExecutor(max_workers=20) as pool:
        agents = list(pool.map(spawn_fn, range(20)))

    spawn_time = time.time() - start_t
    print(f"  -> Concurrent spawn of 20 agents: {spawn_time:.3f}s (Avg: {spawn_time/20*1000:.1f}ms/agent)", flush=True)

    time.sleep(1.0)

    telemetry = sm.get_telemetry()
    print(f"  -> Telemetry under load: Active={telemetry['active_count']}, Total={telemetry['total_count']}, Total CPU={telemetry['swarm_metrics']['total_cpu_percent']}%, Total RAM={telemetry['swarm_metrics']['total_memory_mb']}MB", flush=True)

    all_agents = sm.get_agents()
    completed = sum(1 for a in all_agents if a.get("status") == "completed")
    failed = sum(1 for a in all_agents if a.get("status") == "failed")
    running = sum(1 for a in all_agents if a.get("status") == "running")
    print(f"  -> Process states: Completed={completed}, Failed={failed}, Running={running}", flush=True)

    long_cmd = f'"{sys.executable}" -c "import time; time.sleep(30)"'
    term_agents = [sm.spawn_agent(name=f"Term-{i}", command=long_cmd) for i in range(10)]
    term_start = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as pool:
        _ = list(pool.map(lambda a: sm.terminate_agent(a["id"]), term_agents))

    term_time = time.time() - term_start
    print(f"  -> Concurrent termination of 10 running processes: {term_time:.3f}s", flush=True)

    with open(tmp_queue, "r", encoding="utf-8") as f:
        file_data = json.load(f)
    print(f"  -> JSON state file integrity: PASSED ({len(file_data)} entries stored)", flush=True)

    # -----------------------------------------------------------------
    # STRESS TEST 2: Voice Audio Engine Compute & STEM Demux Throughput
    # -----------------------------------------------------------------
    print("\n[STRESS TEST 2] Voice Audio Engine Compute Throughput (500 PCM Chunks)", flush=True)
    ae = AudioEngine()

    t = np.linspace(0, 1.0, 16000, False)
    pcm_float = np.sin(2 * np.pi * 440 * t) * 0.5
    pcm_bytes = (pcm_float * 32767).astype(np.int16).tobytes()

    ae_start = time.time()
    for _ in range(500):
        _ = ae.detect_vad(pcm_bytes)
        _ = ae.process_stem(pcm_bytes)

    ae_time = time.time() - ae_start
    throughput = 500 / ae_time
    latency_ms = (ae_time / 500) * 1000

    print(f"  -> 500 VAD + STEM demux ops completed in {ae_time:.3f}s", flush=True)
    print(f"  -> Throughput: {throughput:.1f} ops/sec (Avg Latency: {latency_ms:.3f}ms/op)", flush=True)

    # -----------------------------------------------------------------
    # STRESS TEST 3: Rapid WebSocket Connect / Disconnect Cycles
    # -----------------------------------------------------------------
    print("\n[STRESS TEST 3] Rapid WebSocket Connect / Disconnect Cycles (50 Cycles)", flush=True)

    audio_cycles_ok = 0
    ws_audio_start = time.time()
    for _ in range(50):
        try:
            with client.websocket_connect("/ws/audio") as ws:
                _ = ws.receive_json()
                ws.send_text("ping")
                _ = ws.receive_json()
                audio_cycles_ok += 1
        except Exception as e:
            print(f"    Error in Audio WS: {e}", flush=True)
    ws_audio_time = time.time() - ws_audio_start
    print(f"  -> /ws/audio rapid connect/disconnect: {audio_cycles_ok}/50 cycles succeeded in {ws_audio_time:.3f}s ({ws_audio_time/50*1000:.1f}ms/cycle)", flush=True)

    swarm_cycles_ok = 0
    ws_swarm_start = time.time()
    for _ in range(50):
        try:
            with client.websocket_connect("/ws/swarm") as ws:
                _ = ws.receive_text()
                ws.send_text("ping")
                _ = ws.receive_text()
                swarm_cycles_ok += 1
        except Exception as e:
            print(f"    Error in Swarm WS: {e}", flush=True)
    ws_swarm_time = time.time() - ws_swarm_start
    print(f"  -> /ws/swarm rapid connect/disconnect: {swarm_cycles_ok}/50 cycles succeeded in {ws_swarm_time:.3f}s ({ws_swarm_time/50*1000:.1f}ms/cycle)", flush=True)

    # -----------------------------------------------------------------
    # STRESS TEST 4: High-Concurrency Audio WS PCM Streaming
    # -----------------------------------------------------------------
    print("\n[STRESS TEST 4] High-Concurrency Audio WS PCM Streaming (20 Clients x 10 Frames)", flush=True)

    dummy_pcm = b"\x00\x10" * 800
    total_frames = 0
    stream_errors = 0
    lock = threading.Lock()
    stream_start = time.time()

    def ws_client_worker(cid):
        nonlocal total_frames, stream_errors
        try:
            with client.websocket_connect("/ws/audio") as ws:
                _ = ws.receive_json()
                for _ in range(10):
                    ws.send_bytes(dummy_pcm)
                    res = ws.receive_json()
                    if res.get("type") == "audio_telemetry":
                        with lock:
                            total_frames += 1
        except Exception as e:
            with lock:
                stream_errors += 1

    with ThreadPoolExecutor(max_workers=20) as pool:
        list(pool.map(ws_client_worker, range(20)))

    stream_time = time.time() - stream_start
    print(f"  -> Streamed {total_frames} PCM frames across 20 concurrent WS clients in {stream_time:.3f}s ({total_frames/stream_time:.1f} frames/sec, errors={stream_errors})", flush=True)

    print("\n=================================================================", flush=True)
    print("               STRESS TEST SUITE FULLY COMPLETED                ", flush=True)
    print("=================================================================", flush=True)

if __name__ == "__main__":
    main()
