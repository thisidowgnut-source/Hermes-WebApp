# Project: Hermes OS WebApp — Telegram Mini App for Unlimited Remote PC Control

> **Mission**: Transform Telegram into a full-featured command center for your PC — real terminal, remote browser, AI agent swarm, human-in-the-loop, all from your phone.

---

## Architecture Overview

Hermes-WebApp is a **FastAPI + WebSocket** backend serving an **OLED Bento-box** Telegram Mini App. It bridges mobile ↔ PC via Cloudflare Tunnel, providing unrestricted OS access beyond Telegram Bot API limits.

```
Telegram Mini App ◄──HTTPS──► Cloudflare Tunnel ◄──HTTP──► FastAPI (9220) ◄──WS──► Host OS
                                                              │
                    ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
                    ▼                                         ▼                                         ▼
             ┌─────────────┐                          ┌─────────────┐                          ┌─────────────┐
             │  REST API   │                          │  WebSockets │                          │  Services   │
             │  /api/*     │                          │  /ws/*      │                          │  (background)│
             └─────────────┘                          └─────────────┘                          └─────────────┘
```

---

## Module Breakdown

### 1. Core System & Infrastructure (Foundation)
| File | Purpose |
|------|---------|
| `main.py` | Entry point with port fallback (9220→9230→9225→9255→9290→8080) |
| `backend/main.py` | FastAPI app, lifespan, CORS, static files, router registration |
| `backend/config.py` | Pydantic Settings from `.env` (HOST, PORT, TOKEN, CORS) |
| `backend/observability.py` | **Structured logging, Prometheus metrics, Telegram alerting** |
| `backend/bot_bridge.py` | Outbound-only Telegram messaging (no polling — split-token arch) |

### 2. System REST API (`backend/routers/system.py`)
| Endpoint | Description |
|----------|-------------|
| `GET /health` | **Health check for orchestration** |
| `GET /metrics` | **Prometheus-format metrics** |
| `GET /api/stats` | CPU, RAM, Disk, Uptime |
| `GET /api/stream/telemetry` | SSE stream (1Hz) |
| `GET /api/processes` | Top 15 processes by memory |
| `POST /api/kill/{pid}` | Terminate process |
| `POST /api/macro/{name}` | Macros: clean_temp, lock_pc, cleanup_zombies, sync_webhook |
| `GET/POST /api/files` | Directory listing, read (≤2MB), write with backup |
| `GET /api/logs` | Agent transcript logs |
| `GET /api/system/*` | Obsidian, Kanban, Network scan, Threat scan, Env info, Services, FIM, Firewall, Event logs |
| `POST /api/system/send-alert` | Telegram alert dispatch |

### 3. Multi-Agent Swarm Control Panel (R1) ✅
| Component | Purpose |
|-----------|---------|
| `backend/services/swarm_manager.py` | Agent lifecycle: spawn, terminate, telemetry, logs, stdin commands |
| `backend/routers/swarm.py` | REST: list, spawn, details, terminate, logs |
| `backend/websockets/swarm.py` | **Enhanced WS**: broadcast telemetry + system snapshot, agent commands, event subscriptions |
| Frontend | `#swarm-bento-card` + `#mod-swarm` full-screen overlay (Dock index 6) |

**WS Protocol**: `init` → `telemetry` (2s) + `agent_spawned`/`agent_terminated`/`agent_logs`/`agent_details`/`command_sent`

### 4. Voice Command Terminal & STEM Audio Stream (R2) ✅
| Component | Purpose |
|-----------|---------|
| `backend/services/audio_engine.py` | VAD, STEM demux (Vocals/Drums/Bass/Other), Voice CLI parser |
| `backend/routers/audio.py` | REST: status, process-stem |
| `backend/websockets/audio.py` | WS: PCM streaming, transcripts, voice commands |
| Frontend | `#voice-toggle-badge` + `#mod-audio` spectrum visualizer (Dock index 7) |

