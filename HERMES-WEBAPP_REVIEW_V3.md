# HERMES-WEBAPP — SECURITY & CODE REVIEW (V3)

| | |
|---|---|
| **Target** | `C:\Users\megat\Hermes-WebApp` (FastAPI backend + Telegram Mini App SPA) |
| **Review date** | 2026-08-19 |
| **Review type** | Full source audit + live exposure verification + test suite run |
| **Prior baselines** | V1 `IMPROVEMENT_PLAN.md` — **5.6/10** · V2 `HERMES-WEBAPP_REVIEW_V2.md` — **6.5/10** |
| **This review (V3)** | **3.5/10** — **CRITICAL** |
| **Method** | Read every backend module; grepped every endpoint & router inclusion for auth; ran the test suite; probed the production Cloudflare tunnel |

---

## ⚠️ EXECUTIVE SUMMARY

**The single most important finding: the application is publicly reachable on the internet RIGHT NOW, and every single HTTP route and WebSocket endpoint is unauthenticated.**

Live verification performed during this review:

```
GET https://spider-thread-jennifer-pad.trycloudflare.com/health
→ HTTP 200
→ {"status":"healthy","service":"hermes-webapp","version":"1.0.0","uptime_seconds":6132}
```

That tunnel fronts a server exposing, **with no authentication of any kind**:

- 🔴 **`/ws/terminal`** — spawns `pwsh.exe` and streams an interactive PowerShell session. Anyone who can reach the tunnel gets a **full remote shell as `C:\Users\megat`**.
- 🔴 **`POST /api/files/read`** — read **any file on disk ≤2MB** (including `.env` with the live Telegram bot token, SSH keys, browser cookies, documents).
- 🔴 **`POST /api/files/write`** — **write to any path** (arbitrary file write → instant RCE: drop a `.py`/`.bat`/Startup-folder payload, or overwrite backend source).
- 🔴 **`POST /api/system/services/{name}/{action}`** — raw **PowerShell command injection** via unescaped single-quoted service name.
- 🔴 **`POST /api/kill/{pid}`** — terminate any process.
- 🔴 **`POST /api/macro/*`** — `os.system()` execution of destructive commands (`del /q/f/s %TEMP%\*`, `rundll32 LockWorkStation`, arbitrary `python <script>`).
- 🟠 **Chrome cookie-decryption + Facebook automation toolkit** shipped in `scripts/` — credential theft capability on the same box.
- 🟠 **Defender exclusions script** — disables real-time AV coverage on production paths.

**All 5 P0 items from V2 remain UNFIXED. Two new P0s were discovered (PowerShell injection in service control, arbitrary file write). The score has dropped from 6.5 → 3.5 because the public tunnel exposure turns every finding from "local risk" into "internet-exploitable".**

**The only mitigations in the repo's favor:** `.env` is gitignored, the app is NOT committed to the GitHub remote (only the home-dir monorepo root is), and the README token is a real token but the file is untracked — so the token has **not** leaked to GitHub *yet*. It must still be rotated (see P0-09), and the app must be pulled off the tunnel immediately.

---

## 📊 SCORES

| Category | V2 | V3 | Δ | Notes |
|---|---|---|---|---|
| **Security** | 5.0 | **2.0** | ↓3.0 | Zero auth + public tunnel + arbitrary file R/W + PS injection |
| **Code quality** | 6.5 | **5.0** | ↓1.5 | Solid structure, but guard exists and is never wired; string-built shell commands |
| **Testing** | 7.0 | **5.0** | ↓2.0 | 33 pass, but auth wiring & critical endpoints have zero coverage; timeout config inert |
| **Operability** | 6.5 | **4.0** | ↓2.5 | Stubbed/fake endpoints; live tunnel with no access control; junk temp file |
| **OVERALL** | **6.5** | **3.5** | **↓3.0** | **CRITICAL — do not expose until remediated** |

---

## ✅ V2 P0 FIX VERIFICATION

