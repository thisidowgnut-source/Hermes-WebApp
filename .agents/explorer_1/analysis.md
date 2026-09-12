# Hermes-WebApp Backend Architecture & Integration Analysis

**Author:** explorer_1  
**Target:** `C:\Users\megat\Hermes-WebApp`  
**Date:** 2026-07-23  
**Status:** Complete (Read-Only Pass)

---

## 1. Executive Summary

This document presents a comprehensive, evidence-first investigation of the backend architecture of **Hermes-WebApp**. The system is an asynchronous Python application built on **FastAPI**, **Uvicorn**, **WebSockets**, **Playwright**, and **psutil**, featuring an Anti-AI Slop OLED Bento-box dark-mode interface and real-time system management tools.

### Key Discoveries:
1. **Entrypoint Decoupling**: Application entrypoint is cleanly decoupled into root `main.py` (compatibility wrapper) and `backend/main.py` (FastAPI core application).
2. **Modular Organization**: Endpoints are split into REST routers (`backend/routers/system.py`) and WebSocket controllers (`backend/websockets/terminal.py`, `backend/websockets/browser.py`).
3. **Telegram WebApp Security Layer**: `backend/auth.py` implements HMAC-SHA256 signature verification for `initData` with an automatic dev-mode bypass when `TELEGRAM_BOT_TOKEN` is unset.
4. **Background Tasks & Process Hygiene**: Uses FastAPI `lifespan` for async Telegram bot polling (`backend/bot_bridge.py`), `asyncio.create_subprocess_exec` for interactive PowerShell terminals, file-based atomic staging queues (`.queue/queue.json`), and `scripts/cleanup_tasks.py` for zombie process protection.
5. **Expansion Readiness**: Clear integration points exist for both **Multi-Agent Swarm Control Panel (R1)** and **Voice Command Terminal with STEM Audio (R2)** without disrupting existing routes or WebSocket handlers.

---

## 2. Codebase Architecture Overview

```
C:\Users\megat\Hermes-WebApp
├── main.py                          # Uvicorn launcher entrypoint
├── backend/
│   ├── main.py                      # FastAPI app initialization, CORS, lifespan, router mounts
│   ├── config.py                    # Environment variable loader & global settings
│   ├── auth.py                      # HMAC-SHA256 Telegram initData validation guard
│   ├── bot_bridge.py                # aiogram 3.x Telegram bot polling & n8n webhook bridge
│   ├── routers/
│   │   └── system.py                # REST endpoints (telemetry, queue, files, logs, processes, macros)
│   └── websockets/
│       ├── terminal.py              # WS /ws/terminal (interactive pwsh.exe process)
│       └── browser.py               # WS /ws/browser (Playwright headless screen stream & input)
├── scripts/
│   ├── queue_manager.py             # Atomic queue modification script
│   ├── cleanup_tasks.py             # Safe zombie process cleaner
│   └── cloudflare_webhook_updater.py# Auto Cloudflare tunnel & Telegram webhook setup
└── static/                          # HTML/CSS/JS Bento-box frontend interface
```

### Component Details:
- **`main.py` (lines 1-8)**: Simple wrapper script that imports `app` from `backend.main` and `config` from `backend.config` and runs `uvicorn.run(app, host=config.HOST, port=config.PORT)`.
- **`backend/main.py` (lines 1-64)**:
  - Defines `lifespan` context manager to manage Telegram bot polling via `start_bot_polling()` and `stop_bot_polling()`.
  - Configures `CORSMiddleware` with configurable origins (`config.CORS_ORIGINS`).
  - Mounts `/static` directory (`config.STATIC_DIR`).
  - Mounts REST routers (`system.router`) and WebSocket routers (`terminal.router`, `browser.router`).
  - Serves `static/index.html` at root `GET /`.
- **`backend/config.py` (lines 1-24)**:
  - Loads `.env` file from project root.
  - Exposes `HOST` (default `127.0.0.1`), `PORT` (default `9220`), `CORS_ORIGINS`, `TELEGRAM_BOT_TOKEN`, `BASE_DIR`, `STATIC_DIR`.
- **`backend/auth.py` (lines 1-90)**:
  - Parses `X-Telegram-Init-Data` header.
  - Verifies HMAC-SHA256 hash using secret `HMAC-SHA256(b"WebAppData", bot_token)`.
  - Exposes `telegram_auth_guard` FastAPI dependency. In dev mode (empty bot token), safely returns mock user dictionary.

---

## 3. Existing REST API Inventory

