# Hermes-WebApp Complete Codebase Review
**Date:** 2026-07-27  
**Profile:** default | Model: nvidia/nemotron-3-ultra-550b-a55b (NVIDIA NIM)  
**Target:** `C:\Users\megat\Hermes-WebApp`  
**Scope:** Full folder + file audit — architecture, security, code quality, testing, ops

---

## 1. Executive Summary

| Dimension | Score | Verdict |
|-----------|-------|---------|
| **Architecture** | 6/10 | Modular FastAPI + WebSockets + Playwright + Swarm + Audio — good separation, but `main.py` (old) vs `backend/main.py` (new) split is confusing |
| **Security** | 3/10 | **CRITICAL**: No Telegram `initData` auth, CORS `*` + credentials, plain token file (`.env` exists but not used everywhere), `kill` endpoint open, shell access via WebSocket |
| **Code Quality** | 6/10 | Services are clean (swarm_manager, audio_engine). Routers OK. WebSockets have cleanup issues. Frontend is a 200KB single-file monolith (`static/index.html`) |
| **Testing** | 5/10 | 4 test files, mostly contract tests. No e2e for browser/terminal WebSockets with real Playwright. Coverage unknown (no pytest-cov). |
| **Operations** | 5/10 | Cloudflare tunnel + VBS startup scripts. No Docker, no compose, no requirements.txt/pyproject.toml. Port fallback logic in `main.py` (9220→9230→9225…). |
| **Frontend/UX** | 7/10 | Premium OLED bento-box design, glassmorphism, dock, particles. But: single 59KB HTML file, all 14 overlays render on load, accessibility gaps (P0 items in TODO.md) |
| **Documentation** | 8/10 | Excellent docs folder (PRD, ARCH, SECURITY, AGENTS, DESIGNS, SKILLS, DEPLOYMENT, API, TROUBLESHOOTING) — but SECURITY.md describes auth that doesn't exist |

**Overall: 5.6/10** — **Functional prototype with critical security gaps and architectural debt. Not production-ready for exposed tunnel.**

---

## 2. Architecture Map

```
Hermes-WebApp/
├── main.py                          # Legacy launcher (port fallback 9220→9230→9225…)
├── backend/
│   ├── main.py                      # FastAPI app + lifespan (bot bridge, routers, WS)
│   ├── config.py                    # Config via .env (CORS, port, token, paths)
│   ├── routers/
│   │   ├── system.py                # 32 endpoints: stats, queue, files, processes, kill, macros, logs, obsidian, kanban, swarm-status, network, threat-scan, env, files R/W, services
│   │   ├── swarm.py                 # 4 REST endpoints: /agents, /spawn, /agent/{id}, /agent/{id}/terminate
│   │   └── audio.py                 # 5 REST endpoints: /status, /process-stem, /vad-threshold, /parse-command
│   ├── services/
│   │   ├── swarm_manager.py         # Singleton: spawn/terminate/monitor agents, JSON persistence (.queue/swarm_agents.json)
│   │   └── audio_engine.py          # VAD (RMS), STEM demux (FFT bands), Voice CLI intent parser (keyword rules)
│   └── websockets/
│       ├── terminal.py              # /ws/terminal → pwsh.exe subprocess (ANSI via xterm.js)
│       ├── browser.py               # /ws/browser → Playwright Chromium JPEG stream (5 FPS) + click/type/goto
│       ├── swarm.py                 # /ws/swarm → 2s telemetry broadcast + spawn via WS
│       └── audio.py                 # /ws/audio → binary PCM → VAD + STEM + intent → JSON frames
├── static/
│   └── index.html                   # 59KB / 4088 lines — single-file SPA (Tailwind CDN, Lucide, xterm.js, canvas particles)
├── scripts/
│   ├── aiogram_bridge.py            # Telegram bot ↔ n8n webhook (port 9221), bot-to-bot loop prevention
│   ├── queue_manager.py             # JSON queue + git auto-commit
│   ├── cloudflare_webhook_updater.py
│   ├── n8n_telegram_hitl.py
│   └── cleanup_tasks.py
├── tests/
│   ├── test_system_api.py           # 8 tests (stats, queue CRUD, telemetry SSE, obsidian, kanban)
│   ├── test_swarm_api.py            # 6 tests (REST + WS + defensive load)
│   ├── test_audio_api.py            # (exists, not read)
│   └── test_websockets_e2e.py       # 5 WS tests (terminal, browser, audio, swarm, uvicorn launch)
├── docs/                            # 11 markdown specs
├── .env.example                     # Template (token, host, port, CORS)
├── .env                             # Actual config (gitignored)
├── deploy/                          # VBS + BAT startup scripts
└── .superpowers/                    # Opus/Superpowers agent artifacts (ignore)
```

