---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — Troubleshooting Runbook"
document_id: "HERMES-WEBAPP-TRB-001"
version: "3.6.0"
last_updated: "2026-09-12 16:35:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "ENGINEERING DOCS // TROUBLESHOOTING RUNBOOK"
lifecycle_status: "PRODUCTION / STABLE"
---

# 🩺 Troubleshooting Guide (TROUBLESHOOTING.md)

> **Runtime Diagnostic Runbook.** Step-by-step resolution guides for WebSocket freezes, Cloudflare tunnel drops, UI button jitter, mobile layout collisions, and zombie task clearance.

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Scope / Root Cause | Components Updated | Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`3.7.0`** | 2026-09-16 07:30:00<br>`2026-09-15T23:30:00Z` | Antigravity Specialist | Capability Health Probes, Restart Recovery, & Migration Diagnostics. | `docs/TROUBLESHOOTING.md`, `backend/services/capability_probe.py` | Pytest 100% pass, restart classification verified. |
| **`3.6.0`** | 2026-09-12 16:35:00<br>`2026-09-12T08:35:00Z` | Antigravity Conductor | Panduan penyelesaian getaran butang (jitter) & pertindihan susun atur mobile. | `docs/TROUBLESHOOTING.md` | Runbook lengkap disahkan. |
| **`3.0.0`** | 2026-07-27 18:00:00<br>`2026-07-27T10:00:00Z` | Hermes Dev Squad | Penyelesaian ralat WebSocket, ping leakage, dan zombie processes. | `scripts/cleanup_tasks.py` | Diagnostic runbook disahkan. |

---

## 1. Telegram Mini App Hangs on "Loading..."
- **Cause:** The Cloudflare Tunnel URL might have expired, or `localtunnel` was accidentally used (which injects an interstitial blocker).
- **Fix:** 
  1. Verify Cloudflare is running: `cloudflared tunnel --url http://127.0.0.1:9220`
  2. Copy the newly generated URL (e.g., `https://xyz.trycloudflare.com`).
  3. Update your Telegram Bot's Menu Button URL via `@BotFather`.

## 2. Terminal Input Freezes / ANSI Codes Show as Weird Characters
- **Cause:** The subprocess buffering might be locked, or the wrong shell is configured.
- **Fix:** Ensure `main.py` is spawning `pwsh.exe -NoProfile -NoLogo` (PowerShell Core), NOT legacy `powershell.exe` or `cmd.exe`. If the terminal freezes completely, kill the backend and restart Uvicorn.

## 3. Playwright "Vision" Tab Shows Blank Screen
- **Cause:** The headless Chromium instance either crashed or a target URL triggered an unhandled navigation exception (e.g., invalid scheme like `htp://`).
- **Fix:** 
  1. Ensure the user's input URL in the frontend automatically prefixes `http://` or `https://` if missing.
  2. Restart the browser session by refreshing the Telegram Web App.
  3. Run `playwright install` on the host PC to ensure browser binaries are up to date.

## 4. High CPU/RAM Usage on Host PC
- **Cause:** `main.py` might be leaking zombie subprocesses if a WebSocket disconnects unexpectedly without triggering the `finally` cleanup block.
- **Fix:** Open Task Manager on the host PC and kill hanging `pwsh.exe` or `chrome.exe` (headless) instances, or trigger the `clean_temp` macro to purge temporary browser profiles. Run `scripts/cleanup_tasks.py` if zombie processes persist.

## 5. Infinite Telegram Bot Messaging Loops
- **Cause:** Two bots (e.g., n8n and AI agent) are responding to each other.
- **Fix:** Ensure `scripts/aiogram_bridge.py` is running. It natively filters `message.from_user.is_bot` to drop recursive bot chatter.

## 6. n8n Media Generation Stuck
- **Cause:** The n8n Wait Node isn't receiving the callback from the webhook.
- **Fix:** Check `.queue/queue.json` lock states. If the queue is stuck, delete the lockfile or clear the JSON array and restart the `queue_manager.py` daemon.

## 7. Buttons Vibrate or Jitter When Hovered
- **Cause:** An interactive button has the `.glass` class applied or is matched by `MagicBento` pointer-tracking physics selectors (`.card`), causing conflicting magnetic transforms.
- **Fix:** Remove `.glass` from the button and ensure the JavaScript pointer tracker excludes interactive controls using `.card:not(button):not(.btn)`. Add `:active { transform: scale(0.97) }` with `100ms ease` transition.

## 8. Mobile Bottom Action Buttons Overlap with Dock
- **Cause:** The `main` container lacks sufficient safe-area bottom padding on mobile viewports.
- **Fix:** Verify `main` has `padding-bottom: calc(140px + env(safe-area-inset-bottom, 28px)) !important` and list panels have `padding-bottom: 36px`. Confirm `.action-launchers-grid` uses `grid-template-columns: repeat(3, 1fr)` on `< 640px`.

## 9. Mission Runs Stuck in STARTING or RUNNING Across Server Restart
- **Cause:** Uvicorn or host machine was restarted while an AGY subprocess was active. The stdin/stdout pipes are closed and cannot be re-attached.
- **Fix:** During startup, `MissionService.reconcile_startup()` automatically marks uncompleted runs as `INTERRUPTED` and logs a `run.interrupted` audit event. If manual reconciliation is needed, invoke `manager.reconcile_incomplete_runs()`. The operator may resume the mission using its persisted `provider_conversation_id`.

## 10. Capability Health Probes Report "Degraded" or "Unavailable"
- **AGY unavailable**: The AGY executable was not found in PATH or configured location. Action: Install AGY CLI or set `AGY_EXECUTABLE_PATH`.
- **AGY degraded**: The executable exists but returned non-zero or timed out during `--version` / `--help` empirical test. Action: Verify binary permissions and dependencies.
- **Hermes unavailable**: `HERMES_ADAPTER_ENABLED` is set to `false`. Action: Set `HERMES_HERMES_ADAPTER_ENABLED=true` in `.env` if Hermes coordinator tasks are desired.
- **Database unavailable**: SQLite file cannot be locked or WAL mode is disabled. Action: Verify permissions on `var/lib/missions.db` and ensure disk space is sufficient.
- **WebBridge unavailable**: Port 10087 is not listening. Action: Start GangNiaga WebBridge background service.
- **Tunnel degraded/unavailable**: `cloudflared` process is not running. Action: Run `cloudflared tunnel --url http://127.0.0.1:9220`.


