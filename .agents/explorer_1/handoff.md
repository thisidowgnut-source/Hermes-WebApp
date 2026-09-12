# Soft Handoff Report — Backend Architecture & Integration Analysis

**Agent:** explorer_1  
**Target:** `C:\Users\megat\Hermes-WebApp`  
**Parent Conversation ID:** `7d599bba-3cbc-4fa8-a38d-e055d1b47786`  
**Date:** 2026-07-23  
**Handoff Type:** Soft Handoff  

---

## 1. Observation

Direct observations made during read-only investigation of `C:\Users\megat\Hermes-WebApp`:

- **Main Entrypoint Wrapper (`main.py`)**:
  - File path: `C:\Users\megat\Hermes-WebApp\main.py`
  - Lines 1-8: Imports `app` from `backend.main` and `config` from `backend.config`, runs `uvicorn.run(app, host=config.HOST, port=config.PORT)`.
- **FastAPI Core App (`backend/main.py`)**:
  - File path: `C:\Users\megat\Hermes-WebApp\backend\main.py`
  - Lines 17-38: `lifespan` context manager handles startup (`start_bot_polling()`) and shutdown (`stop_bot_polling()`) of the Telegram Bot Bridge.
  - Lines 41-47: CORS Middleware initialized using origins from `config.CORS_ORIGINS`.
  - Lines 53-55: Includes routers: `system.router`, `terminal.router`, `browser.router`.
- **System REST API Router (`backend/routers/system.py`)**:
  - File path: `C:\Users\megat\Hermes-WebApp\backend\routers\system.py`
  - Contains 12 endpoints: `GET /api/stats` (l. 31), `GET /api/stream/telemetry` (l. 46), `GET /api/queue` (l. 79), `POST /api/queue/clear` (l. 84), `DELETE /api/queue/{item_id}` (l. 89), `GET /api/files` (l. 115), `GET /api/logs` (l. 132), `GET /api/processes` (l. 150), `POST /api/kill/{pid}` (l. 166), `POST /api/macro/{macro_name}` (l. 175), `GET /api/system/obsidian-context` (l. 201), `GET /api/system/kanban` (l. 216).
- **Interactive Terminal WebSocket (`backend/websockets/terminal.py`)**:
  - Endpoint `/ws/terminal` (l. 7). Spawns subprocess `pwsh.exe -NoProfile -NoLogo` at `C:\Users\megat`. Streams stdout/stderr via `read_stdout()` and responds to text commands and ping/pong heartbeats.
- **Browser Streaming WebSocket (`backend/websockets/browser.py`)**:
  - Endpoint `/ws/browser` (l. 13). Launches Playwright Chromium (`headless=True`), streams JPEG screen frames at 5 FPS (`stream_screen()`), handles mouse clicks, key typing, keydown events, and navigation commands.
- **Security & Bot Bridge (`backend/auth.py` & `backend/bot_bridge.py`)**:
  - `auth.py`: HMAC-SHA256 calculation for Telegram `initData` signature validation. Dev mode bypasses verification if `TELEGRAM_BOT_TOKEN` is unset.
  - `bot_bridge.py`: aiogram 3.4.1 polling task forwarding user messages to n8n webhook (`N8N_WEBHOOK_URL`).
- **Existing Test Suite (`tests/test_system_api.py`)**:
  - 10 automated test functions covering `/api/stats`, `/api/queue`, `/api/stream/telemetry`, `/api/system/obsidian-context`, and `/api/system/kanban`.

---

## 2. Logic Chain

1. **Observation**: `backend/main.py` explicitly decouples application initialization from entrypoint execution in `main.py` and registers modular routers (`system.router`, `terminal.router`, `browser.router`).
   - **Reasoning**: This clean separation enables introducing new expansion feature modules (R1 Swarm Control Panel and R2 Voice Audio Stream) without altering core framework setup.

