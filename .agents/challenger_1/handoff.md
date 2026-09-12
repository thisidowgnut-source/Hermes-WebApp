# Handoff Report — challenger_1: Empirical Stress Testing & Audit

**Date**: 2026-07-23  
**Target**: Hermes-WebApp Expansion Modules (`C:\Users\megat\Hermes-WebApp`)  
**Role**: EMPIRICAL CHALLENGER (`challenger_1`)  

---

## 1. Observation

### Baseline Execution (`pytest -v`)
- Command: `pytest -v`
- Result: **54 passed out of 54 tests** (100% pass rate in 63.47 seconds).
  - `tests/test_audio_api.py`: 6/6 PASSED
  - `tests/test_auth.py`: 9/9 PASSED
  - `tests/test_bot_bridge.py`: 7/7 PASSED
  - `tests/test_bridge.py`: 2/2 PASSED
  - `tests/test_queue_manager.py`: 4/4 PASSED
  - `tests/test_swarm_api.py`: 7/7 PASSED
  - `tests/test_system_api.py`: 14/14 PASSED
  - `tests/test_websockets_e2e.py`: 5/5 PASSED (Including `test_uvicorn_launcher_port_9220`)

### Empirical Stress Harness Output (`tests/stress_harness.py`)
Custom empirical stress harness executed 4 stress modules:

1. **Swarm Manager Process Spawning (`backend/services/swarm_manager.py`)**:
   - **Concurrent Spawning**: 20 subagent background processes spawned concurrently in **0.253s** (Average **12.7ms / agent**).
   - **Process States under load**: Completed = 20, Failed = 0, Running = 0. Zero lost logs or thread crashes.
   - **Concurrent Termination**: 10 running background agents terminated concurrently in **0.136s**.
   - **State Persistence**: 30 agent records serialized and verified in `.pytest_tmp/stress_swarm.json`.

2. **Voice Audio Engine Compute Throughput (`backend/services/audio_engine.py`)**:
   - **500 VAD + STEM demux FFT operations** completed in **0.500s**.
   - **Compute Throughput**: **999.5 ops/sec** (Average latency **1.000ms / chunk**).
   - **STEM Spectral Demux**: Accurately separated frequency energy into Vocals, Drums, Bass, and Other bands alongside 32-bin downsampled spectral envelope.

3. **WebSocket Rapid Connect / Disconnect Cycles**:
   - `/ws/audio`: **50/50 cycles succeeded in 0.318s** (Average **6.4ms / cycle**). Zero socket leaks or unhandled task exceptions.
   - `/ws/swarm`: **50/50 cycles succeeded in 0.365s** (Average **7.3ms / cycle**). Telemetry background broadcast loop task initialized and cancelled cleanly on disconnect without error.

4. **High-Concurrency Audio WS PCM Streaming**:
   - Streamed **200 PCM frames across 20 concurrent WebSocket clients** in **0.380s**.
   - **WebSocket Throughput**: **525.9 frames/sec**, **0 errors**.

### Discovered Vulnerability & Verbatim Log Output
During empirical execution of the stress harness, a critical defect was triggered in `SwarmManager._load_state()`:
- **Traceback**:
  ```python
  File "C:\Users\megat\Hermes-WebApp\backend\services\swarm_manager.py", line 263, in <module>
    swarm_manager = SwarmManager()
  File "C:\Users\megat\Hermes-WebApp\backend\services\swarm_manager.py", line 24, in __init__
    self._load_state()
  File "C:\Users\megat\Hermes-WebApp\backend\services\swarm_manager.py", line 44, in _load_state
    for agent_id, agent in self.agents.items():
  AttributeError: 'NoneType' object has no attribute 'items'
  ```
- **Root Cause**: In `backend/services/swarm_manager.py`, `_load_state()` opens `.queue/swarm_agents.json` and runs `self.agents = json.loads(content)`. If `.queue/swarm_agents.json` contains `"null"`, `json.loads("null")` returns `None`. `self.agents` is set to `None`, causing `self.agents.items()` on line 44 to raise an unhandled `AttributeError`, completely breaking server startup.

### Uvicorn Launch Configuration Audit (Port 9220)
- `backend/config.py` line 16: `PORT: int = int(os.getenv("PORT", 9220))`
- `.env` line 8: `PORT=9220`
- `main.py` line 7: `uvicorn.run(app, host=config.HOST, port=config.PORT)`
- `deploy/hermes_startup.vbs` line 4 & 7:
  - `python -m uvicorn main:app --host 127.0.0.1 --port 9220 --app-dir C:\Users\megat\Hermes-WebApp`
  - `cloudflared tunnel --url http://127.0.0.1:9220`