All existing REST endpoints reside in `backend/routers/system.py` and `backend/main.py`:

| Method | Route Path | Line # | Parameters / Headers | Auth Guard | Response Structure / Behavior |
|---|---|---|---|---|---|
| `GET` | `/` | `backend/main.py:57` | None | None | Serves `FileResponse` (`static/index.html`). |
| `GET` | `/api/stats` | `system.py:31` | None | Optional | `{"cpu": float, "ram": float, "disk": float, "disk_free": float}` |
| `GET` | `/api/stream/telemetry` | `system.py:46` | `limit: int = 0` | Optional | `text/event-stream` SSE yielding `data: {"cpu": float, "ram": float, "disk": float, "uptime": float}\n\n` every 1s. |
| `GET` | `/api/queue` | `system.py:79` | None | Optional | `{"status": "success", "queue": list, "count": int}` reading `.queue/queue.json`. |
| `POST` | `/api/queue/clear` | `system.py:84` | None | Optional | Overwrites `.queue/queue.json` with `[]`. Returns `{"status": "success", "msg": "Queue cleared"}`. |
| `DELETE` | `/api/queue/{item_id}` | `system.py:89` | `item_id: str` | Optional | Removes item matching index, `id` field, or string value. Returns 200 or 404. |
| `GET` | `/api/files` | `system.py:115` | `path: str = "C:\\"` | Optional | Scans directory, returns `{"path": str, "files": [{"name": str, "is_dir": bool, "path": str}]}`. |
| `GET` | `/api/logs` | `system.py:132` | None | Optional | Reads last 20 lines from `.system_generated/logs/transcript.jsonl`. Returns `{"logs": [{"role": str, "msg": str}]}`. |
| `GET` | `/api/processes` | `system.py:150` | None | Optional | Lists top 15 memory-consuming processes via `psutil.process_iter`. Returns `{"processes": [{"pid": int, "name": str, "mem": float}]}`. |
| `POST` | `/api/kill/{pid}` | `system.py:166` | `pid: int` | Optional | Terminates process PID via `psutil.Process(pid).terminate()`. Returns `{"status": "success"|"error", "msg": str}`. |
| `POST` | `/api/macro/{macro_name}` | `system.py:175` | `macro_name: str` | Optional | Executes system macros: `clean_temp`, `lock_pc`, `cleanup_zombies`, `sync_webhook`. |
| `GET` | `/api/system/obsidian-context` | `system.py:201` | None | Optional | Reads Obsidian bridge JSON context file from `OBSIDIAN_CONTEXT_BRIDGE_PATH`. |
| `GET` | `/api/system/kanban` | `system.py:216` | None | Optional | Queries SQLite DB `C:\Users\megat\.hermes\kanban.db` for cards/tasks. Returns `{"status": "success", "tables": list, "tasks": list}`. |

---

## 4. Existing WebSocket Channels Inventory

### 4.1 Terminal WebSocket (`/ws/terminal`)
- **File**: `backend/websockets/terminal.py` (lines 7-65)
- **Transport**: Standard WebSocket (`ws://` or `wss://`)
- **Process Lifecycle**:
  - Upon acceptance, launches background process `pwsh.exe -NoProfile -NoLogo` rooted at `C:\Users\megat`.
  - Spawns stdout reader `read_stdout()` and heartbeat timer `heartbeat()` (15s ping interval).
- **Message Protocol**:
  - **Inbound Text**:
    - `"ping"` or `{"type": "ping"}` → Server responds `{"type": "pong"}`.
    - Command string (e.g. `dir\n`, `git status`) → Written directly to `process.stdin` + `\n`.
  - **Outbound Text**:
    - Raw terminal stdout/stderr string decoded in UTF-8.
    - JSON Heartbeat: `{"type": "ping"}`.
- **Cleanup**: Cancels background tasks, terminates process (`pwsh.exe`) gracefully with 2.0s timeout before `kill()`.

### 4.2 Browser Streaming WebSocket (`/ws/browser`)
- **File**: `backend/websockets/browser.py` (lines 13-125)
- **Transport**: Standard WebSocket
- **Process Lifecycle**:
  - Starts Playwright Chromium headless browser instance (`headless=True`, viewport 1024x768).
  - Navigates to initial page (`https://google.com`).
  - Spawns screen streamer `stream_screen()` (JPEG quality 40 at 5 FPS) and heartbeat task (15s).