---

## 3. Critical Findings (P0 — Fix Before Exposing Tunnel)

### 3.1 No Telegram WebApp Auth (CRITICAL)
**Files:** `backend/main.py`, `backend/routers/system.py`, `backend/websockets/*.py`  
**Evidence:** `SECURITY.md` lines 14-18 mandate `initData` verification on *every* HTTP/WS request. **Implementation: ZERO.**  
**Risk:** Anyone with the Cloudflare URL gets full shell (`/ws/terminal`), process kill, file R/W, browser control, macro execution.  
**Fix:** Add `backend/auth.py` middleware — verify `X-Telegram-Init-Data` header against `TELEGRAM_BOT_TOKEN` (HMAC-SHA256). Reject with 401. Apply to all routers + WebSocket `accept()` guards.

### 3.2 CORS Misconfiguration (CRITICAL)
**File:** `backend/config.py` line 10-12, `backend/main.py` line 41-47  
**Current:** `CORS_ORIGINS="*"` + `ALLOW_CREDENTIALS=True`  
**Risk:** Any origin can send credentials (cookies/auth headers) to your API.  
**Fix:** `CORS_ORIGINS="https://<your-tunnel>.trycloudflare.com"` (single origin) OR set `ALLOW_CREDENTIALS=False` if auth is header-based.

### 3.3 Browser WebSocket Memory Leak (CRITICAL)
**File:** `backend/websockets/browser.py` lines 9-11, 24-30, 94-128  
**Issue:** Global `browser_context`, `browser_page` — **new Playwright launch per connection** (line 25). Cleanup in `finally` block but `stream_task.cancel()` may not await fully; browser process can orphan.  
**Fix:** Singleton browser pool (1 browser, N contexts) OR strict per-connection lifecycle with `asyncio.wait_for(timeout=5)` on cleanup. Add `browser_page.close()` + `browser_context.close()` + `browser.close()` + `playwright.stop()` in `try/finally` with timeouts.

### 3.4 Plain Token Storage
**File:** `.env` (exists, gitignored) but `scripts/aiogram_bridge.py` line 12 has hardcoded placeholder token.  
**Risk:** Token in code history.  
**Fix:** Ensure `.env` in `.gitignore`. Rotate bot token. Use `config.TELEGRAM_BOT_TOKEN` everywhere.

### 3.5 Kill Endpoint No Auth
**File:** `backend/routers/system.py` line 171-178  
**Endpoint:** `POST /api/kill/{pid}` — kills any PID accessible to the process user.  
**Fix:** Guard with auth middleware. Optionally verify PID belongs to same user session.

---

## 4. High-Priority Issues (P1)