### 5. **Human-in-the-Loop (HITL) — NEW (R4)** ✅
| Component | Purpose |
|-----------|---------|
| `backend/websockets/hitl.py` | WS `/ws/hitl`: agent requests → human responses |
| HTTP `/api/hitl/request` | Non-WS agent HITL requests |
| Protocol | Agent blocks on `request_human_intervention()` until Mini App response |

**Reasons**: `captcha`, `2fa`, `consent`, `ambiguous`, `approval`

### 6. Hermes Vision — Remote Browser (Core) ✅
| Component | Purpose |
|-----------|---------|
| `backend/websockets/browser.py` | Playwright Chromium: frame streaming (JPEG/base64), click, type, keydown, goto |
| Frontend | `#browser-bento-card` + `#mod-browser` full-screen overlay |

### 6. Remote Terminal (Core) ✅
| Component | Purpose |
|-----------|---------|
| `backend/websockets/terminal.py` | `pwsh.exe` stdin/stdout/stderr over WS, ANSI via xterm.js |
| Frontend | `#terminal-bento-card` + `#mod-terminal` full-screen overlay |

### 7. Security & Forensics Suite
| Feature | Endpoints |
|---------|-----------|
| Threat Scan | `GET /api/system/threat-scan` — heuristic detection (miners, RATs, etc.) |
| FIM (File Integrity) | `POST /api/forensics/fim/baseline`, `GET /api/forensics/fim/scan` |
| Firewall Rules | `GET/POST /api/forensics/firewall/rules`, `POST /api/forensics/firewall/rule` |
| Event Logs | `GET /api/forensics/event-logs` — Windows Security logs |

### 8. Workflow Engine & Scheduler
| Feature | Endpoints |
|---------|-----------|
| Cron/Interval Tasks | `POST /api/workflow/task/schedule`, `GET /api/workflow/tasks`, `POST /api/workflow/task/{id}/cancel` |
| DAG Visualization | `GET /api/workflow/dag` |
| Obsidian Graph/Search | `GET /api/obsidian/graph`, `POST /api/obsidian/search` |

---

## Milestones

| # | Name | Scope | Status |
|---|------|-------|--------|
| M1 | Exploration & Baseline Audit | Read-only analysis | ✅ DONE |
| M2 | Specification & Test Infra | PROJECT.md, TEST_INFRA.md, contracts | ✅ DONE |
| M3 | Multi-Agent Swarm (R1) | Swarm manager, REST, WS, OLED UI | ✅ DONE |
| M4 | Voice & STEM Audio (R2) | Audio engine, WS, visualizer | ✅ DONE |
| M3 | Systems Health & Tests (R3) | Full test suite, WS E2E, Forensic audit | ✅ DONE |
| **M6** | **HITL Protocol (R4)** | **WS hitl, agent blocking, Mini App UI** | ✅ **DONE** |
| **M7** | **Observability & Hardening** | **Structured logging, metrics, Telegram alerts, health check, service configs, encrypted config** | ✅ **DONE** |
| **M8** | **Telegram Polish** | **PWA manifest, icons, Menu Button setup, splash screens** | ✅ **DONE** |

---

## Interface Contracts

### Swarm WebSocket (`/ws/swarm`)
**Client → Server:**
```json
{"type": "spawn", "name": "...", "task": "...", "command": "...", "model": "gpt-4"}
{"type": "terminate", "agent_id": "..."}
{"type": "get_agent_logs", "agent_id": "...", "lines": 100}
{"type": "get_agent_details", "agent_id": "..."}
{"type": "send_command", "agent_id": "...", "command": "ls\n"}
{"type": "subscribe_events", "events": ["telemetry", "agent_status", "agent_log"]}
```

**Server → Client:**
```json
{"type": "init", "telemetry": {...}, "system": {...}, "timestamp": 123}
{"type": "telemetry", "telemetry": {...}, "system": {...}, "timestamp": 123}
{"type": "agent_spawned", "agent": {...}, "timestamp": 123}
{"type": "agent_terminated", "agent_id": "...", "result": {...}, "timestamp": 123}
{"type": "agent_logs", "agent_id": "...", "logs": [...], "timestamp": 123}
```