- **Message Protocol**:
  - **Inbound JSON**:
    - `{"type": "click", "x": 100, "y": 200}` → `browser_page.mouse.click(x, y)`
    - `{"type": "type", "text": "hello"}` → `browser_page.keyboard.type(text)`
    - `{"type": "keydown", "key": "Enter"}` → `browser_page.keyboard.press(key)`
    - `{"type": "goto", "url": "https://example.com"}` → `browser_page.goto(url)`
  - **Outbound JSON**:
    - Screen frame: `{"type": "frame", "data": "<base64_jpeg_string>"}`
    - Error message: `{"type": "error", "msg": "<error_text>"}`
    - Ping/Pong frames.
- **Cleanup**: Closes page, context, browser, and stops Playwright instance in `finally` block.

---

## 5. Background Tasks & Process Management

1. **Lifespan Task Management**:
   - `backend/main.py` uses `asynccontextmanager` lifespan to start `start_bot_polling()` as an `asyncio.Task` running `aiogram` Telegram bot polling.
2. **Subprocess Management**:
   - WebSockets spawn long-running child processes (`pwsh.exe`, `playwright` chromium).
   - Macros trigger `os.system` process calls (`python scripts/cleanup_tasks.py`).
3. **Queue File Management**:
   - Atomic read/write functions `_read_queue()` and `_write_queue()` operate on `.queue/queue.json`. `scripts/queue_manager.py` handles optional git commit staging updates.
4. **Zombie Cleanup Utility**:
   - `scripts/cleanup_tasks.py` safeguards system memory by detecting orphan `task-*.log` task wrappers and `pwsh.exe` zombie shells while protecting the project pipeline (`PROJECT_PATHS`).

---

## 6. Integration Design: Multi-Agent Swarm Control Panel API (R1)

### 6.1 Proposed Architecture & File Layout
To maintain strict modularity, R1 will introduce:
- `backend/services/swarm_manager.py`: Core singleton managing background agent lifecycle, state tracking, worktrees, and log capturing.
- `backend/routers/swarm.py`: REST API endpoints for agent control.
- `backend/websockets/swarm.py`: Real-time WebSocket channel (`/ws/swarm`) broadcasting swarm state updates and log streams.

```
backend/
├── services/
│   └── swarm_manager.py     # SwarmManager singleton & Process Manager
├── routers/
│   └── swarm.py             # Swarm REST Router (/api/swarm/*)
└── websockets/
    └── swarm.py             # WebSocket /ws/swarm
```

### 6.2 Data Schemas & Models (`swarm.py`)
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class SwarmAgentSpawnRequest(BaseModel):
    name: str = Field(..., description="Agent name, e.g. explorer_2")
    role: str = Field(..., description="Agent role: explorer, implementer, reviewer, orchestrator")
    task_prompt: str = Field(..., description="Full task instruction prompt")
    worktree_dir: Optional[str] = Field(None, description="Target working directory or worktree path")
    env_vars: Optional[Dict[str, str]] = Field(default_factory=dict)

class SwarmAgentStatus(BaseModel):
    agent_id: str
    name: str
    role: str
    status: str # "queued" | "running" | "completed" | "failed" | "terminated"
    pid: Optional[int] = None
    cwd: str
    created_at: float
    finished_at: Optional[float] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    last_log_line: str = ""
    log_file_path: str
```

### 6.3 REST Endpoints to Implement (`backend/routers/swarm.py`)

| Method | Endpoint Path | Description | Payload / Response |
|---|---|---|---|
| `GET` | `/api/swarm/agents` | List all tracked swarm agents | `{"status": "success", "agents": [SwarmAgentStatus], "total": int}` |
| `POST` | `/api/swarm/spawn` | Spawn a parallel background agent | Request: `SwarmAgentSpawnRequest` → Returns: `{"status": "success", "agent": SwarmAgentStatus}` |
| `GET` | `/api/swarm/agent/{agent_id}` | Detailed agent metadata & logs | Returns: `{"agent": SwarmAgentStatus, "logs": [str]}` |
| `POST` | `/api/swarm/agent/{agent_id}/delegate` | Send message/input to agent | Request: `{"message": str}` → Returns status |
| `POST` | `/api/swarm/agent/{agent_id}/terminate` | Force stop/kill background agent | Returns: `{"status": "success", "msg": f"Agent {agent_id} terminated"}` |

### 6.4 Swarm WebSocket (`/ws/swarm`)
- **Broadcast Data**: Periodic JSON payload (every 1s) with active agents list, CPU/RAM utilization per agent, and recent log outputs.
- **Client Commands**:
  - `{"action": "subscribe", "agent_id": "xxx"}`: Focus log streaming on a specific agent.
  - `{"action": "kill", "agent_id": "xxx"}`: Immediately terminate specified agent.

---

## 7. Integration Design: Voice Command Terminal & STEM Audio Engine (R2)

### 7.1 Proposed Architecture & File Layout
For real-time audio streaming, speech recognition, STEM separation, and Voice CLI command execution:
- `backend/services/audio_engine.py`: Audio stream processor, VAD/Speech-to-Text parser, STEM demux handler.
- `backend/routers/audio.py`: REST API for offline audio uploads, STEM track extraction, and engine status.
- `backend/websockets/audio.py`: Real-time bidirectional WebSocket (`/ws/audio`).

```
backend/
├── services/
│   └── audio_engine.py      # STEM processing engine & Voice CLI parser
├── routers/
│   └── audio.py             # Audio REST endpoints (/api/audio/*)
└── websockets/
    └── audio.py             # WebSocket /ws/audio (Audio streaming & commands)