| # | V2 P0 Item | V3 Verdict | Evidence |
|---|---|---|---|
| P0-1 | Wire `telegram_auth_guard` as FastAPI dependency on all routes | **❌ FAIL** | `backend/auth.py:68` defines `telegram_auth_guard`, but grep across `backend/` finds **zero usages**. `backend/main.py:67-74` includes all 8 routers with no `dependencies=`; `auth.py` is not even imported in `main.py`. |
| P0-2 | CORS lockdown (no `*` with credentials) | **❌ FAIL** | `.env` explicitly sets `CORS_ORIGINS="*"`; `backend/config.py` hardcodes `ALLOW_CREDENTIALS=True`. Wildcard + credentials is invalid per spec and effectively disabled, but the intent (allow any origin) is the problem. |
| P0-3 | Browser WS leak / global state race / SSRF | **🟡 PARTIAL** | `backend/websockets/browser.py` now tears down page/context/browser/playwright in `finally`. **Still:** launches a new browser per connection, overwrites module-global `browser_context`/`browser_page` (race with 2+ clients), no auth, and `goto()` accepts arbitrary URLs → SSRF. |
| P0-4 | Auth on `/api/kill/{pid}` | **❌ FAIL** | `backend/routers/system.py:181-188` — plain `def kill_process(pid: int)`, no dependency, terminates any PID on the host. |
| P0-5 | Remove shell injection in macros | **❌ FAIL** | `backend/routers/system.py:194,197,202,208` still use `os.system()`. Worse, a **new** injection vector was added: `control_system_service` (lines 504-526) interpolates the user-supplied `service_name` into a PowerShell command string: `f"Start-Service -Name '{service_name}'"` → single-quote breakout = arbitrary PS command execution. |

**Verdict: 0/5 fixed, 1 partially fixed. V2's optimism was not warranted — none of the critical items landed.**

---

## 🔴 NEW CRITICAL FINDINGS (P0)

### P0-06 — Unauthenticated PowerShell shell over WebSocket (`/ws/terminal`)
`backend/websockets/terminal.py:7-16` — on connect, spawns `pwsh.exe -NoProfile -NoLogo` with `cwd=C:\Users\megat` and pipes stdin/stdout/stderr bidirectionally. No token check, no origin check. Combined with the live tunnel → **remote code execution for anyone on the internet** as the full user account.

### P0-07 — Arbitrary file read AND write (trivial RCE)
`backend/routers/system.py:426-448` (`POST /api/files/read`) — accepts any absolute/relative path, reads ≤2MB, returns content. Reads `.env`, `~/.ssh/*`, cookies, documents.
`backend/routers/system.py:450-473` (`POST /api/files/write`) — accepts any path + content, `os.makedirs()` the parent, writes file. **Worst primitive in the app**: write a `.py` into the running app's source dir (auto-reloaded by uvicorn) or a `.bat` into the Startup folder → persistent RCE without touching the terminal.

### P0-08 — Live public tunnel exposing everything
`.env` → `WEBAPP_URL="https://spider-thread-jennifer-pad.trycloudflare.com"`. Probed during review: **HTTP 200, app healthy, 6132s uptime**. trycloudflare URLs are public, unauthenticated, and ephemeral-but-long-lived. Every P0 above is therefore internet-reachable today.

### P0-09 — Live Telegram bot token in `.env` + real token in README
`.env` contains a live `TELEGRAM_BOT_TOKEN` (value withheld from this report). `README.md` also embeds the real token in the config example. **Not** in git (`.env` and `README.md` are both untracked — the GitHub repo `openclaw-office-monorepo` only tracks queue/n8n/docs files from the home-dir root). Risk is containment-grade for now, but the token is one `git add -A` or one `POST /api/files/read` away from exposure. **Rotate it** via @BotFather and use a placeholder in README.

### P0-10 — PowerShell injection in service control
`backend/routers/system.py:513-517`:
```python
cmd = ["powershell", "-Command", f"Start-Service -Name '{service_name}'"]
```
`service_name` is attacker-controlled and single-quote delimited. Payload `' ; whoami; '` breaks out and executes arbitrary PowerShell. Even without injection, the endpoint already allows start/stop/restart of ANY Windows service — a DoS/lateral-privilege primitive on its own.