| # | Issue | File/Location | Impact |
|---|-------|---------------|--------|
| 1 | **Shell injection risk in macros** | `system.py:183-194` (`os.system` with string interpolation) | Command injection if macro name controlled |
| 2 | **File R/W endpoints path traversal** | `system.py:416-463` — `os.path.abspath` but no chroot/jail | Read/write arbitrary files on host |
| 3 | **WebSocket no origin check** | All WS handlers accept without `Origin` header validation | CSRF-style WS hijacking |
| 4 | **Playwright no sandbox / headless only** | `browser.py:25` — `headless=True` but no `--no-sandbox` flags documented | If host is Linux, may fail; Windows OK but no isolation |
| 5 | **Audio engine: numpy FFT on every frame** | `audio_engine.py:130-188` — heavy for 16kHz real-time | CPU spike under load; consider WebAudio API client-side |
| 6 | **Swarm manager: shell=True subprocess** | `swarm_manager.py:89` — `subprocess.Popen(command, shell=True)` | Injection if `command` user-controlled (spawn WS accepts `command`) |
| 7 | **No requirements.txt / pyproject.toml** | Root — manual `pip install` in README | Non-reproducible builds |
| 8 | **Port fallback confusion** | `main.py` tries 9220→9230→9225→9255→9290→8080 | Cloudflare tunnel expects fixed port; race condition if multiple instances |

---

## 5. Code Quality & Maintainability

### 5.1 Strengths
- **Service layer clean**: `swarm_manager.py` (singleton, thread-safe, JSON persistence, psutil metrics), `audio_engine.py` (DSP logic separated, testable)
- **Router separation**: system / swarm / audio — good REST boundaries
- **WebSocket contracts**: Consistent ping/pong, JSON message types, telemetry broadcast pattern
- **Test fixtures**: `test_system_api.py` properly backs up/restores queue file
- **Documentation depth**: 11 specs in `docs/` — rare for prototype