2. **Observation**: All existing REST routes (`/api/*`) are grouped cleanly under `backend/routers/system.py`, while WebSockets are isolated in `backend/websockets/`.
   - **Reasoning**: To maintain architectural integrity, R1 Swarm REST endpoints should be placed in `backend/routers/swarm.py` and R2 Voice Audio REST endpoints in `backend/routers/audio.py`. WebSockets should be placed in `backend/websockets/swarm.py` (`/ws/swarm`) and `backend/websockets/audio.py` (`/ws/audio`).

3. **Observation**: Background processes are currently managed via three patterns: `lifespan` asyncio tasks (Bot Bridge polling), per-connection WebSocket subprocesses (`pwsh.exe`), and script executions (`cleanup_tasks.py`).
   - **Reasoning**: Swarm agent processes (R1) require a dedicated background process manager (`SwarmManager` singleton in `backend/services/swarm_manager.py`) to manage asynchronous agent spawns, state persistence (`.queue/swarm_agents.json`), resource monitoring via `psutil`, and process termination.

4. **Observation**: Voice stream processing requires both continuous binary frame streaming and command action execution.
   - **Reasoning**: The `/ws/audio` endpoint must accept PCM/Opus binary frames, pass them through a VAD/Noise Gate and STEM Demux engine (`backend/services/audio_engine.py`), parse speech intent, and trigger terminal or macro execution.

---

## 3. Caveats

- **Network Mode**: Operates under CODE_ONLY network mode; no external HTTP calls were executed.
- **Read-Only Scope**: No source files in `backend/` or `main.py` were edited during this investigation pass.
- **Hardware Audio Input**: Audio streaming was evaluated conceptually based on standard PCM/Opus WebSockets and Playwright/FastAPI capabilities without live physical microphone testing.

---

## 4. Conclusion

The backend architecture of **Hermes-WebApp** is highly modular, robustly structured, and ready for expansion. Existing endpoints, WebSockets, data structures, and process management routines have been thoroughly mapped and documented in `C:\Users\megat\Hermes-WebApp\.agents\explorer_1\analysis.md`.

Concrete, non-disruptive integration paths have been designed for:
1. **Multi-Agent Swarm Control Panel API (R1)**: `backend/routers/swarm.py`, `backend/services/swarm_manager.py`, and `WS /ws/swarm`.
2. **Voice Command Terminal & STEM Audio (R2)**: `backend/routers/audio.py`, `backend/services/audio_engine.py`, and `WS /ws/audio`.

---

## 5. Verification Method

To independently verify the current findings:

1. **Verify Existing Tests Pass**:
   ```pwsh
   pytest -v tests/test_system_api.py
   ```
2. **Inspect Route Integrity**:
   Inspect `backend/main.py`, `backend/routers/system.py`, `backend/websockets/terminal.py`, and `backend/websockets/browser.py` to confirm endpoint paths and signatures.
3. **Inspect Detailed Analysis File**:
   View `C:\Users\megat\Hermes-WebApp\.agents\explorer_1\analysis.md` for schemas, REST parameters, line numbers, and architectural specifications.

---

## 6. Remaining Work (Next Phase / Implementer Handoff)

1. **Phase 1 — Swarm Control Panel (R1)**:
   - Create `backend/services/swarm_manager.py` with `SwarmManager` singleton.
   - Create `backend/routers/swarm.py` implementing `/api/swarm/agents`, `/api/swarm/spawn`, `/api/swarm/agent/{id}`, and `/api/swarm/agent/{id}/terminate`.
   - Create `backend/websockets/swarm.py` for `/ws/swarm`.
   - Register new routers in `backend/main.py`.
2. **Phase 2 — Voice Command Terminal & STEM Audio (R2)**:
   - Create `backend/services/audio_engine.py` with VAD, STEM demux filters, and Voice CLI command parser.
   - Create `backend/routers/audio.py` for `/api/audio/status` and `/api/audio/process-stem`.
   - Create `backend/websockets/audio.py` for `/ws/audio`.
   - Register new routers in `backend/main.py`.
3. **Phase 3 — Automated Test Coverage**:
   - Write `tests/test_swarm_api.py` and `tests/test_audio_api.py`.
   - Run full pytest verification suite.

---