### P0-11 — Credential-theft & AV-bypass toolkit shipped in `scripts/`
- `scripts/decrypt_cookies.py` + `scripts/extract_cookies.py` — Chrome cookie DB decryption (DPAPI/AES) → session hijacking capability.
- `scripts/automate_fb.py`, `fb-automation.js`, `fb_public.html` — Facebook account automation/credential flows.
- `scripts/defender_exclusions.ps1` — adds Defender exclusions for `C:\Users\megat` paths, disabling AV on the most valuable target directory.

None of these are called by the backend (they are standalone), but they materially raise the blast radius of the RCE findings: an attacker who reaches `/ws/terminal` or `/api/files/write` also has working cookie-theft and AV-suppression tooling already on disk.

---

## 🟠 OTHER FINDINGS

| ID | Severity | Finding | Location |
|---|---|---|---|
| P1-01 | High | `/api/logs` reads AI agent transcripts and streams them unauthenticated | `system.py:144` |
| P1-02 | High | `/api/files?path=...` directory listing, unauthenticated | `system.py:127` |
| P1-03 | High | `/api/system/env-info` dumps environment variables (leaks secrets/API keys) | `system.py:365` |
| P1-04 | High | `/api/system/network-scan` exposes all listening/established sockets + PIDs | `system.py:279` |
| P1-05 | Medium | SSRF via `/ws/browser` `goto` — browser can fetch internal network resources | `websockets/browser.py` |
| P1-06 | Medium | WebSocket endpoints (`/ws/swarm`, `/ws/audio`, `/ws/hitl`) — no auth, no origin validation | all `websockets/*.py` |
| P1-07 | Medium | `/api/system/send-alert` lets anyone send Telegram alerts to the bot's chat (spam/impersonation) | `system.py:528` |
| P1-08 | Medium | `/api/system/obsidian-context` & `/api/system/kanban` read local vault/kanban DBs unauthenticated | `system.py:216,231` |
| P1-09 | Medium | FIM baseline & firewall-rule endpoints fall back to **hardcoded fake data** on failure — false sense of security | `system.py:552,555,574` |
| P1-10 | Low | `/api/system/threat-scan` heuristics only (process-name matching), no real detection | `system.py:310` |
| P2-01 | Low | `.queue/pytest_temp` teardown PermissionError on Windows (WinError 5) — flaky test runs | `pytest.ini` basetemp |
| P2-02 | Low | `pytest.ini` sets `timeout=30` but **pytest-timeout is not installed** → "Unknown config option: timeout" warning; suite can hang (observed in V2 run) | `pytest.ini` |
| P2-03 | Low | Junk file in temp: `CUsersmegatAppDataLocalTemphermes-verify-fix.py` (stray artifact, no leading separators in name) | temp dir |

---

## 🧪 TEST SUITE (RUN THIS REVIEW)

Command: `python -m pytest tests/test_auth.py tests/test_system_api.py -q`

```
33 passed, 3 warnings, 2 errors in 26.80s
```
- **33 tests pass** — but they test the *guard function in isolation* (`test_auth.py` validates `verify_telegram_init_data` logic) and basic CRUD. **Zero tests assert that routes are protected** (i.e., no test sends a request to `/api/kill/1` without a token and expects 401). That is exactly why 33 green tests coexist with a fully open app.
- 2 errors = `PermissionError` removing `.queue/pytest_temp` (Windows file-lock artifact) — not app logic, but should be fixed (`--basetemp` to a non-`.queue` path).
- `pytest-timeout` absent → the `timeout=30` in `pytest.ini` is silently inert.

---

## 🔎 ATTACK SURFACE MAP (ALL UNAUTHENTICATED)

```
INTERNET ──► https://spider-thread-jennifer-pad.trycloudflare.com   [LIVE]
                  │  HTTP 200 confirmed
                  ▼
            FASTAPI :9220
   ├─ REST: /api/stats, /api/processes, /api/files?path=, /api/logs,
   │        /api/system/{env-info,network-scan,threat-scan,services,
   │        obsidian-context,kanban,send-alert,env-info}, /api/macro/*,
   │        /api/kill/{pid}, /api/files/{read,write},
   │        /api/system/services/{name}/{action}  ← PS INJECTION
   ├─ WS:  /ws/terminal  ← pwsh.exe SHELL
   │        /ws/browser  ← Playwright control + SSRF
   │        /ws/swarm, /ws/audio, /ws/hitl
   └─ Static SPA + /metrics (Prometheus)
```