### 5.2 Debt
| Area | Problem |
|------|---------|
| **Frontend monolith** | `static/index.html` = 4088 lines (CSS + JS + HTML). 14 module overlays all rendered on load (TODO.md P0#1). No build step, no modules, no TypeScript. |
| **Legacy `main.py` vs `backend/main.py`** | Two entrypoints. `main.py` (root) is old monolithic version with browser WS inline. `backend/main.py` is new modular. Which runs? `deploy/hermes_startup.vbs` calls `main.py`. |
| **Config hardcoded paths** | `system.py:136-138` — Obsidian log path hardcoded to `C:\Users\megat\.gemini\...`. `kanban.db` path hardcoded. |
| **Duplicate queue logic** | `system.py:_read_queue/_write_queue` vs `scripts/queue_manager.py:add_to_queue` — same JSON file, different code. |
| **No dependency lock** | `requirements.txt` exists (1 line: `fastapi uvicorn websockets playwright psutil`) — **unpinned**. |
| **Audio engine stubs** | `detect_vad` / `process_stem` use numpy FFT — no real STEM separation (needs `demucs`/`spleeter` or WebAssembly). Voice intent parser = keyword matching only. |

---

## 6. Testing Gap Analysis

| Test File | Coverage | Missing |
|-----------|----------|---------|
| `test_system_api.py` | REST: stats, queue, telemetry SSE, obsidian, kanban | `/api/kill`, `/api/macro`, `/api/files/*`, `/api/processes`, `/api/logs`, `/api/system/services`, threat-scan, network-scan |
| `test_swarm_api.py` | REST + WS + defensive load | Process metrics accuracy, termination race conditions |
| `test_audio_api.py` | (not read) | VAD threshold edge cases, STEM output validation, intent parser coverage |
| `test_websockets_e2e.py` | Contract tests (TestClient) — **no real Playwright/browser**, no real `pwsh.exe` | Real browser frame stream, real terminal ANSI, audio binary frames, concurrent WS load |

**No:** `pytest.ini` only has `asyncio_mode = auto`. No `pytest-cov`, no `pytest-xdist`, no CI workflow.

---

## 7. Operations & Deployment

| Component | Status | Notes |
|-----------|--------|-------|
| **Process manager** | VBS script (`deploy/hermes_startup.vbs`) → `main.py` | No systemd/supervisor/pm2. No health check endpoint (`/health` missing). |
| **Tunnel** | Cloudflare `trycloudflare.com` (ephemeral) | URL changes on restart — breaks Telegram Menu Button. Need fixed tunnel (cloudflared service + config.yml). |
| **Bot bridge** | `scripts/aiogram_bridge.py` port 9221 | Separate process. No supervision. |
| **Logs** | `main.log`, `cloudflared.log` in root | No rotation, no structured logging (JSON). |
| **Secrets** | `.env` (gitignored) | Good. But `aiogram_bridge.py` has hardcoded placeholder. |
| **Dependencies** | Manual `pip install` + `playwright install` | No `requirements.txt` with pins. No `uv`/`poetry`. |

---

## 8. Frontend (static/index.html) — Detailed

**Size:** 204 KB / 4088 lines  
**Architecture:** Single-file SPA, vanilla JS, Tailwind CDN, Lucide CDN, xterm.js CDN

### Good
- OLED black (#000) + zinc palette, Inter font, glassmorphism, bento grid
- Dock (macOS-style) with 8 modules: Home, Monitor, Terminal, Swarm, Files, Browser, Kanban, Audio, Security, Workflow, Obsidian, Settings
- Command Palette (Cmd+K), particle background canvas, ring gauges
- Anti-AI-Slop protocol: no emojis, no placeholder text, no generic gradients

### Bad (from TODO.md + audit)
| P0 Blockers | P1 High |
|-------------|---------|
| All 14 overlays render on load (`visibility` not toggled) | No keyboard navigation for cards/rows |
| `btn.removeAttribute('onclick')` patch breaks handlers | Form labels missing, placeholders `...` not `…` |
| Extra `</div>` in Services/Workflow modules (invalid HTML) | No focus trap in modals, Escape doesn't close |
| `maximum-scale=1, user-scalable=no` (accessibility fail) | No `aria-live` on toasts/logs, no retry on WS fail |
| Telegram `requestFullscreen()` throws on old WebApp | Duplicate `BackButton.onClick` / `MainButton.onClick` registrations |

### Structural Debt
- **No CSS/JS splitting** — 59KB inline styles + 140KB inline JS
- **No design tokens** — colors/spacing duplicated
- **No CSP / integrity** on CDN assets
- **CDN reliance** — offline = broken

---

## 9. Recommended Action Plan

### Phase 0 — Security Lockdown (Do First, < 2 hrs)
```bash
# 1. Add auth middleware
# backend/auth.py — verify Telegram initData HMAC
# 2. Apply to all routers + WS
# 3. Fix CORS
CORS_ORIGINS="https://<fixed-tunnel>.trycloudflare.com"
ALLOW_CREDENTIALS=False
# 4. Rotate bot token, remove hardcoded from aiogram_bridge.py
# 5. Add origin check on WS accept()
# 6. Sandbox kill/files endpoints behind auth
```

### Phase 1 — Architecture Cleanup (1-2 days)
1. **Delete root `main.py`** — use only `backend/main.py` (modular). Update VBS startup.
2. **Create `requirements.txt` pinned** + `pyproject.toml` with `[build-system]`, `[tool.pytest]`.
3. **Extract browser WS to singleton pool** — one Playwright process, multiple contexts.
4. **Consolidate queue logic** — single `QueueManager` class used by both router and script.
5. **Add `/health` endpoint** (liveness + readiness: check browser pool, DB, token).

### Phase 2 — Frontend Modularization (2-3 days)
1. Split `static/index.html` → `static/css/`, `static/js/modules/`, `static/index.html` (shell only)
2. Implement module lazy-load (dynamic `import()`) — only load overlay JS when dock item clicked
3. Fix P0/P1 items from TODO.md
4. Add `@media (prefers-reduced-motion)` and CSP headers

### Phase 3 — Testing & Reliability (1-2 days)
1. Add `pytest-cov`, target >80% on services/routers
2. Real Playwright e2e test (headless CI) for browser WS
3. Real terminal test with `pexpect` or `pty`
4. GitHub Actions workflow: lint → test → build frontend (if step 2 done)

### Phase 4 — Operational Hardening (ongoing)
1. Fixed Cloudflare tunnel (named tunnel + `config.yml`)
2. Systemd/pm2 service files for `backend/main.py` + `aiogram_bridge.py`
3. Log rotation (`logrotate` or Python `RotatingFileHandler`)
4. Structured JSON logging + correlation IDs

---

## 10. File Inventory (Key Files Only)

| Path | Lines | Purpose | Status |
|------|-------|---------|--------|
| `backend/main.py` | 67 | FastAPI app + lifespan + routers + WS | ✅ Current entrypoint |
| `backend/config.py` | 23 | `.env` config (CORS, port, token) | ✅ Used |
| `backend/routers/system.py` | 843 | 32 system endpoints | ⚠️ No auth, path traversal risk |
| `backend/routers/swarm.py` | 61 | Swarm REST | ✅ Clean |
| `backend/routers/audio.py` | 107 | Audio REST | ✅ Clean |
| `backend/services/swarm_manager.py` | 268 | Agent lifecycle + persistence | ✅ Solid |
| `backend/services/audio_engine.py` | 250 | DSP + intent parser | ⚠️ Stub STEM, keyword intent |
| `backend/websockets/terminal.py` | 65 | `pwsh.exe` WS | ⚠️ No auth, no resize handling |
| `backend/websockets/browser.py` | 128 | Playwright JPEG stream | 🔴 Leak, new browser/conn |
| `backend/websockets/swarm.py` | 65 | Telemetry broadcast + spawn | ✅ Good |
| `backend/websockets/audio.py` | 75 | PCM → VAD/STEM/intent | ✅ Good |
| `scripts/aiogram_bridge.py` | 87 | Telegram ↔ n8n bridge | ⚠️ Hardcoded token placeholder |
| `scripts/queue_manager.py` | 38 | JSON queue + git commit | ✅ Used by n8n |
| `static/index.html` | 4088 | Entire frontend | 🔴 Monolith, P0 bugs |
| `tests/test_system_api.py` | 158 | System REST tests | ✅ Good fixtures |
| `tests/test_swarm_api.py` | 189 | Swarm REST+WS + defensive | ✅ Good |
| `tests/test_websockets_e2e.py` | 158 | WS contract tests | ⚠️ TestClient only |
| `docs/*.md` | 11 files | Full spec suite | ✅ Excellent |
| `.env.example` | 11 | Config template | ✅ Exists |
| `deploy/hermes_startup.vbs` | — | Windows startup | ⚠️ Points to old `main.py` |

---

## 11. Verdict & Next Step

**This is a powerful local control panel masquerading as a Telegram Mini App.**  
The backend capabilities (shell, browser, process control, file system, swarm agents, audio pipeline) are **genuinely impressive** for a solo project. The documentation is thorough. The UI is polished.

**But it is NOT safe to expose via Cloudflare Tunnel today.**  
The auth gap (P0 #1) alone makes it a remote code execution endpoint for anyone who finds the URL.

**My recommendation:**  
> **Spend 2 hours on Phase 0 (auth + CORS + token rotation + WS origin check).**  
> Then validate: `curl -H "X-Telegram-Init-Data: <valid>" https://your-tunnel/api/stats` → 200, without header → 401.  
> Only then re-enable the tunnel and set the Telegram Menu Button.

Once locked down, the modular backend is ready for iterative hardening. The frontend needs a proper build pipeline — but that can wait until the tunnel is safe.

---

**Ready to execute Phase 0?** Say the word and I'll:
1. Create `backend/auth.py` with `initData` verification
2. Patch `backend/main.py` + all routers + WS handlers
3. Fix `backend/config.py` CORS
4. Update `scripts/aiogram_bridge.py` to use `config.TELEGRAM_BOT_TOKEN`
5. Verify with a test request

Megat, your call. 🎯