### HITL WebSocket (`/ws/hitl`)
**Server → Client (broadcast):**
```json
{"type": "hitl_request", "session_id": "...", "agent_name": "...", "reason": "captcha", "context": {...}, "priority": "high", "timeout": 300}
```

**Client → Server:**
```json
{"type": "hitl_response", "session_id": "...", "action": "continue|abort|retry|custom", "payload": {...}}
```

### Terminal WebSocket (`/ws/terminal`)
- **Client → Server**: Raw keystrokes (`\r` = Enter, `\x03` = Ctrl+C)
- **Server → Client**: Raw stdout/stderr (ANSI sequences)
- **Heartbeat**: Binary ping frame (`\x09`) every 15s

### Browser WebSocket (`/ws/browser`)
- **Commands**: `click`, `type`, `keydown`, `goto`
- **Stream**: `{"type": "frame", "data": "base64jpeg"}` @ ~5 FPS

---

## Code Layout

```
Hermes-WebApp/
├── main.py                          # Port-fallback launcher
├── backend/
│   ├── main.py                      # FastAPI + lifespan + routers
│   ├── config.py                    # Settings from .env
│   ├── observability.py             # Logging, metrics, Telegram alerts
│   ├── bot_bridge.py                # Outbound Telegram
│   ├── routers/
│   │   ├── system.py                # Core + forensics + workflow
│   │   ├── swarm.py                 # Swarm REST
│   │   └── audio.py                 # Audio REST
│   ├── services/
│   │   ├── swarm_manager.py         # Agent lifecycle
│   │   └── audio_engine.py          # VAD + STEM + Voice CLI
│   └── websockets/
│       ├── terminal.py              # pwsh.exe WS
│       ├── browser.py               # Playwright WS
│       ├── swarm.py                 # Enhanced telemetry WS
│       ├── audio.py                 # PCM + transcript WS
│       └── hitl.py                  # HITL WS
├── static/
│   ├── index.html                   # Mini App SPA
│   ├── manifest.json                # PWA manifest
│   └── icons/                       # 72–512px + shortcuts + splashes
├── scripts/
│   ├── setup_telegram_menu.py       # Bot Menu Button config
│   ├── generate_icons.py            # Icon generator
│   ├── encrypt_config.py            # age encryption for .env
│   ├── queue_manager.py             # Shared-state queue
│   └── aiogram_bridge.py            # Bot-loop prevention
├── deploy/
│   ├── hermes-webapp.service        # systemd (Linux/WSL2)
│   └── Install-HermesWebAppService.ps1  # NSSM (Windows)
├── tests/
│   ├── test_system_api.py           # Core REST tests
│   ├── test_swarm_api.py            # Swarm REST + WS tests
│   ├── test_audio_api.py            # Audio REST + WS tests
│   └── test_websockets_e2e.py       # E2E connectivity
├── docs/
│   ├── AGENTS.md                    # Agent directives
│   ├── DESIGNS.md                   # Anti-AI Slop UI spec
│   ├── PROJECT.md                   # This file
│   └── TEST_INFRA.md                # Test infrastructure
└── design-system/hermes-webapp/
    ├── MASTER.md                    # Design tokens
    └── pages/                       # Page overrides
```

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Split-Token Architecture** | Gateway polls inbound; WebApp only sends outbound → zero 409 conflicts |
| **WebSocket over HTTP** | Real-time streaming (terminal, browser, telemetry) impossible with Bot API |
| **Cloudflare Tunnel** | No port forwarding, free HTTPS, DDoS protection |
| **age encryption** | Modern, simple, auditable `.env` encryption |
| **JetBrains Mono** | Monospace = terminal aesthetic, code-readable, OLED-friendly |
| **Structured JSON logging** | evlog-style wide events for analysis |
| **Prometheus metrics** | Standard scraping, Grafana-ready |

---

*This document reflects the current architecture as of the hardening & polish phase. Update when modules evolve.*