```

### 7.2 Real-Time Audio WebSocket Protocol (`/ws/audio`)
- **Transport**: Supports both Binary (PCM / Opus audio chunk buffers) and Text (JSON control & transcript frames).
- **Client → Server Frame Format**:
  - **Binary Frame**: Raw 16kHz 16-bit Mono PCM audio bytes or WebM opus chunk.
  - **Text JSON Frame**:
    - `{"action": "start"}`: Initialize audio session & buffers.
    - `{"action": "stop"}`: Flush buffer, finalize recognition & STEM processing.
    - `{"action": "set_stem_mode", "mode": "vocal_isolation"}`: Set STEM audio filter mode.
- **Server → Client Frame Format (JSON)**:
  - **Transcript Event**: `{"type": "transcript", "text": "show system status", "is_final": true, "confidence": 0.96}`
  - **Voice CLI Command Event**: `{"type": "voice_command", "intent": "macro_run", "command": "clean_temp", "executed": true}`
  - **STEM Telemetry Event**: `{"type": "stem_metrics", "vocal_energy": 0.82, "noise_floor": -45.2, "active_track": "vocals"}`
  - **Audio Output Feedback**: Base64 encoded audio response chunk (for text-to-speech feedback).

### 7.3 STEM Audio Processing Engine Capabilities (`audio_engine.py`)
1. **Real-time Noise Gate & Bandpass Filter**: Removes background hiss and electrical noise from incoming mic frames.
2. **STEM Track Demux / Separation**: Splits mixed audio into Vocals, Music, and Background Noise channels using standard digital signal processing (DSP) filters or lightweight ML classifiers.
3. **Voice CLI Navigation Engine**: Maps transcribed text to system commands:
   - *"open terminal"* / *"list files"* → Dispatches to Terminal WS or returns file system structure.
   - *"clean temp"* / *"lock pc"* → Triggers `/api/macro/clean_temp` or `lock_pc`.
   - *"kill process 1234"* → Triggers process termination.

### 7.4 REST Endpoints to Implement (`backend/routers/audio.py`)

| Method | Endpoint Path | Description | Response / Payload |
|---|---|---|---|
| `GET` | `/api/audio/status` | Audio processing engine status check | `{"status": "ready", "stem_enabled": true, "vad_active": true}` |
| `POST` | `/api/audio/process-stem` | Upload audio file for offline STEM demux | Request: Multipart `file` → Returns URLs/data for separated tracks (Vocals/Noise/Background) |
| `POST` | `/api/audio/voice-command` | Process single audio clip to Voice CLI command | Request: Audio file → Returns executed command & transcript |

---

## 8. Verification Strategy & Next Steps

1. **System Health Verification**:
   - Run `pytest -v` to ensure existing 10 test cases in `tests/test_system_api.py` pass cleanly.
   - Verify server launches on Uvicorn port 9220 without warnings.
2. **Swarm Module (R1) Verification**:
   - Unit test `SwarmManager` process creation and state tracking.
   - Test REST endpoints `/api/swarm/agents` and `/api/swarm/spawn` with `TestClient`.
   - Verify WebSocket `/ws/swarm` broadcasts json frame events.
3. **Voice & STEM Audio (R2) Verification**:
   - Test audio frame decoding and transcript signal output in `/ws/audio`.
   - Verify STEM separation filters on sample audio inputs.
   - Test Voice CLI parser mapping to system macro calls.

---

*End of Analysis Report.*