**Practical exploit chain (verified components, no auth needed):**
1. `GET /api/files/read` with `{"path":"C:/Users/megat/.env"}` → steal the Telegram bot token.
2. `POST /api/system/services/'; calc; '/start` → arbitrary PowerShell command execution.
3. `POST /api/files/write` with a `.py` payload into `backend/routers/` → persistent code execution on reload.
4. Or simply open `/ws/terminal` and type — a full interactive shell.

---

## 🛠️ REMEDIATION ROADMAP (in priority order)

### Immediate (today — stop the bleeding)
1. **Kill the tunnel** — stop `cloudflared`; bind backend to `127.0.0.1` only (already `HOST=127.0.0.1`). Do not re-expose until auth lands.
2. **Rotate the Telegram bot token** (both the `.env` token and the one embedded in `README.md`; replace with placeholder in README).
3. **Remove / quarantine** `scripts/decrypt_cookies.py`, `extract_cookies.py`, `automate_fb.py`, `fb-automation.js`, `fb_public.html`, `defender_exclusions.ps1`. If the Defender exclusions are active, remove them and re-run a full scan.

### Next 48h — wire the auth that already exists
4. `backend/auth.py` `telegram_auth_guard` is well-built and unused. Wire it:
   - `app.include_router(..., dependencies=[Depends(telegram_auth_guard)])` in `main.py:67-74` for every router (or a single parent router).
   - For WebSockets, validate the token/init-data during the WebSocket handshake (`websocket.headers` / query param) before spawning `pwsh` or Playwright.
   - Add an origin allow-list check (reject non-TelegraM/known origins) as defense-in-depth.
5. Fix CORS: set `CORS_ORIGINS` to the real Telegram Mini App origins / your domain; drop `ALLOW_CREDENTIALS=True` with `*`.

### Next week — close the primitives
6. `control_system_service`: whitelist service names (regex `^[A-Za-z0-9_\-\.]+$`) and stop building shell strings; use `subprocess` list-form or the `net start/stop` list-form with argv arrays, never string interpolation into `-Command`.
7. `files/read` + `files/write`: resolve and constrain paths under a configured allow-root (e.g., project dir + a scratch dir); forbid `.env`, `.ssh`, `AppData` by default.
8. `/api/kill`, `/api/macro`: admin-only role check (beyond the base guard); replace `os.system` with list-form `subprocess.run`.
9. `/ws/browser`: serialize browser access (asyncio lock around global context), or spawn per-session isolated context; restrict `goto` to http(s) and optionally a domain allow-list.
10. Add auth tests: every route must return 401 without a valid `X-Telegram-Init-Data`; install `pytest-timeout`; move `--basetemp` out of `.queue`.
11. Replace the fake-data fallbacks (FIM baseline, firewall rules) with explicit `501 Not Implemented` or real persistence.

---

## ✅ WHAT'S ACTUALLY GOOD (worth preserving)

- **Clean module layout** — routers/websockets/services split is sensible; consistent typing and Pydantic models.
- **`backend/auth.py`** — HMAC-SHA256 + constant-time compare; the guard logic itself is correct and ready to wire.
- **`browser.py` resource cleanup** — finally-based teardown is the right pattern (just needs the race/auth fixes).
- **Observability intent** — structured JSON logging, Prometheus metrics, Telegram alerting hooks are all present and wired in `main.py` lifespan.
- **33 passing tests** — foundation exists; the gap is *negative-path* (auth) coverage, not the harness.

---

## FINAL VERDICT

**3.5/10 — CRITICAL. Do not expose this application to anything other than localhost until P0-06 through P0-11 are remediated.** The architecture is salvageable and the auth primitive already exists — the failure is one of *wiring and exposure*, not design. Fix the wiring, kill the tunnel, rotate the token, and remove the offensive scripts, and the score can recover quickly in a V4 review.