# Troubleshooting Guide (TROUBLESHOOTING.md)

Use this guide when the Hermes OS WebApp becomes unresponsive, crashes, or exhibits strange behavior.

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