- `test_uvicorn_launcher_port_9220()` in `tests/test_websockets_e2e.py` passed cleanly.

---

## 2. Logic Chain

1. **Baseline Validity**:
   - `pytest -v` ran all 54 tests across 8 test suites. 100% of tests passed, confirming baseline REST & WebSocket functionality.

2. **Empirical Concurrency & Throughput Assessment**:
   - Swarm Manager subprocess spawning (`subprocess.Popen` with `shell=True`) handled 20 concurrent process spawns in 253ms without process orphan leaks or thread starvation.
   - Audio Engine VAD & STEM demux performed NumPy FFTs at 999.5 ops/sec (1.0ms latency/op), demonstrating high computational headroom for real-time WebAudio.
   - Rapid connect/disconnect testing (50 cycles each on `/ws/audio` and `/ws/swarm`) proved that FastAPI's `WebSocketDisconnect` catch blocks clean up connection resources without event loop pollution or memory growth.

3. **Vulnerability Analysis**:
   - **Vulnerability 1: Unhandled `NoneType` on Corrupt State File**:
     - Observation: `json.loads("null")` returns `None`. `SwarmManager._load_state()` sets `self.agents = None` and immediately calls `self.agents.items()`.
     - Risk: High. If the state file `.queue/swarm_agents.json` is corrupted or truncated to `null`, the FastAPI server crashes on startup and cannot recover without manual file deletion.
   - **Vulnerability 2: Synchronous Disk Serialization on Every Output Line**:
     - Observation: `_monitor_process()` calls `_save_state_unlocked()` inside `self._lock` on every stdout line emitted by every spawned subagent.
     - Risk: Medium. High log volume from 50+ background processes causes disk write amplification and thread lock contention.
   - **Vulnerability 3: Non-Atomic State Persistence**:
     - Observation: `_save_state_unlocked()` opens `.queue/swarm_agents.json` directly in `"w"` mode without writing to a temp file and renaming.
     - Risk: Medium. A process crash mid-write results in truncated/null JSON, triggering Vulnerability 1.

---

## 3. Caveats

- **External Network Dependency**: Telegram Bot Bridge polling (`aiogram`) requires outbound HTTPS access to `api.telegram.org`. In offline/CODE_ONLY environments, setting `TELEGRAM_BOT_TOKEN=""` during testing prevents long-polling timeout hangs.
- **Windows Process Creation Overhead**: `subprocess.Popen(command, shell=True)` on Windows spawns `cmd.exe`. While fast (12.7ms/agent), quote escaping must use double quotes `"` rather than single quotes `'` inside `-c` arguments on Windows.

---

## 4. Conclusion

The Hermes-WebApp expansion modules demonstrate **EXCELLENT core performance, high WebSocket throughput, and 100% baseline test compliance (54/54 passed)**.
- **Swarm Manager**: 20 agents spawned in 253ms (12.7ms/agent), 10 terminated in 136ms.
- **Voice Audio Engine**: 999.5 demux ops/sec (1.0ms/chunk).
- **WebSockets**: 525.9 PCM frames/sec across 20 concurrent clients with 0 errors; 50/50 rapid connect/disconnect cycles passed.
- **Uvicorn Port 9220**: Fully aligned across `.env`, `backend/config.py`, `main.py`, and `deploy/hermes_startup.vbs`.

**Actionable Mitigations Recommended**:
1. Patch `backend/services/swarm_manager.py` line 34: `self.agents = loaded if isinstance(loaded, dict) else {}` to prevent the `AttributeError: 'NoneType' object has no attribute 'items'` startup crash loop.
2. Implement atomic write (`.tmp` file + `os.replace`) in `SwarmManager._save_state_unlocked()`.

---

## 5. Verification Method

To independently verify all findings and rerun the empirical stress test harness:

1. **Run Baseline Pytest Suite**:
   ```pwsh
   pytest -v
   ```
   *Expected*: 54 passed in ~60s.

2. **Run Empirical Stress Harness**:
   ```pwsh
   python -u tests/stress_harness.py
   ```
   *Expected*: Outputs 4 completed benchmark sections (Swarm 20 agents, Audio 500 chunks, 50 WS cycles, 200 WS PCM frames) with 0 errors.

3. **Verify Discovered Crash Loop Vulnerability**:
   ```pwsh
   Set-Content -Path .queue/swarm_agents.json -Value "null"
   python -c "from backend.services.swarm_manager import swarm_manager"
   ```
   *Expected*: Reproduces `AttributeError: 'NoneType' object has no attribute 'items'`.
